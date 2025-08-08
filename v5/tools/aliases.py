from typing import Dict, Any

ALIASES = {
    # metric: (metric_id, requires, formula_hint)
    "ebitda": ("EBITDA", ["OPERATING_INCOME", "DEPRECIATION", "AMORTIZATION"], "OPERATING_INCOME + DEPRECIATION + AMORTIZATION"),
    "ebit": ("EBIT", ["OPERATING_INCOME"], "OPERATING_INCOME"),
    "operating margin": ("OPERATING_MARGIN", ["OPERATING_INCOME", "REVENUE"], "OPERATING_INCOME / REVENUE"),
    "operating profit margin": ("OPERATING_MARGIN", ["OPERATING_INCOME", "REVENUE"], "OPERATING_INCOME / REVENUE"),
    "gross margin": ("GROSS_MARGIN", ["GROSS_PROFIT", "REVENUE"], "GROSS_PROFIT / REVENUE"),
    "gross profit": ("GROSS_PROFIT", ["GROSS_PROFIT"], "GROSS_PROFIT")
}


def resolve_alias(payload: Dict[str, Any]) -> Dict[str, Any]:
    metric = payload.get("metric", "").strip().lower()

    # normalize phrasing for common question forms
    repl = [
        ("what is ", ""),
        ("?", ""),
        ("the ", ""),
        ("in the year ending", ""),
        ("for the year ending", ""),
        ("for the year", ""),
        ("year ending", ""),
    ]
    norm = metric
    for a, b in repl:
        norm = norm.replace(a, b)
    norm = " ".join(norm.split())

    # try exact alias first
    if norm in ALIASES:
        mid, reqs, formula = ALIASES[norm]
        return {"metric_id": mid, "requires": reqs, "formula": formula}

    # fuzzy: if question contains keyword, pick longest matching alias
    best = None
    for k in ALIASES.keys():
        if k in norm:
            if best is None or len(k) > len(best):
                best = k
    if best:
        mid, reqs, formula = ALIASES[best]
        return {"metric_id": mid, "requires": reqs, "formula": formula}

    # fallback: treat question as metric id string (will be rejected upstream if unsupported)
    mid = norm.replace(" ", "_").upper()
    return {"metric_id": mid, "requires": [], "formula": ""}

