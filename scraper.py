import requests
from parsel import Selector
import time
import os
import re
import math
from typing import List, Dict, Optional


class BanglaPoetryWebScraper:
    def __init__(
        self,
        base_url: str = "https://nazrul-rachanabali.nltr.org/page1.php",
        delay: float = 1.0,
    ):
        """
        Initialize the scraper

        Args:
            base_url: Base URL for the poetry website
            delay: Delay between requests to be respectful to the server
        """
        self.base_url = base_url
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def get_page(self, url: str) -> Optional[Selector]:
        """
        Fetch a page and return a Selector object

        Args:
            url: URL to fetch

        Returns:
            Selector object or None if failed
        """
        try:
            print(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            time.sleep(self.delay)
            return Selector(text=response.text)
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def get_collection_info(self, titleid: int) -> Dict:
        """
        Get information about a collection (title, total pages)

        Args:
            titleid: Title ID for the collection

        Returns:
            Dictionary with collection info
        """
        url = f"{self.base_url}?pageno=1&titleid={titleid}"
        selector = self.get_page(url)

        if not selector:
            return {}

        last_page_link = selector.css(
            'form[name="pageno"] a[href*="pageno="]:last-child::attr(href)'
        ).get()
        total_pages = None
        if last_page_link:
            pageno_match = re.search(r"pageno=(\d+)", last_page_link)
            if pageno_match:
                total_pages = int(pageno_match.group(1))

        return {
            "titleid": titleid,
            "total_pages": total_pages,
        }

    def extract_poem_content(self, selector: Selector) -> str:
        """
        Extract Bengali poem content preserving indentation and spacing.
        Automatically detects the poem structure type and uses appropriate extraction method.

        Two types supported:
        1. Traditional kabita classes (kabita, kabita1, kabita11, etc.)
        2. Gap kabita structure (gapkabita with left/right divisions)
        """
        if selector.css("div.gapkabita"):
            return self.extract_gapkabita_poem(selector)
        elif selector.css('p[class*="kabita"]'):
            return self.extract_traditional_kabita(selector)
        else:
            return "No recognized poem structure found"

    def extract_traditional_kabita(self, selector: Selector) -> str:
        """Extract poems with traditional kabita classes (kabita, kabita1, kabita11, etc.)"""
        poem_lines = []
        all_p = selector.css("#data p")

        for p in all_p:
            class_name = p.css("::attr(class)").get() or ""

            if re.match(r"^kabita\d*$", class_name):
                text_parts = p.css("::text").getall()
                line_text = "".join(text_parts).strip()

                if line_text:
                    indent = self.get_kabita_indentation(class_name)
                    poem_lines.append(indent + line_text)
            elif class_name == "space":
                poem_lines.append("")

        return "\n".join(poem_lines)

    def extract_gapkabita_poem(self, selector: Selector) -> str:
        """Extract poems with gapkabita structure (left/right divisions) preserving alignment."""
        poem_lines = []
        gapkabita_divs = selector.css("div.gapkabita")

        left_col_width = 20

        for div in gapkabita_divs:
            left_text = div.css(".gapkabita_left::text").get() or ""
            right_text = div.css(".gapkabita_right::text").get() or ""

            left_text = left_text.strip().replace("\xa0", "")
            right_text = right_text.strip().replace("\xa0", "")

            if left_text or right_text:
                line = f"{left_text.rjust(left_col_width)} {right_text}"
                poem_lines.append(line.rstrip())

        return "\n".join(poem_lines)

    import re

    def get_kabita_indentation(self, class_name: str) -> str:
        """
        Indentation rule:
        - Base on the maximum digit in the suffix (higher digit → more indentation).
        - If only 1's, indentation grows with the count of 1's.
        - 'kabita' -> no spaces
        """
        match = re.match(r"kabita(\d*)$", class_name)
        if not match:
            return ""

        digits = match.group(1)
        if not digits:
            return ""

        if set(digits) == {"1"}:
            return " " * (4 * len(digits))

        max_digit = max(int(d) for d in digits)
        return " " * (4 * max_digit + 2)

    def scrape_poem_page(self, titleid: int, pageno: int) -> Dict:
        """
        Scrape a single poem page

        Args:
            titleid: Title ID for the collection
            pageno: Page number

        Returns:
            Dictionary with poem data
        """
        url = f"{self.base_url}?pageno={pageno}&titleid={titleid}"
        selector = self.get_page(url)

        if not selector:
            return {}

        poem_content = self.extract_poem_content(selector)

        return {
            "titleid": titleid,
            "pageno": pageno,
            "url": url,
            "content": poem_content,
        }

    def scrape_collection(
        self, titleid: int, start_page: int = 2, max_pages: Optional[int] = None
    ) -> List[Dict]:
        """
        Scrape all poems from a collection

        Args:
            titleid: Title ID for the collection
            start_page: Starting page (usually 2, as page 1 is TOC)
            max_pages: Maximum number of pages to scrape

        Returns:
            List of poem dictionaries
        """
        print(f"\n=== Scraping Collection {titleid} ===")

        collection_info = self.get_collection_info(titleid)
        total_pages = collection_info.get("total_pages", 10)

        print(f"Total pages: {total_pages}")

        if max_pages:
            total_pages = min(int(total_pages), max_pages)

        poems = []

        for pageno in range(start_page, total_pages + 1):
            poem_data = self.scrape_poem_page(titleid, pageno)

            if poem_data and poem_data.get("content"):
                poems.append(poem_data)
                print(f"  ✓ Page {pageno}: {len(poem_data['content'])} characters")
            else:
                print(f"  ✗ Page {pageno}: No content found")

        return poems

    def save_poems_to_file(self, poems: List[Dict], filename: str):
        """
        Save poems to a text file

        Args:
            poems: List of poem dictionaries
            filename: Output filename
        """
        os.makedirs("scraped_poems", exist_ok=True)
        filepath = os.path.join("scraped_poems", filename)

        with open(filepath, "w", encoding="utf-8") as f:
            for poem in poems:
                f.write(f"{'='*80}\n")
                f.write(f"Title ID: {poem['titleid']}, Page: {poem['pageno']}\n")
                f.write(f"URL: {poem['url']}\n")
                f.write(f"{'='*80}\n\n")
                f.write(poem["content"])
                f.write(f"\n\n{'='*80}\n\n")

        print(f"Saved {len(poems)} poems to {filepath}")

    def scrape_all_collections(self, titleids: List[int] = None):
        """
        Scrape all collections

        Args:
            titleids: List of title IDs to scrape (default: 4-23)
            max_pages_per_collection: Maximum pages per collection (for testing)
        """
        if titleids is None:
            titleids = list(range(4, 24))

        all_poems = []

        for titleid in titleids:
            try:
                poems = self.scrape_collection(titleid)
                all_poems.extend(poems)

                if poems:
                    collection_filename = f"collection_{titleid}.txt"
                    self.save_poems_to_file(poems, collection_filename)

            except Exception as e:
                print(f"Error scraping collection {titleid}: {e}")
                continue

        if all_poems:
            self.save_poems_to_file(all_poems, "all_poems.txt")

        print(f"\n✓ Scraping completed! Total poems: {len(all_poems)}")
        return all_poems
