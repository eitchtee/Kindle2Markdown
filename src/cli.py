import argparse
import os
from collections import defaultdict
from . import parser
from . import writer


def main():
    """
    The main function of the application.
    """
    arg_parser = argparse.ArgumentParser(
        description="Parse Kindle's My Clippings file and create markdown files for each book."
    )
    arg_parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Path to the 'My Clippings.txt' file.",
    )
    arg_parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Path to the output directory for the markdown files.",
    )
    arg_parser.add_argument(
        "--deduplicate",
        action="store_true",
        help="Remove duplicate highlights, keeping only the most recent one.",
    )
    arg_parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Overwrite existing files and covers.",
    )

    args = arg_parser.parse_args()

    print(f"Input file: {args.input}")
    print(f"Output directory: {args.output}")

    try:
        with open(args.input, "r", encoding="utf-8-sig") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Input file not found at {args.input}")
        return
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    clippings = parser.parse_clippings(content)

    if not clippings:
        print("No clippings found in the input file.")
        return

    if args.deduplicate:
        print("Deduplicating highlights...")
        unique_clippings = {}
        clippings_without_position = []

        for clipping in clippings:
            position = clipping.get("position")
            if not position:
                clippings_without_position.append(clipping)
                continue

            start_pos = position.split("-")[0]
            book_key = (clipping["book_title"], tuple(clipping["author"]))
            dedup_key = (book_key, start_pos)

            if dedup_key not in unique_clippings:
                unique_clippings[dedup_key] = clipping
            else:
                existing_date = unique_clippings[dedup_key].get("date")
                current_date = clipping.get("date")

                if current_date and (not existing_date or current_date > existing_date):
                    unique_clippings[dedup_key] = clipping

        original_count = len(clippings)
        clippings = list(unique_clippings.values()) + clippings_without_position
        new_count = len(clippings)
        print(f"Removed {original_count - new_count} duplicate highlights.")

    # Group clippings by book
    grouped_clippings = defaultdict(list)
    for clipping in clippings:
        book_key = (clipping["book_title"], tuple(clipping["author"]))
        grouped_clippings[book_key].append(clipping)

    # Write the markdown files
    writer.write_markdown_files(grouped_clippings, args.output, rebuild=args.rebuild)

    print(
        f"\nSuccessfully processed {len(clippings)} clippings into {len(grouped_clippings)} books."
    )
    print("Done!")


if __name__ == "__main__":
    main()
