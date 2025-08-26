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

    args = arg_parser.parse_args()

    print(f"Input file: {args.input}")
    print(f"Output directory: {args.output}")

    try:
        with open(args.input, 'r', encoding='utf-8-sig') as f:
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

    # Group clippings by book
    grouped_clippings = defaultdict(list)
    for clipping in clippings:
        book_key = (clipping['book_title'], clipping['author'])
        grouped_clippings[book_key].append(clipping)

    # Write the markdown files
    writer.write_markdown_files(grouped_clippings, args.output)

    print(f"\nSuccessfully processed {len(clippings)} clippings into {len(grouped_clippings)} books.")
    print("Done!")

if __name__ == "__main__":
    main()
