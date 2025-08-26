import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple


def parse_clippings(file_content: str) -> List[Dict]:
    """
    Parses the content of a "My Clippings.txt" file.
    """
    clippings = []
    # Each clipping is separated by '=========='
    clipping_blocks = file_content.strip().split("==========")

    for block in clipping_blocks:
        block = block.strip()
        if not block:
            continue

        lines = block.split("\n")
        if len(lines) < 3:
            continue

        clipping = _parse_clipping_block(lines)

        if clipping:
            clippings.append(clipping)

    return clippings


def _parse_clipping_block(lines: List[str]) -> Optional[Dict]:
    """
    Parses a single clipping block.
    """
    try:
        title, author = _parse_title_and_author(lines[0])
        page, position, date = _parse_metadata(lines[1])
        highlight = _parse_highlight(
            lines[3:]
        )  # The highlight starts from the 4th line (index 3)

        return {
            "book_title": title,
            "author": author,
            "page": page,
            "position": position,
            "date": date,
            "highlight": highlight,
        }
    except (ValueError, IndexError):
        # Handle cases where a block is malformed
        return None


def _parse_title_and_author(line: str) -> Tuple[str, List[str]]:
    """
    Parses the book title and author(s) from the first line of a clipping.
    Authors can be separated by ';', '&', or 'and'.
    Returns the title and a list of authors.
    """
    line = line.strip()
    match = re.search(r"\(([^)]+)\)", line)

    if not match:
        # No author in parentheses, return the whole line as title
        return line, []

    authors_raw = match.group(1).strip()
    title = line[: match.start()].strip()

    # Handle the second case: "Book Title - Author (Author)"
    if title.endswith(f" - {authors_raw}"):
        title = title[: -(len(authors_raw) + 3)].strip()

    # Split authors by delimiters
    authors_list = re.split(r"\s*;\s*|\s*&\s*|\s+and\s+", authors_raw)

    authors = []
    for author_name in authors_list:
        author_name = author_name.strip()
        if not author_name:
            continue
        # Handle "Last, First" format
        if "," in author_name:
            parts = [p.strip() for p in author_name.split(",")]
            if len(parts) == 2:
                author_name = f"{parts[1]} {parts[0]}"
        authors.append(author_name)

    return title, authors


def _parse_metadata(
    line: str,
) -> Tuple[Optional[str], Optional[str], Optional[datetime]]:
    """
    Parses the metadata line of a clipping.
    e.g., "- Seu destaque ou posição 3631-3632 | Adicionado: quinta-feira, 12 de janeiro de 2017 17:34:14"
    """
    page = _extract_page(line)
    position = _extract_position(line)
    date = _extract_date(line)
    return page, position, date


def _extract_page(metadata_line: str) -> Optional[str]:
    """
    Extracts the page number from the metadata line.
    This is a placeholder for now, as the example shows 'posição' (position) but not 'página' (page).
    The logic can be expanded if clippings with page numbers are provided.
    For now, it will return None.
    """
    # Example for page: "- Sua nota na página 234"
    match = re.search(r"página (\d+)", metadata_line, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def _extract_position(metadata_line: str) -> Optional[str]:
    """
    Extracts the position from the metadata line.
    e.g., "posição 3631-3632"
    """
    match = re.search(r"posição ([\d-]+)", metadata_line, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def _extract_date(metadata_line: str) -> Optional[datetime]:
    """
    Extracts the date from the metadata line.
    e.g., "Adicionado: quinta-feira, 12 de janeiro de 2017 17:34:14"
    """
    date_str_match = re.search(r"Adicionado: .*?, (.*)", metadata_line)
    if not date_str_match:
        return None

    date_str = date_str_match.group(1)

    # The month names are in Portuguese. I need to map them to numbers.
    month_map = {
        "janeiro": 1,
        "fevereiro": 2,
        "março": 3,
        "abril": 4,
        "maio": 5,
        "junho": 6,
        "julho": 7,
        "agosto": 8,
        "setembro": 9,
        "outubro": 10,
        "novembro": 11,
        "dezembro": 12,
    }

    for month_name, month_num in month_map.items():
        if month_name in date_str:
            date_str = date_str.replace(f" de {month_name} de ", f"-{month_num}-")
            break

    # Now the date string is something like "12-1-2017 17:34:14"
    try:
        return datetime.strptime(date_str, "%d-%m-%Y %H:%M:%S")
    except ValueError:
        return None


def _parse_highlight(lines: List[str]) -> str:
    """
    Parses the highlight text from the clipping block.
    """
    return "\n".join(lines).strip()
