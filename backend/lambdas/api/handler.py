"""
API Gateway Lambda handler.
Routes:
  GET /prices/latest        — latest gold price record
  GET /prices?start=&end=   — price history between dates
  GET /prices/roi           — ROI calculation (query params)
"""

import json
import logging
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from shared.dynamo import get_latest_price, get_price, get_prices_range
from shared.units import to_bhari, UNIT_LABELS, UNIT_TO_BHARI

logger = logging.getLogger()
logger.setLevel(logging.INFO)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,OPTIONS",
    "Content-Type": "application/json",
}


def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def ok(body: dict) -> dict:
    return {
        "statusCode": 200,
        "headers": CORS_HEADERS,
        "body": json.dumps(body, default=decimal_default),
    }


def error(status: int, message: str) -> dict:
    return {
        "statusCode": status,
        "headers": CORS_HEADERS,
        "body": json.dumps({"error": message}),
    }


def route_latest(_params: dict) -> dict:
    record = get_latest_price()
    if not record:
        return error(404, "No price data available yet")
    return ok(record)


def route_history(params: dict) -> dict:
    end = params.get("end", date.today().isoformat())
    start = params.get("start", (date.today() - timedelta(days=90)).isoformat())
    records = get_prices_range(start, end)
    return ok({"start": start, "end": end, "count": len(records), "prices": records})


def route_roi(params: dict) -> dict:
    """
    Calculate ROI for a gold purchase.
    Query params:
      buy_date  — ISO date of purchase
      amount    — quantity purchased
      unit      — bhari/ana/roti/gram/tola/ounce
      karat     — karat_22 / karat_21 / karat_18 / karat_24 / sanatan
    """
    required = ["buy_date", "amount", "unit", "karat"]
    for r in required:
        if r not in params:
            return error(400, f"Missing parameter: {r}")

    buy_date = params["buy_date"]
    karat = params["karat"]
    unit = params["unit"]

    if unit not in UNIT_TO_BHARI:
        return error(400, f"Invalid unit: {unit}. Valid: {list(UNIT_TO_BHARI.keys())}")

    valid_karats = {"karat_22", "karat_21", "karat_18", "karat_24", "sanatan"}
    if karat not in valid_karats:
        return error(400, f"Invalid karat: {karat}. Valid: {list(valid_karats)}")

    try:
        amount = Decimal(str(params["amount"]))
    except Exception:
        return error(400, "Invalid amount value")

    buy_record = get_price(buy_date)
    if not buy_record:
        return error(404, f"No price data for buy_date: {buy_date}")

    current_record = get_latest_price()
    if not current_record:
        return error(404, "No current price data available")

    amount_in_bhari = to_bhari(amount, unit)

    buy_price_per_bhari = Decimal(str(buy_record[karat]))
    current_price_per_bhari = Decimal(str(current_record[karat]))

    buy_value = (buy_price_per_bhari * amount_in_bhari).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    current_value = (current_price_per_bhari * amount_in_bhari).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    profit_loss = current_value - buy_value
    pct_change = ((profit_loss / buy_value) * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return ok({
        "buy_date": buy_date,
        "current_date": current_record["date"],
        "karat": karat,
        "amount": float(amount),
        "unit": unit,
        "unit_label": UNIT_LABELS.get(unit, unit),
        "amount_in_bhari": float(amount_in_bhari),
        "buy_price_per_bhari": float(buy_price_per_bhari),
        "current_price_per_bhari": float(current_price_per_bhari),
        "buy_value_bdt": float(buy_value),
        "current_value_bdt": float(current_value),
        "profit_loss_bdt": float(profit_loss),
        "percent_change": float(pct_change),
        "is_profit": profit_loss >= 0,
    })


def lambda_handler(event, context):
    method = event.get("httpMethod", "GET")
    path = event.get("path", "/")
    params = event.get("queryStringParameters") or {}

    logger.info(f"{method} {path} params={params}")

    if method == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    if path == "/prices/latest":
        return route_latest(params)
    elif path == "/prices/roi":
        return route_roi(params)
    elif path == "/prices":
        return route_history(params)
    else:
        return error(404, f"Unknown route: {path}")
