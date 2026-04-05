"""
Gold price scraper Lambda.
Triggered daily by EventBridge.
Scrapes bajus.org using Playwright (headless browser) and stores prices in DynamoDB.
"""

import json
import logging
import re
from datetime import date
from decimal import Decimal, InvalidOperation

from bs4 import BeautifulSoup

from shared.dynamo import put_price

logger = logging.getLogger()
logger.setLevel(logging.INFO)

BAJUS_URL = "https://www.bajus.org/gold-price"

# Maps scraped text patterns to our DynamoDB field names.
# Keys are lowercase substrings to match against cell text.
# bajus.org uses "TRADITIONAL Gold" for sanatan; no 24k listed.
KARAT_MAP = {
    "22 karat gold": "karat_22",
    "21 karat gold": "karat_21",
    "18 karat gold": "karat_18",
    "traditional gold": "sanatan",
}

# bajus.org prices are per gram — convert to per bhari (1 bhari = 11.664g)
GRAMS_PER_BHARI = Decimal("11.664")


def parse_prices(html: str) -> dict:
    """
    Parse gold prices from bajus.org HTML.
    Table structure: Product | Description | Price (BDT/GRAM)
    Converts per-gram prices to per-bhari before returning.
    """
    soup = BeautifulSoup(html, "html.parser")
    prices = {}

    rows = soup.find_all("tr")
    for row in rows:
        cells = row.find_all(["td", "th"])
        if len(cells) < 3:
            continue

        label = cells[0].get_text(strip=True).lower()
        price_text = cells[2].get_text(strip=True)  # 3rd column: "21,260 BDT/GRAM"

        field = None
        for key, val in KARAT_MAP.items():
            if key in label:
                field = val
                break

        if field is None:
            continue

        # Strip commas and non-numeric chars: "21,260 BDT/GRAM" → "21260"
        numeric = re.sub(r"[^\d.]", "", price_text.replace(",", ""))
        if not numeric:
            continue

        try:
            price_per_gram = Decimal(numeric)
            price_per_bhari = (price_per_gram * GRAMS_PER_BHARI).quantize(Decimal("1"))
            prices[field] = price_per_bhari
            logger.info(f"  {label!r} → {field}: {price_per_gram}/gram = {price_per_bhari}/bhari")
        except InvalidOperation:
            logger.warning(f"Could not parse price '{price_text}' for {field}")

    return prices


def scrape_with_playwright() -> str:
    """Use Playwright headless browser to fetch the rendered page HTML."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()
        page.goto(BAJUS_URL, wait_until="networkidle", timeout=30000)
        html = page.content()
        browser.close()
        return html


def lambda_handler(event, context):
    today = date.today().isoformat()
    logger.info(f"Scraping gold prices for {today}")

    try:
        html = scrape_with_playwright()
        prices = parse_prices(html)
    except Exception as e:
        logger.error(f"Scraping failed: {e}", exc_info=True)
        return {"statusCode": 500, "body": str(e)}

    if not prices:
        logger.error("No prices extracted — page structure may have changed")
        logger.error("Run debug_scraper.py to inspect the raw HTML")
        return {"statusCode": 500, "body": "No prices found"}

    expected_fields = {"karat_22", "karat_21", "karat_18", "sanatan"}
    missing = expected_fields - prices.keys()
    if missing:
        logger.warning(f"Missing fields: {missing}")

    record = {
        "date": today,
        "currency": "BDT",
        "unit": "bhari",
        "source": "bajus.org",
        **prices,
    }

    put_price(record)
    logger.info(f"Stored prices: {record}")

    return {
        "statusCode": 200,
        "body": json.dumps({"date": today, "prices": {k: str(v) for k, v in prices.items()}}),
    }
