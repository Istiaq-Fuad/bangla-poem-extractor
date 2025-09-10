import requests
from parsel import Selector
import time
import os
import re
import math
import json
import unicodedata
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

            if re.match(r"^kabita(\d*)$", class_name):
                # Get the HTML content of the p tag
                p_html = p.get()

                # Remove span tags and their content (tooltips)
                p_html = re.sub(r"<span[^>]*>.*?</span>", "", p_html, flags=re.DOTALL)

                # Create a new selector from the cleaned HTML
                cleaned_p = Selector(text=p_html)

                # Extract all text content
                text_parts = cleaned_p.css("::text").getall()
                line_text = "".join(text_parts).strip()

                # Remove any newlines within the content
                line_text = re.sub(r"\n+", " ", line_text)

                # Remove extra whitespaces
                line_text = re.sub(r"\s+", " ", line_text).strip()

                # 1. Unicode Normalization
                line_text = unicodedata.normalize("NFC", line_text)

                # 2. Normalize spacing around punctuation
                line_text = re.sub(r"([।?!,—])", r" \1 ", line_text)

                # Clean up any multiple spaces that might have been introduced
                line_text = re.sub(r"\s+", " ", line_text).strip()

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

            # 1. Unicode Normalization
            left_text = unicodedata.normalize("NFC", left_text)
            right_text = unicodedata.normalize("NFC", right_text)

            # 2. Normalize spacing around punctuation
            left_text = re.sub(r"([।?!,—])", r" \1 ", left_text)
            right_text = re.sub(r"([।?!,—])", r" \1 ", right_text)

            # Clean up any multiple spaces that might have been introduced
            left_text = re.sub(r"\s+", " ", left_text).strip()
            right_text = re.sub(r"\s+", " ", right_text).strip()

            if left_text or right_text:
                line = f"{left_text.rjust(left_col_width)} {right_text}"
                poem_lines.append(line.rstrip())

        return "\n".join(poem_lines)

    import re

    def get_kabita_indentation(self, class_name: str) -> str:
        """
        Indentation rule:
        - Primary: Based on the maximum digit in the suffix (4 spaces per max digit)
        - Secondary: Additional spacing based on length of digit string (2 spaces per extra digit)
        - Examples: kabita=4 spaces (base), kabita1=4 spaces, kabita11=6 spaces, kabita111=8 spaces, kabita2=8 spaces, kabita22=10 spaces
        """
        match = re.match(r"kabita(\d*)$", class_name)
        if not match:
            return ""

        digits = match.group(1)
        if not digits:  # Just 'kabita' with no number - give it base indentation
            return "    "  # 4 spaces base indentation

        # Primary spacing: based on maximum digit (4 spaces per max digit for more distinction)
        max_digit = max(int(d) for d in digits)
        base_spacing = 4 * max_digit

        # Additional spacing: based on length (2 extra spaces per additional digit beyond first)
        length_bonus = (len(digits) - 1) * 2

        total_spacing = base_spacing + length_bonus
        return " " * total_spacing

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
        self,
        titleid: int,
        start_page: int = 2,
        max_pages: Optional[int] = None,
        save_individual: bool = True,
        append_to_file: Optional[str] = None,
    ) -> List[Dict]:
        """
        Scrape all poems from a collection with optional saving

        Args:
            titleid: Title ID for the collection
            start_page: Starting page (usually 2, as page 1 is TOC)
            max_pages: Maximum number of pages to scrape
            save_individual: Whether to save collection to individual file
            append_to_file: If provided, append all poems to this file

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

                # Append to file if specified
                if append_to_file:
                    self.append_poem_to_file(poem_data, append_to_file)
            else:
                print(f"  ✗ Page {pageno}: No content found")

        # Save individual collection file if requested
        if save_individual and poems:
            collection_filename = f"collection_{titleid}.txt"
            self.save_poems_to_file(poems, collection_filename)

        return poems

    def process_poem_content(self, content: str) -> str:
        """
        Process poem content to add markers:
        - Remove text wrapped in square brackets [] (can be one-line or multi-line)
        - <start_poem> at the beginning
        - <end_poem> at the end
        - <line> before single newlines
        - <stanza> between double newlines and before <end_poem>

        Args:
            content: Raw poem content

        Returns:
            Processed poem content with markers
        """
        if not content.strip():
            return content

        # Remove text wrapped in square brackets (including multi-line)
        processed = re.sub(r"\[.*?\]", "", content, flags=re.DOTALL)

        # Start with the content, but only strip trailing whitespace to preserve indentation
        processed = processed.rstrip()

        # Replace multiple newlines (3 or more) with double newlines
        processed = re.sub(r"\n{3,}", "\n\n", processed)

        # Split by double newlines to handle stanzas
        parts = processed.split("\n\n")

        # Process each part (stanza)
        processed_parts = []
        for part in parts:
            if part.strip():
                # Split lines and add <line> at the end of each line
                lines = part.split("\n")
                processed_lines = []
                for line in lines:
                    if line.strip():  # Only process non-empty lines
                        processed_lines.append(line + "<line>")

                processed_parts.append("\n".join(processed_lines))

        # Join all parts with <stanza> separators
        if processed_parts:
            processed = "\n<stanza>\n".join(processed_parts)
        else:
            processed = ""

        # Add start marker, final stanza marker, and end marker
        if processed:
            processed = f"<start_poem>\n{processed}\n<stanza>\n<end_poem>"
        else:
            processed = "<start_poem>\n<stanza>\n<end_poem>"

        return processed

    def save_poems_to_file(self, poems: List[Dict], filename: str):
        """
        Save poems to both text and JSON files with processed content markers

        Args:
            poems: List of poem dictionaries
            filename: Output filename (without extension)
        """
        os.makedirs("scraped_poems", exist_ok=True)

        # Remove extension if provided and get base filename
        base_filename = os.path.splitext(filename)[0]

        # Prepare poems with processed content for saving
        processed_poems = []
        for poem in poems:
            processed_poem = poem.copy()
            processed_poem["content"] = self.process_poem_content(poem["content"])
            processed_poems.append(processed_poem)

        # Save as text file
        txt_filepath = os.path.join("scraped_poems", f"{base_filename}.txt")
        with open(txt_filepath, "w", encoding="utf-8") as f:
            for poem in processed_poems:
                # f.write(f"{'='*80}\n")
                # f.write(f"Title ID: {poem['titleid']}, Page: {poem['pageno']}\n")
                # f.write(f"URL: {poem['url']}\n")
                # f.write(f"{'='*80}\n\n")
                f.write(poem["content"])
                # f.write(f"\n\n{'='*80}\n\n")

        # Save as JSON file
        json_filepath = os.path.join("scraped_poems", f"{base_filename}.json")
        with open(json_filepath, "w", encoding="utf-8") as f:
            json.dump(processed_poems, f, ensure_ascii=False, indent=2)

        print(f"Saved {len(poems)} poems to {txt_filepath}")
        print(f"Saved {len(poems)} poems to {json_filepath}")

    def append_poem_to_file(self, poem: Dict, filename: str):
        """
        Append a single poem to both text and JSON files with processed content markers

        Args:
            poem: Poem dictionary
            filename: Output filename (without extension)
        """
        os.makedirs("scraped_poems", exist_ok=True)

        # Remove extension if provided and get base filename
        base_filename = os.path.splitext(filename)[0]

        # Process the poem content
        processed_poem = poem.copy()
        processed_poem["content"] = self.process_poem_content(poem["content"])

        # Append to text file
        txt_filepath = os.path.join("scraped_poems", f"{base_filename}.txt")
        with open(txt_filepath, "a", encoding="utf-8") as f:
            # f.write(f"{'='*80}\n")
            # f.write(
            # f"Title ID: {processed_poem['titleid']}, Page: {processed_poem['pageno']}\n"
            # )
            # f.write(f"URL: {processed_poem['url']}\n")
            # f.write(f"{'='*80}\n\n")
            f.write("\n" + processed_poem["content"])
            # f.write(f"\n\n{'='*80}\n\n")

        # Handle JSON file (load existing data, append new poem, save back)
        json_filepath = os.path.join("scraped_poems", f"{base_filename}.json")
        try:
            # Try to load existing JSON data
            if os.path.exists(json_filepath):
                with open(json_filepath, "r", encoding="utf-8") as f:
                    existing_poems = json.load(f)
            else:
                existing_poems = []

            # Append new processed poem
            existing_poems.append(processed_poem)

            # Save updated data
            with open(json_filepath, "w", encoding="utf-8") as f:
                json.dump(existing_poems, f, ensure_ascii=False, indent=2)

        except (json.JSONDecodeError, FileNotFoundError):
            # If JSON is corrupted or doesn't exist, start fresh
            with open(json_filepath, "w", encoding="utf-8") as f:
                json.dump([processed_poem], f, ensure_ascii=False, indent=2)

        print(
            f"Appended poem (Title ID: {poem['titleid']}, Page: {poem['pageno']}) to {txt_filepath}"
        )
        print(
            f"Appended poem (Title ID: {poem['titleid']}, Page: {poem['pageno']}) to {json_filepath}"
        )

    def scrape_all_collections(
        self,
        titleids: List[int] = None,
        save_individual: bool = True,
        save_combined: bool = True,
        append_to_file: Optional[str] = None,
        max_pages_per_collection: Optional[int] = None,
    ):
        """
        Scrape all collections with flexible saving options

        Args:
            titleids: List of title IDs to scrape (default: 4-23)
            save_individual: Whether to save each collection to separate files
            save_combined: Whether to save all poems to a combined file
            append_to_file: If provided, append all poems to this specific file
            max_pages_per_collection: Maximum pages per collection (for testing)
        """
        if titleids is None:
            titleids = list(range(4, 24))

        all_poems = []

        for titleid in titleids:
            try:
                poems = self.scrape_collection(
                    titleid,
                    max_pages=max_pages_per_collection,
                    save_individual=save_individual,
                    append_to_file=append_to_file,
                )
                all_poems.extend(poems)

            except Exception as e:
                print(f"Error scraping collection {titleid}: {e}")
                continue

        # Save combined file if requested
        if save_combined and all_poems:
            combined_filename = append_to_file if append_to_file else "all_poems.txt"
            if not append_to_file:  # Only save if we haven't been appending
                self.save_poems_to_file(all_poems, combined_filename)

        print(f"\n✓ Scraping completed! Total poems: {len(all_poems)}")
        return all_poems
