"""
Gold unit conversion utilities.
Base unit: bhari (1 bhari = 11.664 grams)
"""

from decimal import Decimal

# All conversion factors relative to 1 bhari
BHARI_TO_GRAM = Decimal("11.664")
BHARI_TO_ANA = Decimal("16")
BHARI_TO_ROTI = Decimal("96")       # 1 bhari = 6 ana * 16 roti
BHARI_TO_TOLA = Decimal("1")        # 1 tola ≈ 1 bhari in Bangladesh
BHARI_TO_TROY_OZ = Decimal("0.375") # 1 bhari ≈ 0.375 troy oz

UNIT_TO_BHARI = {
    "bhari": Decimal("1"),
    "ana":   Decimal("1") / BHARI_TO_ANA,
    "roti":  Decimal("1") / BHARI_TO_ROTI,
    "gram":  Decimal("1") / BHARI_TO_GRAM,
    "tola":  Decimal("1"),
    "ounce": Decimal("1") / BHARI_TO_TROY_OZ,
}

UNIT_LABELS = {
    "bhari": "ভরি",
    "ana":   "আনা",
    "roti":  "রতি",
    "gram":  "গ্রাম",
    "tola":  "তোলা",
    "ounce": "আউন্স",
}


def to_bhari(amount: Decimal, unit: str) -> Decimal:
    """Convert any unit amount to bhari."""
    factor = UNIT_TO_BHARI.get(unit)
    if factor is None:
        raise ValueError(f"Unknown unit: {unit}")
    return amount * factor


def price_per_unit(price_per_bhari: Decimal, unit: str) -> Decimal:
    """Convert a per-bhari price to a per-unit price."""
    factor = UNIT_TO_BHARI.get(unit)
    if factor is None:
        raise ValueError(f"Unknown unit: {unit}")
    return price_per_bhari * factor
