from decimal import Decimal, getcontext, ROUND_HALF_EVEN
from typing import Dict, Any, List

getcontext().prec = 50

class MathError(Exception):
    pass

# Simple helpers

def _safe_div(n: Decimal, d: Decimal) -> Decimal:
    try:
        if d == 0:
            return Decimal("0")
        return n / d
    except Exception:
        return Decimal("0")

# Enhanced formula registry with more financial calculations
FORMULAS = {
    # Profitability metrics
    "EBITDA": {
        "requires": ["OPERATING_INCOME", "DEPRECIATION", "AMORTIZATION"],
        "compute": lambda inp: inp["OPERATING_INCOME"] + inp["DEPRECIATION"] + inp["AMORTIZATION"]
    },
    "EBIT": {
        "requires": ["OPERATING_INCOME"],
        "compute": lambda inp: inp["OPERATING_INCOME"]
    },
    "OPERATING_MARGIN": {
        "requires": ["OPERATING_INCOME", "REVENUE"],
        "compute": lambda inp: _safe_div(inp["OPERATING_INCOME"], inp["REVENUE"]) * Decimal("100")
    },
    "GROSS_MARGIN": {
        "requires": ["GROSS_PROFIT", "REVENUE"],
        "compute": lambda inp: _safe_div(inp["GROSS_PROFIT"], inp["REVENUE"]) * Decimal("100")
    },
    "NET_MARGIN": {
        "requires": ["NET_INCOME", "REVENUE"],
        "compute": lambda inp: _safe_div(inp["NET_INCOME"], inp["REVENUE"]) * Decimal("100")
    },
    "GROSS_PROFIT": {
        "requires": ["REVENUE", "COST_OF_GOODS_SOLD"],
        "compute": lambda inp: inp["REVENUE"] - inp["COST_OF_GOODS_SOLD"]
    },
    
    # Growth calculations
    "REVENUE_GROWTH": {
        "requires": ["REVENUE_CURRENT", "REVENUE_PRIOR"],
        "compute": lambda inp: _safe_div(inp["REVENUE_CURRENT"] - inp["REVENUE_PRIOR"], inp["REVENUE_PRIOR"]) * Decimal("100")
    },
    "YOY_GROWTH": {
        "requires": ["VALUE_CURRENT", "VALUE_PRIOR"],
        "compute": lambda inp: _safe_div(inp["VALUE_CURRENT"] - inp["VALUE_PRIOR"], inp["VALUE_PRIOR"]) * Decimal("100")
    },
    "CAGR": {
        "requires": ["BEGIN_VALUE", "END_VALUE", "YEARS"],
        "compute": lambda inp: ((_safe_div(inp["END_VALUE"], inp["BEGIN_VALUE"]) ** _safe_div(Decimal("1"), inp["YEARS"])) - Decimal("1")) * Decimal("100")
    },
    
    # Liquidity ratios
    "CURRENT_RATIO": {
        "requires": ["CURRENT_ASSETS", "CURRENT_LIABILITIES"],
        "compute": lambda inp: _safe_div(inp["CURRENT_ASSETS"], inp["CURRENT_LIABILITIES"])
    },
    "QUICK_RATIO": {
        "requires": ["CURRENT_ASSETS", "INVENTORY", "CURRENT_LIABILITIES"],
        "compute": lambda inp: _safe_div(inp["CURRENT_ASSETS"] - inp["INVENTORY"], inp["CURRENT_LIABILITIES"])
    },
    "WORKING_CAPITAL": {
        "requires": ["CURRENT_ASSETS", "CURRENT_LIABILITIES"],
        "compute": lambda inp: inp["CURRENT_ASSETS"] - inp["CURRENT_LIABILITIES"]
    },
    
    # Leverage ratios
    "DEBT_TO_EQUITY": {
        "requires": ["TOTAL_DEBT", "TOTAL_EQUITY"],
        "compute": lambda inp: _safe_div(inp["TOTAL_DEBT"], inp["TOTAL_EQUITY"])
    },
    "DEBT_RATIO": {
        "requires": ["TOTAL_DEBT", "TOTAL_ASSETS"],
        "compute": lambda inp: _safe_div(inp["TOTAL_DEBT"], inp["TOTAL_ASSETS"])
    },
    
    # Return metrics
    "ROE": {
        "requires": ["NET_INCOME", "TOTAL_EQUITY"],
        "compute": lambda inp: _safe_div(inp["NET_INCOME"], inp["TOTAL_EQUITY"]) * Decimal("100")
    },
    "ROA": {
        "requires": ["NET_INCOME", "TOTAL_ASSETS"],
        "compute": lambda inp: _safe_div(inp["NET_INCOME"], inp["TOTAL_ASSETS"]) * Decimal("100")
    },
    "ROIC": {
        "requires": ["NOPAT", "INVESTED_CAPITAL"],
        "compute": lambda inp: _safe_div(inp["NOPAT"], inp["INVESTED_CAPITAL"]) * Decimal("100")
    },
    
    # Cash flow metrics
    "FREE_CASH_FLOW": {
        "requires": ["OPERATING_CASH_FLOW", "CAPEX"],
        "compute": lambda inp: inp["OPERATING_CASH_FLOW"] - inp["CAPEX"]
    },
    "FCF_CONVERSION": {
        "requires": ["FREE_CASH_FLOW", "NET_INCOME"],
        "compute": lambda inp: _safe_div(inp["FREE_CASH_FLOW"], inp["NET_INCOME"]) * Decimal("100")
    },
    
    # Simple calculations
    "PERCENTAGE_OF": {
        "requires": ["PART", "WHOLE"],
        "compute": lambda inp: _safe_div(inp["PART"], inp["WHOLE"]) * Decimal("100")
    },
    "MULTIPLY": {
        "requires": ["VALUE1", "VALUE2"],
        "compute": lambda inp: inp["VALUE1"] * inp["VALUE2"]
    },
    "DIVIDE": {
        "requires": ["NUMERATOR", "DENOMINATOR"],
        "compute": lambda inp: _safe_div(inp["NUMERATOR"], inp["DENOMINATOR"])
    },
    "ADD": {
        "requires": ["VALUE1", "VALUE2"],
        "compute": lambda inp: inp["VALUE1"] + inp["VALUE2"]
    },
    "SUBTRACT": {
        "requires": ["VALUE1", "VALUE2"],
        "compute": lambda inp: inp["VALUE1"] - inp["VALUE2"]
    }
}

ROUNDING_MODES = {
    "ROUND_HALF_EVEN": ROUND_HALF_EVEN
}


def _to_decimal_map(inputs: Dict[str, str]) -> Dict[str, Decimal]:
    out = {}
    for k, v in inputs.items():
        out[k] = Decimal(str(v))
    return out


def compute_formula(payload: Dict[str, Any]) -> Dict[str, Any]:
    metric_id = payload["metric_id"].upper()
    period = payload.get("period", {})
    inputs = payload.get("inputs", {})
    rounding = payload.get("rounding", {"quantize": "0.01", "mode": "ROUND_HALF_EVEN"})

    if metric_id not in FORMULAS:
        raise MathError(f"Unknown metric_id: {metric_id}")

    reqs = FORMULAS[metric_id]["requires"]
    for r in reqs:
        if r not in inputs:
            raise MathError(f"Missing input: {r}")

    din = _to_decimal_map(inputs)

    trace: List[Dict[str, Any]] = []

    if metric_id == "EBITDA":
        a = din["OPERATING_INCOME"] + din["DEPRECIATION"]
        trace.append({"op": "ADD", "args": ["OPERATING_INCOME", "DEPRECIATION"], "result": str(a)})
        b = a + din["AMORTIZATION"]
        trace.append({"op": "ADD", "args": ["<prev>", "AMORTIZATION"], "result": str(b)})
        value = b
    else:
        value = FORMULAS[metric_id]["compute"](din)
        # a minimal trace for single op formulas
        trace.append({"op": "COMPUTE", "args": reqs, "result": str(value)})

    q = Decimal(str(rounding.get("quantize", "0.01")))
    mode = ROUNDING_MODES.get(rounding.get("mode", "ROUND_HALF_EVEN"), ROUND_HALF_EVEN)
    value = value.quantize(q, rounding=mode)

    return {"value": str(value), "trace": trace}

