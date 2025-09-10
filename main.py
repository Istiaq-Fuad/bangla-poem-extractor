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

    # Example usage with new combined functionality:

    # 1. Scrape a single collection and append all poems to one file
    # print("\n1. Scraping collection with append functionality...")
    # scraper.scrape_collection(
    #     titleid=4,
    #     max_pages=3,
    #     save_individual=True,  # Also save individual collection file
    #     # append_to_file="all_poems_collection.txt",  # Append each poem as it's scraped
    # )

    # 2. Scrape multiple collections with different save options
    # print("\n2. Scraping multiple collections with flexible saving...")
    # scraper.scrape_all_collections(
    #     titleids=[4, 5],  # Only scrape collections 4 and 5 for testing
    #     max_pages_per_collection=2,  # Limit pages for testing
    #     save_individual=True,  # Save each collection separately
    #     save_combined=False,  # Don't create a combined file (we're using append)
    #     append_to_file="master_collection.txt",  # Append everything to this file
    # )

    # 3. Scrape all collections (uncomment for full scraping - will take a long time!)
    print("\n4. Scraping all collections...")
    scraper.scrape_all_collections(
        # save_individual=True,
        save_combined=True,
        append_to_file="complete_nazrul_collection.txt",
    )


if __name__ == "__main__":
    main()
