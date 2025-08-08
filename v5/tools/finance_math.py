from decimal import Decimal, getcontext, ROUND_HALF_EVEN
from typing import Dict, Any, List

getcontext().prec = 50

class MathError(Exception):
    pass

# Simple formula registry
FORMULAS = {
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
        "compute": lambda inp: (inp["OPERATING_INCOME"] / inp["REVENUE"]) * Decimal("100")
    },
    "GROSS_MARGIN": {
        "requires": ["GROSS_PROFIT", "REVENUE"],
        "compute": lambda inp: (inp["GROSS_PROFIT"] / inp["REVENUE"]) * Decimal("100")
    },
    "GROSS_PROFIT": {
        "requires": ["GROSS_PROFIT"],
        "compute": lambda inp: inp["GROSS_PROFIT"]
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

