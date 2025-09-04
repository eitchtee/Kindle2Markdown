import os
import re
import shutil
import requests
import urllib.parse
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from . import utils


def sanitize_filename(filename: str) -> str:
    """Removes invalid characters from a filename."""
    return re.sub(r"[\\/*?:\"<>|]", "", filename)


def _find_existing_cover(
    title: str, authors: List[str], output_dir: str
) -> Optional[str]:
    """Checks if a cover file already exists for the book, regardless of extension."""
    covers_dir = os.path.join(output_dir, "covers")
    if not os.path.isdir(covers_dir):
        return None

    authors_str = "; ".join(authors)
    base_filename = sanitize_filename(f"{title} - {authors_str}")

    for filename in os.listdir(covers_dir):
        if os.path.splitext(filename)[0] == base_filename:
            return f"./covers/{filename}"
    return None


def _get_cover_url_from_longitood(title: str, author: str) -> Optional[str]:
    """Tries to fetch a cover URL from the longitood.com API."""
    if not title or not author:
        return None

    longitood_api_url = "https://bookcover.longitood.com/bookcover"
    params = {"book_title": title, "author_name": author}
    try:
        response = requests.get(longitood_api_url, params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get("url")
        elif response.status_code not in [400, 404]:
            response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error querying longitood API for '{title}': {e}")
    except Exception as e:
        print(f"Error processing response from longitood API for '{title}': {e}")
    return None


def _get_cover_url_from_google_books(title: str, author: str) -> Optional[str]:
    """Tries to fetch a cover URL from the Google Books API."""
    query = f"intitle:{urllib.parse.quote_plus(title)}"
    if author:
        query += f"+inauthor:{urllib.parse.quote_plus(author)}"

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
                    return image_links.get("thumbnail")
    except requests.exceptions.RequestException as e:
        print(f"Could not fetch metadata from Google Books for '{title}': {e}")
    return None


def _download_cover(
    cover_url: str, title: str, authors: List[str], output_dir: str
) -> Optional[str]:
    """Downloads a cover from a URL."""
    try:
        _, ext = os.path.splitext(urllib.parse.urlparse(cover_url).path)
        if not ext or len(ext) > 5:
            ext = ".jpg"

        authors_str = "; ".join(authors)
        cover_filename = sanitize_filename(f"{title} - {authors_str}{ext}")
        covers_dir = os.path.join(output_dir, "covers")
        cover_filepath = os.path.join(covers_dir, cover_filename)

        img_response = requests.get(cover_url, stream=True)
        img_response.raise_for_status()

        with open(cover_filepath, "wb") as f:
            for chunk in img_response.iter_content(1024):
                f.write(chunk)

        return f"./covers/{cover_filename}"
    except requests.exceptions.RequestException as e:
        print(f"Could not download cover for '{title}': {e}")
    return None


def _download_placeholder_cover(title: str, authors: List[str], output_dir: str) -> str:
    """Downloads and saves a placeholder cover."""
    authors_str = "; ".join(authors)
    cover_filename = sanitize_filename(f"{title} - {authors_str}.png")
    covers_dir = os.path.join(output_dir, "covers")
    cover_filepath = os.path.join(covers_dir, cover_filename)

    if not os.path.exists(cover_filepath):
        placeholder_text = f"{title}\n{authors_str}"
        placeholder_url = f"https://placehold.co/450x600.png?text={urllib.parse.quote(placeholder_text)}"
        try:
            img_response = requests.get(placeholder_url, stream=True)
            img_response.raise_for_status()
            with open(cover_filepath, "wb") as f:
                for chunk in img_response.iter_content(1024):
                    f.write(chunk)
        except requests.exceptions.RequestException as e:
            print(f"Could not download placeholder image: {e}")

    return f"./covers/{cover_filename}"


def get_metadata(
    original_title: str,
    original_authors: List[str],
    output_dir: str,
    rebuild: bool = False,
) -> Tuple[str, List[str], str]:
    """
    Fetches book metadata, prioritizing existing covers, then external APIs.
    Returns (title, authors, cover_path).
    """
    os.makedirs(os.path.join(output_dir, "covers"), exist_ok=True)

    if not rebuild:
        existing_cover = _find_existing_cover(
            original_title, original_authors, output_dir
        )
        if existing_cover:
            return original_title, original_authors, existing_cover

    first_author = original_authors[0] if original_authors else ""
    cover_url = _get_cover_url_from_longitood(original_title, first_author)
    if cover_url:
        cover_path = _download_cover(
            cover_url, original_title, original_authors, output_dir
        )
        if cover_path:
            return original_title, original_authors, cover_path

    cover_url = _get_cover_url_from_google_books(original_title, first_author)
    if cover_url:
        cover_path = _download_cover(
            cover_url, original_title, original_authors, output_dir
        )
        if cover_path:
            return original_title, original_authors, cover_path

    # Fallback to placeholder
    cover_path = _download_placeholder_cover(
        original_title, original_authors, output_dir
    )
    return original_title, original_authors, cover_path


def generate_book_markdown(
    book_id: str,
    title: str,
    authors: List[str],
    clippings: List[Dict],
    cover_path: str,
    date_format: str,
) -> str:
    """Generates the markdown content for a single book."""
    clippings.sort(key=lambda c: c.get("date") or datetime.min)

    last_clipping_date_str = ""
    if clippings and clippings[-1].get("date"):
        last_clipping_date = clippings[-1]["date"]
        last_clipping_date_str = last_clipping_date.strftime("%Y-%m-%d")

    if authors:
        authors_list_formatted = "\n".join([f'  - "{author}"' for author in authors])
        author_field = f"Author:\n{authors_list_formatted}"
    else:
        author_field = 'Author: ""'

    header = f"""---
ID: "{book_id}"
Cover: "{cover_path}"
Book: "{title}"
{author_field}
Clippings: {len(clippings)}
Last clipping: {last_clipping_date_str}
---"""

    body_parts = []
    for clipping in clippings:
        quote_title_parts = []
        if clipping.get("page"):
            quote_title_parts.append(f"📄 {clipping['page']}")
            if clipping.get("position"):
                quote_title_parts.append(f"({clipping['position']})")
        else:
            if clipping.get("position"):
                quote_title_parts.append(f"📑 {clipping['position']}")
        if clipping.get("date"):
            quote_title_parts.append(f"@ {clipping['date'].strftime(date_format)}")

        quote_title = " ".join(quote_title_parts)
        highlight_lines = clipping["highlight"].split("\n")
        formatted_highlight = "\n".join([f"> {line}" for line in highlight_lines])
        body_parts.append(f"> [!quote]+ {quote_title}\n{formatted_highlight}")

    body = "\n\n".join(body_parts)
    return f"{header}\n{body}"


def write_markdown_files(
    grouped_clippings: Dict,
    output_dir: str,
    rebuild: bool = False,
    date_format: str = "%d/%m/%Y %H:%M",
):
    """Writes the markdown files for all books."""

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    covers_dir = os.path.join(output_dir, "covers")
    if not os.path.exists(covers_dir):
        os.makedirs(covers_dir)

    id_to_filepath = {}
    if not rebuild:
        for filename in os.listdir(output_dir):
            if not filename.endswith(".md"):
                continue

            filepath = os.path.join(output_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    # Read only the beginning of the file for performance
                    content = f.read(1024)
                match = re.search(r"^ID: \s*\"?([^\r\n\"]+)\"?", content, re.MULTILINE)
                if match:
                    book_id = match.group(1)
                    if book_id not in id_to_filepath:
                        id_to_filepath[book_id] = filepath
            except (IOError, ValueError) as e:
                print(e)
                continue

    for (title, author_tuple), clippings in grouped_clippings.items():
        authors = list(author_tuple)
        book_id = utils.generate_book_id(title, authors)
        filepath = id_to_filepath.get(book_id)

        if filepath and os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    existing_content = f.read()

                match = re.search(r"Clippings: (\d+)", existing_content)
                if match:
                    existing_clippings_count = int(match.group(1))
                    if existing_clippings_count == len(clippings):
                        print(f"Skipping up-to-date file: {os.path.basename(filepath)}")
                        continue
            except (IOError, ValueError) as e:
                print(
                    f"Could not check existing file {os.path.basename(filepath)}, will overwrite. Error: {e}"
                )
        else:
            authors_str = "; ".join(authors)
            filename = sanitize_filename(f"{title} - {authors_str}.md")
            filepath = os.path.join(output_dir, filename)

        _, authors, cover_path = get_metadata(
            title, authors, output_dir, rebuild=rebuild
        )
        markdown_content = generate_book_markdown(
            book_id, title, authors, clippings, cover_path, date_format
        )

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            print(f"Successfully created/updated: {os.path.basename(filepath)}")
        except Exception as e:
            print(f"Error writing file {os.path.basename(filepath)}: {e}")
