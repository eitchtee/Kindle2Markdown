import hashlib


def generate_book_id(title: str, authors: list[str]) -> str:
    """Generates a unique ID for a book based on its title and authors."""
    authors_str = ";".join(sorted(authors))
    book_identifier = f"{title.strip()}-{authors_str.strip()}"
    return hashlib.sha1(book_identifier.encode("utf-8")).hexdigest()