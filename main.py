"""
Bangla Poem Scraper for Nazrul Rachanabali
Scrapes poems from https://nazrul-rachanabali.nltr.org while preserving formatting
"""

import requests
from parsel import Selector
import time
import os
import re
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

from scraper import BanglaPoetryWebScraper


def main():
    """Main function to run the scraper"""
    print("Bangla Poetry Web Scraper")
    print("=" * 50)

    # Initialize scraper
    scraper = BanglaPoetryWebScraper(delay=1.0)  # 1 second delay between requests

    # Example usage:

    # 1. Scrape a single collection (titleid=4) with max 3 pages for testing
    # print("\n1. Testing with single collection...")
    # poems = scraper.scrape_collection(titleid=4, max_pages=3)
    # if poems:
    #     scraper.save_poems_to_file(poems, "test_collection_4.txt")

    # 2. Scrape multiple collections (uncomment to run)
    # print("\n2. Scraping multiple collections...")
    # scraper.scrape_all_collections(titleids=[4, 5, 6], max_pages_per_collection=5)

    # 3. Scrape all collections (uncomment for full scraping - will take a long time!)
    print("\n3. Scraping all collections...")
    scraper.scrape_all_collections()


if __name__ == "__main__":
    main()
