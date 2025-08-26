import os
import re
from datetime import datetime
from typing import List, Dict


def sanitize_filename(filename: str) -> str:
    """Removes invalid characters from a filename."""
    return re.sub(r"[\\/*?:\"<>|]", "", filename)


def generate_book_markdown(title: str, author: str, clippings: List[Dict]) -> str:
    """Generates the markdown content for a single book."""
    # Sort clippings by date to maintain a chronological order in the file
    clippings.sort(key=lambda c: c.get("date") or datetime.min)

    last_clipping_date_str = ""
    if clippings and clippings[-1].get("date"):
        last_clipping_date = clippings[-1]["date"]
        last_clipping_date_str = last_clipping_date.strftime("%Y-%m-%d")

    header = f"""---
Cover: empty for now
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

        # Format the highlight content, ensuring each line is a blockquote
        highlight_lines = clipping["highlight"].split("\n")
        formatted_highlight = "\n".join([f"> {line}" for line in highlight_lines])

        body_parts.append(f"> [!quote]+ {quote_title}\n{formatted_highlight}")

    body = "\n\n".join(body_parts)
    return f"{header}\n{body}"


def write_markdown_files(grouped_clippings: Dict, output_dir: str):
    """Writes the markdown files for all books."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for (title, author), clippings in grouped_clippings.items():
        markdown_content = generate_book_markdown(title, author, clippings)

        # Create a safe filename
        filename = sanitize_filename(f"{title} - {author}.md")
        filepath = os.path.join(output_dir, filename)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            print(f"Successfully created: {filename}")
        except Exception as e:
            print(f"Error writing file {filename}: {e}")
