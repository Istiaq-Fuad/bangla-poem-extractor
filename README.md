# Bangla Poem Scraper (Nazrul Rachanabali)

Scrapes poems from https://nazrul-rachanabali.nltr.org while preserving original formatting

## Prerequisites

- uv (Python package/dependency manager): https://docs.astral.sh/uv/
- Python (uv can manage Python automatically; Python 3.11+ recommended)

Install uv:

- macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Windows (PowerShell): `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`

Verify: `uv --version`

## Setup

From the project root:

```bash
# Initialize the project and install dependencies from pyproject.toml
uv sync
```

This sets up the project with a virtual environment managed automatically by uv.

## Run

```bash
# Run the scraper (uv handles venv creation/activation automatically)
uv run main.py
```

Output files will be written under `scraped_poems/` (auto-created).

## Codebase overview

- `scraper.py` — Core scraper:
  - `BanglaPoetryWebScraper` with:
    - Networking (requests session, polite delay)
    - Pagination/collection discovery
    - Content extraction:
      - Traditional `kabita*` paragraphs with smart indentation based on class suffixes
      - `gapkabita` two-column alignment with proper spacing
      - Unicode normalization and punctuation spacing
    - Content processing with structured markers:
      - `process_poem_content()` adds `<start_poem>`, `<end_poem>`, `<line>`, `<stanza>` markers
      - Removes bracketed metadata `[...]`
      - Handles stanza separation
    - Integrated save utilities:
      - `scrape_collection()` with built-in save/append options
      - `scrape_all_collections()` with flexible saving modes
      - `save_poems_to_file()` for batch saving (saves both .txt and .json formats)
      - `append_poem_to_file()` for real-time appending (both .txt and .json)
- `main.py` — Entry point. Demonstrates different scraping and saving patterns.
- `demo.txt` — Sample poem output showing the structured format with markers.
- `scraped_poems/` — Output folder for text files (created on first run).
- `pyproject.toml` — Project configuration and dependencies (managed by uv).

## Configuration

- Delay between requests: set via `BanglaPoetryWebScraper(delay=...)`.
- Base URL override (if needed): `BanglaPoetryWebScraper(base_url=...)`.
- **Flexible saving options:**
  - `scrape_collection(save_individual=True, append_to_file="filename.txt")`
  - `scrape_all_collections(save_individual=True, save_combined=True, append_to_file="master.txt")`
  - Choose specific collections: `titleids=[4, 5, 6]`
  - Limit pages for testing: `max_pages=3` or `max_pages_per_collection=5`
- **Output formats:**
  - Both `.txt` and `.json` files are automatically generated
  - `.txt` files contain structured poems with `<start_poem>`, `<line>`, `<stanza>`, `<end_poem>` markers
  - `.json` files contain structured data with metadata (titleid, pageno, url, content)

Edit `main.py` to switch between different scraping and saving patterns.

## Responsible scraping

- Be respectful: keep delays, avoid overwhelming the site.
- This project is for educational/research purposes.
