from decimal import Decimal
from typing import Dict, Any

POLICY = {
  "default_tolerance": Decimal("0.01"),
}

def verify_consistency(payload: Dict[str, Any]) -> Dict[str, Any]:
    metric_id = payload.get("metric_id", "")
    computed = Decimal(str(payload.get("computed", "0")))
    # For now, nothing to compare with besides basic sanity check
    ok = computed.is_finite()
    return {"ok": bool(ok), "tolerance": str(POLICY["default_tolerance"]) }

