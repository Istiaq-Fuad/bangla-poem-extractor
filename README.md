# Bangla Poem Scraper (Nazrul Rachanabali)

Scrapes poems from https://nazrul-rachanabali.nltr.org while preserving original formatting

## Prerequisites

- uv (Python package/dependency manager): https://docs.astral.sh/uv/
- Python (uv can manage Python automatically; Python 3.10+ recommended)

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
      - Traditional `kabita*` paragraphs with smart indentation
      - `gapkabita` two-column alignment
    - Save utilities (`save_poems_to_file`)
    - Batch runners (`scrape_collection`, `scrape_all_collections`)
- `main.py` — Entry point. Instantiates the scraper and runs a scrape.
- `scraped_poems/` — Output folder for text files (created on first run).
- `pyproject.toml` — Project configuration and dependencies (managed by uv).

## Configuration

- Delay between requests: set via `BanglaPoetryWebScraper(delay=...)`.
- Base URL override (if needed): `BanglaPoetryWebScraper(base_url=...)`.
- Choose specific collections/pages:
  - Use `scrape_collection(titleid=..., max_pages=...)`
  - Or pass a list to `scrape_all_collections(titleids=[...])`

Edit `main.py` to switch between targeted tests and full runs.

## Responsible scraping

- Be respectful: keep delays, avoid overwhelming the site.
- This project is for educational/research purposes.
