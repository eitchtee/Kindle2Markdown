# Kindle2MD

A simple CLI tool to convert your Kindle "My Clippings.txt" file into a set of organized markdown files, one for each book.

**This tool is designed to work with clippings in Portuguese**, but it can be adapted for other languages (issues and pull requests for other languages are welcome. Share your My Clippings file). It automatically fetches book covers, deduplicates highlights, and generates clean markdown files ready for use in note-taking apps like [Obsidian](https://obsidian.md/).

## Features

- **Markdown Conversion**: Parses `My Clippings.txt` and generates individual markdown files for each book.
- **Cover Fetching**: Automatically fetches book covers from [bookcover API](https://github.com/w3slley/bookcover-api/i) and Google Books API.
- **Placeholder Covers**: Generates placeholder covers from [placehold.co](https://placehold.co) if no official cover is found.
- **Efficient Processing**: Caches covers locally and skips files that are already up-to-date to speed up later runs.
- **Deduplication**: Optionally removes duplicate highlights, keeping only the most recent one for each position.
- **Smart Parsing**:
    - Handles various author formats (e.g., `Last, First`, multiple authors separated by `;`, `&`, or `and`).
    - Correctly parses clippings metadata, including page, position, and date.
    - Currently optimized for clippings in Portuguese.
- **Customizable Output**:
    - Allows custom date formatting in the output files.
    - Generates clean, readable markdown with YAML frontmatter, perfect for Obsidian vaults.

## Usage

### Basic Command

```bash
python -m src -i "path/to/My Clippings.txt" -o "path/to/output/directory"
```

### Arguments

| Argument | Alias | Description | Default |
|---|---|---|---|
| `--input` | `-i` | **Required**. Path to your `My Clippings.txt` file. | |
| `--output` | `-o` | **Required**. Path to the directory where markdown files will be saved. | |
| `--deduplicate` | | A flag to remove duplicate highlights, keeping only the most recent one for each unique position. | `False` |
| `--rebuild` | | A flag to force the tool to overwrite existing markdown files and redownload all book covers. | `False` |
| `--date-format`| | A Python `strftime` string to format the date of each clipping in the markdown output. | `%d/%m/%Y %H:%M` |

### Example with all arguments

```bash
python -m src -i "C:\Kindle\My Clippings.txt" -o "D:\Notes\Books" --deduplicate --rebuild --date-format "%Y-%m-%d %H:%M"
```

## Output Example

The tool generates a markdown file for each book with a YAML frontmatter and your highlights formatted as blockquotes.

**`Book Title - Author.md`**
```markdown
---
Cover: "./covers/Project Hail Mary - Andy Weir.jpg"
Book: "Project Hail Mary"
Author:
  - "Andy Weir"
Clippings: 15
Last clipping: 2023-10-27
---
> [!quote]+ 📄 123 (1900-1902) @ 27/10/2023 15:30
> Eridians are so much better at problem-solving than humans. They’re also better at being not-stupid.

> [!quote]+ 📑 2500-2501 @ 27/10/2023 16:00
> Human beings have a remarkable ability to accept the bizarre as long as it’s explained with a straight face.
```

A `covers` folder will also be created inside your output directory to store the downloaded cover images.

## Development

To install the dependencies, run:
```bash
pip install -r requirements.txt
```
