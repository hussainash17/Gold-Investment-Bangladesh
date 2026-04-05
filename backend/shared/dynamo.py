import os
import boto3
from decimal import Decimal

REGION = os.environ.get("AWS_DEFAULT_REGION", "ap-southeast-1")
PRICE_TABLE = os.environ.get("PRICE_TABLE", "gold-prices")

# LocalStack Pro sets LOCALSTACK_HOSTNAME inside Lambda containers.
# Outside Lambda (scripts, tests), fall back to LOCALSTACK_ENDPOINT.
_ls_hostname = os.environ.get("LOCALSTACK_HOSTNAME")
_ls_port = os.environ.get("EDGE_PORT", "4566")
ENDPOINT_URL = (
    f"http://{_ls_hostname}:{_ls_port}"
    if _ls_hostname
    else os.environ.get("LOCALSTACK_ENDPOINT", None)
)


def get_dynamodb():
    kwargs = dict(region_name=REGION)
    if ENDPOINT_URL:
        kwargs["endpoint_url"] = ENDPOINT_URL
    return boto3.resource("dynamodb", **kwargs)


def get_price_table():
    return get_dynamodb().Table(PRICE_TABLE)


def put_price(price_dict: dict):
    """Store a daily gold price record. date is the partition key."""
    table = get_price_table()
    # DynamoDB requires Decimal for floats
    item = {k: Decimal(str(v)) if isinstance(v, float) else v
            for k, v in price_dict.items()}
    table.put_item(Item=item)


def get_price(date: str) -> dict | None:
    table = get_price_table()
    resp = table.get_item(Key={"date": date})
    return resp.get("Item")


def get_prices_range(start_date: str, end_date: str) -> list[dict]:
    """Scan prices between two ISO dates (inclusive). Uses FilterExpression."""
    from boto3.dynamodb.conditions import Attr
    table = get_price_table()
    resp = table.scan(
        FilterExpression=Attr("date").between(start_date, end_date)
    )
    items = resp.get("Items", [])
    # Handle pagination
    while "LastEvaluatedKey" in resp:
        resp = table.scan(
            FilterExpression=Attr("date").between(start_date, end_date),
            ExclusiveStartKey=resp["LastEvaluatedKey"]
        )
        items.extend(resp.get("Items", []))
    return sorted(items, key=lambda x: x["date"])


def get_latest_price() -> dict | None:
    """Get the most recently scraped price record."""
    from boto3.dynamodb.conditions import Attr
    table = get_price_table()
    resp = table.scan(
        FilterExpression=Attr("date").exists()
    )
    items = resp.get("Items", [])
    while "LastEvaluatedKey" in resp:
        resp = table.scan(ExclusiveStartKey=resp["LastEvaluatedKey"])
        items.extend(resp.get("Items", []))
    if not items:
        return None
    return max(items, key=lambda x: x["date"])
