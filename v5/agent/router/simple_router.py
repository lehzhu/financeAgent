class SimpleRouter:
    """
    Very lightweight heuristic router.
    Returns one of: "calc", "assumption-calc", "structured", "narrative".
    """
    CALC_KEYWORDS = [
        "margin", "ratio", "ebitda", "ebit", "operating income",
        "revenue", "gross profit", "net income", "free cash flow",
        "growth", "cagr", "ttm", "fy", "%"
    ]

    ASSUMPTION_HINTS = ["exclude sbc", "asc 842", "add back", "one-off", "adjust"]

    def route(self, question: str, context=None) -> str:
        q = (question or "").lower()
        if any(k in q for k in self.ASSUMPTION_HINTS):
            return "assumption-calc"
        if any(k in q for k in self.CALC_KEYWORDS):
            return "calc"
        if context and isinstance(context, dict) and context.get("structured"):
            return "structured"
        return "narrative"

