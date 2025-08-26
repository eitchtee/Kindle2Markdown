import os
import re
import shutil

import requests
import urllib.parse
from datetime import datetime
from typing import List, Dict, Tuple


def sanitize_filename(filename: str) -> str:
    """Removes invalid characters from a filename."""
    return re.sub(r"[\\/*?:\"<>|]", "", filename)


def get_metadata(
    original_title: str, original_author: str, output_dir: str
) -> Tuple[str, str, str]:
    """
    Fetches book metadata from various sources.
    Tries longitood.com API first, then Google Books API, then a placeholder.
    Returns (title, author, cover_path).
    """
    cover_url = None

    # 1. Try longitood.com API if we have title and author
    if original_title and original_author:
        longitood_api_url = "https://bookcover.longitood.com/bookcover"
        params = {
            "book_title": original_title,
            "author_name": original_author,
        }
        try:
            response = requests.get(longitood_api_url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get("url"):
                    cover_url = data["url"]
            # Per instructions, 400 and 404 are not errors, but fallbacks
            elif response.status_code not in [400, 404]:
                response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error querying longitood API for '{original_title}': {e}")
        except Exception as e:
            print(f"Error processing response from longitood API for '{original_title}': {e}")

    # 2. Fallback to Google Books API if no cover found yet
    if not cover_url:
        query = f"intitle:{urllib.parse.quote_plus(original_title)}"
        if original_author:
            query += f"+inauthor:{urllib.parse.quote_plus(original_author)}"

        google_api_url = f"https://www.googleapis.com/books/v1/volumes?q={query}"

        try:
            response = requests.get(google_api_url)
            response.raise_for_status()
            data = response.json()

            if data.get("totalItems", 0) > 0:
                for item in data["items"]:
                    volume_info = item.get("volumeInfo", {})
                    image_links = volume_info.get("imageLinks", {})
                    if image_links.get("thumbnail"):
                        cover_url = image_links.get("thumbnail")
                        break  # Found a cover, stop looking
        except requests.exceptions.RequestException as e:
            print(f"Could not fetch metadata from Google Books for '{original_title}': {e}")

    # 3. Download the cover or use a placeholder
    covers_dir = os.path.join(output_dir, "covers")
    os.makedirs(covers_dir, exist_ok=True)

    # If we have a cover_url, try to download it.
    if cover_url:
        try:
            # Determine file extension from URL
            _, ext = os.path.splitext(urllib.parse.urlparse(cover_url).path)
            if not ext or len(ext) > 5:  # Basic check for valid extension
                ext = ".jpg"

            cover_filename = sanitize_filename(f"{original_title} - {original_author}{ext}")
            cover_filepath = os.path.join(covers_dir, cover_filename)

            img_response = requests.get(cover_url, stream=True)
            img_response.raise_for_status()

            with open(cover_filepath, "wb") as f:
                img_response.raw.decode_content = True
                shutil.copyfileobj(img_response.raw, f)

            cover_path = f"./covers/{cover_filename}"
            return original_title, original_author, cover_path

        except requests.exceptions.RequestException as e:
            print(f"Could not download cover for '{original_title}': {e}")
            # Fall through to placeholder if download fails

    # Fallback to placeholder if no cover_url or if download failed
    placeholder_url = "https://placehold.co/150x200.png?text=No%20Cover"
    cover_filename = sanitize_filename(f"{original_title} - {original_author}.png")
    cover_filepath = os.path.join(covers_dir, cover_filename)

    try:
        if not os.path.exists(cover_filepath):
            img_response = requests.get(placeholder_url, stream=True)
            img_response.raise_for_status()
            with open(cover_filepath, "wb") as f:
                img_response.raw.decode_content = True
                shutil.copyfileobj(img_response.raw, f)
    except requests.exceptions.RequestException as e:
        print(f"Could not download placeholder image: {e}")

    cover_path = f"./covers/{cover_filename}"
    return original_title, original_author, cover_path


def generate_book_markdown(
    title: str, author: str, clippings: List[Dict], cover_path: str
) -> str:
    """Generates the markdown content for a single book."""
    clippings.sort(key=lambda c: c.get("date") or datetime.min)

    last_clipping_date_str = ""
    if clippings and clippings[-1].get("date"):
        last_clipping_date = clippings[-1]["date"]
        last_clipping_date_str = last_clipping_date.strftime("%Y-%m-%d")

    header = f"""---
Cover: "{cover_path}"
Book: "{title}" 
Author: "{author}" 
Clippings: {len(clippings)}
Last clipping: {last_clipping_date_str}
---
"""

    body_parts = []
    for clipping in clippings:
        quote_title_parts = []
        if clipping.get("page"):
            quote_title_parts.append(f"Page {clipping['page']}")
        if clipping.get("position"):
            quote_title_parts.append(f"({clipping['position']})")
        if clipping.get("date"):
            quote_title_parts.append(f"@ {clipping['date'].strftime('%Y-%m-%d %H:%M')}")

        quote_title = " ".join(quote_title_parts)
        highlight_lines = clipping["highlight"].split("\n")
        formatted_highlight = "\n".join([f"> {line}" for line in highlight_lines])
        body_parts.append(f"> [!quote]+ {quote_title}\n{formatted_highlight}")

    body = "\n\n".join(body_parts)
    return f"{header}\n{body}"


def write_markdown_files(grouped_clippings: Dict, output_dir: str):
    """Writes the markdown files for all books."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    covers_dir = os.path.join(output_dir, "covers")
    if not os.path.exists(covers_dir):
        os.makedirs(covers_dir)

    for (title, author), clippings in grouped_clippings.items():
        new_title, new_author, cover_path = get_metadata(title, author, output_dir)
        markdown_content = generate_book_markdown(title, author, clippings, cover_path)
        filename = sanitize_filename(f"{title} - {author}.md")
        filepath = os.path.join(output_dir, filename)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            print(f"Successfully created: {filename}")
        except Exception as e:
            print(f"Error writing file {filename}: {e}")
