"""
Debug script — fetches bajus.org with Playwright and dumps:
  1. The raw HTML to debug_output.html (open in browser to verify)
  2. All <table>, <tr>, <td> text so we can see the price structure

Usage:
    python scripts/debug_scraper.py
"""
import re
import sys
import os
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

BAJUS_URL = "https://www.bajus.org/gold-price"
OUT_FILE = os.path.join(os.path.dirname(__file__), "debug_output.html")


def main():
    print("Fetching bajus.org with Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ))
        page.goto(BAJUS_URL, wait_until="networkidle", timeout=30000)
        html = page.content()
        browser.close()

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Raw HTML saved to: {OUT_FILE}")

    soup = BeautifulSoup(html, "html.parser")

    print("\n--- All TABLE rows ---")
    for i, row in enumerate(soup.find_all("tr")):
        cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
        if cells:
            print(f"  Row {i}: {cells}")

    print("\n--- Text containing 'carat' or 'ক্যারেট' or 'sanatan' ---")
    for el in soup.find_all(string=re.compile(r"carat|ক্যারেট|সনাতন|gold", re.IGNORECASE)):
        print(f"  [{el.parent.name}] {el.strip()!r}")

    print("\n--- All numbers that look like gold prices (5-7 digits) ---")
    for el in soup.find_all(string=re.compile(r"\b\d{4,7}\b")):
        txt = el.strip()
        if txt:
            print(f"  [{el.parent.name}] {txt!r}")


if __name__ == "__main__":
    main()
