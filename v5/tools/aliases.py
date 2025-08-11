from typing import Dict, Any

ALIASES = {
    # metric: (metric_id, requires, formula_hint)
    # Profitability metrics
    "ebitda": ("EBITDA", ["OPERATING_INCOME", "DEPRECIATION", "AMORTIZATION"], "OPERATING_INCOME + DEPRECIATION + AMORTIZATION"),
    "ebit": ("EBIT", ["OPERATING_INCOME"], "OPERATING_INCOME"),
    "operating margin": ("OPERATING_MARGIN", ["OPERATING_INCOME", "REVENUE"], "OPERATING_INCOME / REVENUE"),
    "operating profit margin": ("OPERATING_MARGIN", ["OPERATING_INCOME", "REVENUE"], "OPERATING_INCOME / REVENUE"),
    "gross margin": ("GROSS_MARGIN", ["GROSS_PROFIT", "REVENUE"], "GROSS_PROFIT / REVENUE"),
    "gross profit margin": ("GROSS_MARGIN", ["GROSS_PROFIT", "REVENUE"], "GROSS_PROFIT / REVENUE"),
    "net margin": ("NET_MARGIN", ["NET_INCOME", "REVENUE"], "NET_INCOME / REVENUE"),
    "profit margin": ("NET_MARGIN", ["NET_INCOME", "REVENUE"], "NET_INCOME / REVENUE"),
    "gross profit": ("GROSS_PROFIT", ["REVENUE", "COST_OF_GOODS_SOLD"], "REVENUE - COST_OF_GOODS_SOLD"),
    
    # Growth calculations
    "yoy growth": ("YOY_GROWTH", ["VALUE_CURRENT", "VALUE_PRIOR"], "(CURRENT - PRIOR) / PRIOR"),
    "year over year growth": ("YOY_GROWTH", ["VALUE_CURRENT", "VALUE_PRIOR"], "(CURRENT - PRIOR) / PRIOR"),
    "revenue growth": ("REVENUE_GROWTH", ["REVENUE_CURRENT", "REVENUE_PRIOR"], "(CURRENT - PRIOR) / PRIOR"),
    "growth rate": ("YOY_GROWTH", ["VALUE_CURRENT", "VALUE_PRIOR"], "(CURRENT - PRIOR) / PRIOR"),
    "cagr": ("CAGR", ["BEGIN_VALUE", "END_VALUE", "YEARS"], "((END/BEGIN)^(1/YEARS) - 1)"),
    "compound annual growth": ("CAGR", ["BEGIN_VALUE", "END_VALUE", "YEARS"], "((END/BEGIN)^(1/YEARS) - 1)"),
    
    # Liquidity metrics
    "current ratio": ("CURRENT_RATIO", ["CURRENT_ASSETS", "CURRENT_LIABILITIES"], "CURRENT_ASSETS / CURRENT_LIABILITIES"),
    "quick ratio": ("QUICK_RATIO", ["CURRENT_ASSETS", "INVENTORY", "CURRENT_LIABILITIES"], "(CURRENT_ASSETS - INVENTORY) / CURRENT_LIABILITIES"),
    "working capital": ("WORKING_CAPITAL", ["CURRENT_ASSETS", "CURRENT_LIABILITIES"], "CURRENT_ASSETS - CURRENT_LIABILITIES"),
    
    # Leverage metrics
    "debt to equity": ("DEBT_TO_EQUITY", ["TOTAL_DEBT", "TOTAL_EQUITY"], "TOTAL_DEBT / TOTAL_EQUITY"),
    "debt ratio": ("DEBT_RATIO", ["TOTAL_DEBT", "TOTAL_ASSETS"], "TOTAL_DEBT / TOTAL_ASSETS"),
    
    # Return metrics
    "roe": ("ROE", ["NET_INCOME", "TOTAL_EQUITY"], "NET_INCOME / TOTAL_EQUITY"),
    "return on equity": ("ROE", ["NET_INCOME", "TOTAL_EQUITY"], "NET_INCOME / TOTAL_EQUITY"),
    "roa": ("ROA", ["NET_INCOME", "TOTAL_ASSETS"], "NET_INCOME / TOTAL_ASSETS"),
    "return on assets": ("ROA", ["NET_INCOME", "TOTAL_ASSETS"], "NET_INCOME / TOTAL_ASSETS"),
    "roic": ("ROIC", ["NOPAT", "INVESTED_CAPITAL"], "NOPAT / INVESTED_CAPITAL"),
    
    # Cash flow metrics
    "free cash flow": ("FREE_CASH_FLOW", ["OPERATING_CASH_FLOW", "CAPEX"], "OPERATING_CASH_FLOW - CAPEX"),
    "fcf": ("FREE_CASH_FLOW", ["OPERATING_CASH_FLOW", "CAPEX"], "OPERATING_CASH_FLOW - CAPEX"),
    "fcf conversion": ("FCF_CONVERSION", ["FREE_CASH_FLOW", "NET_INCOME"], "FREE_CASH_FLOW / NET_INCOME"),
    
    # Simple calculations
    "percentage": ("PERCENTAGE_OF", ["PART", "WHOLE"], "PART / WHOLE * 100"),
    "percent of": ("PERCENTAGE_OF", ["PART", "WHOLE"], "PART / WHOLE * 100"),
    "what percent": ("PERCENTAGE_OF", ["PART", "WHOLE"], "PART / WHOLE * 100"),
    "multiply": ("MULTIPLY", ["VALUE1", "VALUE2"], "VALUE1 * VALUE2"),
    "divide": ("DIVIDE", ["NUMERATOR", "DENOMINATOR"], "NUMERATOR / DENOMINATOR"),
    "add": ("ADD", ["VALUE1", "VALUE2"], "VALUE1 + VALUE2"),
    "subtract": ("SUBTRACT", ["VALUE1", "VALUE2"], "VALUE1 - VALUE2")
}


def resolve_alias(payload: Dict[str, Any]) -> Dict[str, Any]:
    metric = payload.get("metric", "").strip().lower()

    # Special handling for "X% of Y" pattern
    import re
    percent_pattern = re.match(r'.*?(\d+)%\s+of\s+(\d+)', metric)
    if percent_pattern:
        # This is a simple percentage calculation
        return {"metric_id": "PERCENTAGE_OF", "requires": ["PART", "WHOLE"], "formula": "PART / WHOLE * 100"}
    
    # normalize phrasing for common question forms
    repl = [
        ("what is ", ""),
        ("?", ""),
        ("the ", ""),
        ("calculate ", ""),
        ("compute ", ""),
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

