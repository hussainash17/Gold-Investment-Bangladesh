"""
Seed historical gold prices from backend/prices.csv into DynamoDB.

CSV columns: date, k18, k21, k22, traditional (all BDT per gram)
Converts to per-bhari (× 11.664) before storing — consistent with scraper records.
Uses DynamoDB batch_writer (25 items/request) for speed.
Overwrites existing records — idempotent, safe to run multiple times.

Usage:
    python scripts/seed_historical.py
"""

import csv
import os
import sys
from decimal import Decimal, ROUND_HALF_UP

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("LOCALSTACK_ENDPOINT", "http://localhost:4566")
os.environ.setdefault("AWS_DEFAULT_REGION", "ap-southeast-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("PRICE_TABLE", "gold-prices")

from backend.shared.dynamo import get_price_table

CSV_PATH = os.path.join(os.path.dirname(__file__), "../backend/prices.csv")
GRAMS_PER_BHARI = Decimal("11.664")

# CSV column → DynamoDB field
COLUMN_MAP = {
    "k22": "karat_22",
    "k21": "karat_21",
    "k18": "karat_18",
    "traditional": "sanatan",
}


def to_bhari(price_per_gram_str: str) -> Decimal:
    return (Decimal(price_per_gram_str) * GRAMS_PER_BHARI).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def load_csv() -> list[dict]:
    records = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        # Skip leading blank lines before passing to DictReader
        lines = (line for line in f if line.strip())
        reader = csv.DictReader(lines)
        for row in reader:
            date = row["date"].strip()
            if not date:
                continue

            record = {
                "date": date,
                "currency": "BDT",
                "unit": "bhari",
                "source": "historical",
            }

            for csv_col, db_field in COLUMN_MAP.items():
                val = row.get(csv_col, "").strip()
                if val:
                    record[db_field] = to_bhari(val)

            records.append(record)
    return records


def seed(records: list[dict]):
    table = get_price_table()
    total = len(records)

    with table.batch_writer() as batch:
        for i, record in enumerate(records, 1):
            batch.put_item(Item=record)
            if i % 50 == 0 or i == total:
                print(f"  Queued {i}/{total} records...")

    print(f"Done. {total} records written to DynamoDB.")


if __name__ == "__main__":
    print(f"Loading CSV from: {CSV_PATH}")
    records = load_csv()
    print(f"Loaded {len(records)} records ({records[0]['date']} to {records[-1]['date']})")
    print("Seeding DynamoDB...")
    seed(records)
