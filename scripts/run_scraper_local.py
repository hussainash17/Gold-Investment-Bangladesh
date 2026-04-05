"""
Run the scraper Lambda locally (without deploying) for testing.
Usage: python scripts/run_scraper_local.py
"""
import os
import sys

os.environ.setdefault("LOCALSTACK_ENDPOINT", "http://localhost:4566")
os.environ.setdefault("AWS_DEFAULT_REGION", "ap-southeast-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("PRICE_TABLE", "gold-prices")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.lambdas.scraper.handler import lambda_handler

result = lambda_handler({}, {})
print(result)
