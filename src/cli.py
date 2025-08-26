import argparse
import os

from . import parser as kindle_parser

def main():
    """
    The main function of the application.
    """
    parser = argparse.ArgumentParser(
        description="Parse Kindle's My Clippings file and create markdown files for each book."
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Path to the 'My Clippings.txt' file.",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Path to the output directory for the markdown files.",
    )

    args = parser.parse_args()

    print(f"Input file: {args.input}")
    print(f"Output directory: {args.output}")

    # Create the output directory if it doesn't exist
    if not os.path.exists(args.output):
        os.makedirs(args.output)

    try:
        with open(args.input, 'r', encoding='utf-8-sig') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Input file not found at {args.input}")
        return
    except Exception as e:
        print(f"Error reading file: {e}")
        return


    clippings = kindle_parser.parse_clippings(content)

    # For now, just print the parsed clippings to show it works.
    # The logic to write to markdown files will be added later.
    for clipping in clippings:
        print("-" * 20)
        print(f"Book: {clipping['book_title']}")
        print(f"Author: {clipping['author']}")
        print(f"Page: {clipping['page']}")
        print(f"Position: {clipping['position']}")
        print(f"Date: {clipping['date']}")
        print(f"Highlight: {clipping['highlight']}")

    print(f"\nSuccessfully parsed {len(clippings)} clippings.")
    print("Done!")

if __name__ == "__main__":
    main()
