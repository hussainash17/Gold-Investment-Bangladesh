"""
DynamoDB performance benchmark — measures current Scan-based queries vs GetItem.

Usage:
    python scripts/benchmark_dynamo.py

Requires LocalStack running with gold-prices table seeded.
Prints avg/min/max latency + ScannedCount/Count for each operation.
"""
import os
import sys
import time
import statistics

os.environ.setdefault("LOCALSTACK_ENDPOINT", "http://localhost:4566")
os.environ.setdefault("AWS_DEFAULT_REGION", "ap-southeast-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("PRICE_TABLE", "gold-prices")

import boto3

TABLE = os.environ["PRICE_TABLE"]
ENDPOINT = os.environ["LOCALSTACK_ENDPOINT"]
REGION = os.environ["AWS_DEFAULT_REGION"]

client = boto3.client(
    "dynamodb",
    region_name=REGION,
    endpoint_url=ENDPOINT,
    aws_access_key_id="test",
    aws_secret_access_key="test",
)

RUNS = 10


def benchmark(label: str, fn, warmup: int = 2):
    """Run fn() RUNS times, discard first `warmup` results, print stats."""
    latencies = []
    last_resp = None
    for i in range(RUNS + warmup):
        t0 = time.perf_counter()
        last_resp = fn()
        elapsed_ms = (time.perf_counter() - t0) * 1000
        if i >= warmup:
            latencies.append(elapsed_ms)

    avg = statistics.mean(latencies)
    med = statistics.median(latencies)

    print(f"\n{'─' * 55}")
    print(f"  {label}")
    print(f"{'─' * 55}")
    print(f"  Avg      : {avg:.1f} ms")
    print(f"  Median   : {med:.1f} ms")
    print(f"  Min/Max  : {min(latencies):.1f} / {max(latencies):.1f} ms")

    if last_resp:
        scanned = last_resp.get("ScannedCount")
        count = last_resp.get("Count")
        cap = last_resp.get("ConsumedCapacity", {})

        if scanned is not None:
            ratio = f"  (filter efficiency: {count}/{scanned} = {count/scanned*100:.0f}%)" if scanned else ""
            print(f"  Count    : {count}  ScannedCount: {scanned}{ratio}")
        if cap:
            print(f"  CapUnits : {cap.get('CapacityUnits')}")

    return latencies


# ── 1. GetItem — single known date (O(1), direct key lookup) ──────────────────
def op_getitem_single():
    return client.get_item(
        TableName=TABLE,
        Key={"date": {"S": "2024-06-15"}},
        ReturnConsumedCapacity="TOTAL",
    )


# ── 2. Scan ALL — how get_latest_price() works today ─────────────────────────
def op_scan_all_for_latest():
    """Replicates current get_latest_price(): scan entire table, Python max()."""
    resp = client.scan(
        TableName=TABLE,
        FilterExpression="attribute_exists(#d)",
        ExpressionAttributeNames={"#d": "date"},
        ReturnConsumedCapacity="TOTAL",
    )
    items = resp.get("Items", [])
    while "LastEvaluatedKey" in resp:
        resp = client.scan(
            TableName=TABLE,
            ExclusiveStartKey=resp["LastEvaluatedKey"],
            ReturnConsumedCapacity="TOTAL",
        )
        items.extend(resp.get("Items", []))
    # Python-side max — same as current code
    _ = max(items, key=lambda x: x["date"]["S"]) if items else None
    return resp  # return last page resp for metadata


# ── 3. Scan + FilterExpression — how get_prices_range() works today ───────────
def op_scan_range_1year():
    """90-day range scan — typical history chart query."""
    return client.scan(
        TableName=TABLE,
        FilterExpression="#d BETWEEN :s AND :e",
        ExpressionAttributeNames={"#d": "date"},
        ExpressionAttributeValues={
            ":s": {"S": "2024-01-01"},
            ":e": {"S": "2024-12-31"},
        },
        ReturnConsumedCapacity="TOTAL",
    )


# ── 4. Scan + FilterExpression — narrow 30-day range ─────────────────────────
def op_scan_range_30days():
    return client.scan(
        TableName=TABLE,
        FilterExpression="#d BETWEEN :s AND :e",
        ExpressionAttributeNames={"#d": "date"},
        ExpressionAttributeValues={
            ":s": {"S": "2024-06-01"},
            ":e": {"S": "2024-06-30"},
        },
        ReturnConsumedCapacity="TOTAL",
    )


# ── 5. GetItem — known latest date (what optimized get_latest_price looks like) ─
def op_getitem_sentinel():
    """Simulates storing a '_latest_' sentinel key — O(1) latest lookup."""
    return client.get_item(
        TableName=TABLE,
        Key={"date": {"S": "_latest_"}},
        ReturnConsumedCapacity="TOTAL",
    )


if __name__ == "__main__":
    print("=" * 55)
    print("  DynamoDB Benchmark — Gold Prices Table")
    print(f"  Table     : {TABLE}")
    print(f"  Endpoint  : {ENDPOINT}")
    print(f"  Runs      : {RUNS} (+ 2 warmup discarded)")
    print("=" * 55)

    # First, check table item count
    info = client.describe_table(TableName=TABLE)
    item_count = info["Table"].get("ItemCount", "unknown")
    print(f"\n  Table item count (approximate): {item_count}")

    benchmark("1. GetItem — exact date (O(1))", op_getitem_single)
    benchmark("2. Scan ALL — current get_latest_price()", op_scan_all_for_latest)
    benchmark("3. Scan + Filter — 1-year range (current get_prices_range)", op_scan_range_1year)
    benchmark("4. Scan + Filter — 30-day range (current get_prices_range)", op_scan_range_30days)
    benchmark("5. GetItem '_latest_' sentinel (optimized latest — key missing, fast miss)", op_getitem_sentinel)

    print(f"\n{'=' * 55}")
    print("  Done. Compare op 1 vs op 2 for get_latest_price cost.")
    print("  Compare op 3/4 vs op 1 for range query cost.")
    print("=" * 55)
