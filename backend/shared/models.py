from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional


@dataclass
class GoldPrice:
    date: str          # ISO format: YYYY-MM-DD
    karat_22: Decimal
    karat_21: Decimal
    karat_18: Decimal
    karat_24: Decimal
    sanatan: Decimal
    currency: str = "BDT"
    unit: str = "bhari"
    source: str = "bajus.org"


KARAT_LABELS = {
    "karat_22": "২২ ক্যারেট",
    "karat_21": "২১ ক্যারেট",
    "karat_18": "১৮ ক্যারেট",
    "karat_24": "২৪ ক্যারেট (পাকা)",
    "sanatan": "সনাতন",
}

KARAT_KEYS = list(KARAT_LABELS.keys())
