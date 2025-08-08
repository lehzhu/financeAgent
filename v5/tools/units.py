from decimal import Decimal
from typing import Dict, Any

SCALES = {
    "USD": Decimal("1"),
    "USD_thousands": Decimal("1000"),
    "USD_millions": Decimal("1000000"),
    "USD_billions": Decimal("1000000000"),
    "percent": Decimal("1")
}


def normalize_units(payload: Dict[str, Any]) -> Dict[str, str]:
    value = Decimal(str(payload["value"]))
    from_units = payload.get("from_units", "USD")
    to_units = payload.get("to_units", "USD")
    percent = bool(payload.get("percent", False))

    if percent:
        # if input is like 12.3 (%) and to_units is percent, keep as-is
        return {"value": str(value), "units": "percent"}

    if from_units not in SCALES or to_units not in SCALES:
        raise ValueError("Unknown units")

    base = value * SCALES[from_units]
    dest = base / SCALES[to_units]
    return {"value": str(dest), "units": to_units}

