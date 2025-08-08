from decimal import Decimal
from typing import Dict, Any

RULES = {
    "ASC842_ADD_BACK": lambda values: {
        "EBITDA": (Decimal(values.get("EBITDA", "0")) + Decimal(values.get("OPERATING_LEASE_EXP", "0"))).quantize(Decimal("0.01"))
    },
    "EXCLUDE_SBC": lambda values: {
        "EBITDA": (Decimal(values.get("EBITDA", "0")) + Decimal(values.get("SBC", "0"))).quantize(Decimal("0.01"))
    },
    "EXCLUDE_RESTRUCTURING": lambda values: {
        "EBITDA": (Decimal(values.get("EBITDA", "0")) + Decimal(values.get("RESTRUCTURING", "0"))).quantize(Decimal("0.01"))
    }
}


def apply_assumptions(payload: Dict[str, Any]) -> Dict[str, Any]:
    assumptions = payload.get("assumptions", [])
    base_values = payload.get("base_values", {})

    adjusted = {k: Decimal(str(v)) for k, v in base_values.items()}
    rationales = []

    for a in assumptions:
        rule = RULES.get(a)
        if not rule:
            continue
        delta = rule({k: str(v) for k, v in adjusted.items()})
        for k, v in delta.items():
            adjusted[k] = Decimal(str(v))
        rationales.append(f"Applied rule {a}")

    # stringify
    adjusted_str = {k: str(v) for k, v in adjusted.items()}
    return {"adjusted_values": adjusted_str, "rationales": rationales}

