class SimpleRouter:
    """
    Enhanced heuristic router for financial questions.
    Returns one of: "calc", "assumption-calc", "structured", "narrative".
    """
    
    # Keywords that strongly indicate calculation needs
    CALC_KEYWORDS = [
        "calculate", "compute", "what is", "what's",
        "growth rate", "percentage", "percent of",
        "margin", "ratio", "cagr", "compound",
        "increase", "decrease", "change",
        "times", "multiply", "divide",
        "average", "mean", "sum", "total of"
    ]
    
    # Financial metrics that might need calculation
    CALC_METRICS = [
        "ebitda", "ebit", "operating margin", "gross margin",
        "net margin", "profit margin", "roe", "roa", "roi",
        "debt ratio", "current ratio", "quick ratio",
        "free cash flow", "fcf", "working capital"
    ]

    # Keywords for structured data lookup
    STRUCTURED_KEYWORDS = [
        "revenue", "sales", "income", "profit", "earnings",
        "assets", "liabilities", "equity", "cash",
        "inventory", "expenses", "cost", "debt",
        "eps", "share", "dividend", "retained earnings"
    ]
    
    # Keywords for narrative/conceptual questions
    NARRATIVE_KEYWORDS = [
        "strategy", "risk", "business", "describe", "explain",
        "how does", "why", "what are the", "discuss", "overview",
        "operations", "management", "competition", "market",
        "segment", "product", "service", "customer",
        "plan", "outlook", "guidance", "challenge"
    ]

    # Assumption indicators
    ASSUMPTION_HINTS = [
        "exclude", "excluding", "include", "including",
        "adjust", "adjusted", "normalize", "normalized",
        "add back", "one-off", "one-time", "extraordinary",
        "sbc", "stock-based", "asc 842", "gaap", "non-gaap"
    ]

    def route(self, question: str, context=None) -> str:
        q = (question or "").lower()
        
        # Check for assumptions first (highest priority)
        if any(hint in q for hint in self.ASSUMPTION_HINTS):
            return "assumption-calc"
        
        # Count matches for each category
        calc_score = sum(1 for kw in self.CALC_KEYWORDS if kw in q)
        calc_score += sum(0.5 for metric in self.CALC_METRICS if metric in q)
        
        struct_score = sum(1 for kw in self.STRUCTURED_KEYWORDS if kw in q)
        
        narr_score = sum(1 for kw in self.NARRATIVE_KEYWORDS if kw in q)
        
        # Check for year mentions (indicates structured data)
        import re
        if re.search(r'20\d{2}', question):
            struct_score += 1
        
        # Check for mathematical operators
        if any(op in q for op in ['%', '+', '-', '*', '/', '=']):
            calc_score += 2
        
        # Decision logic
        if calc_score > 0 and calc_score >= max(struct_score, narr_score):
            # Check if it's a pure calculation or needs data lookup
            if struct_score > 0:
                # Might need to fetch data then calculate
                return "calc"  # The calc handler can fetch structured data if needed
            return "calc"
        
        if struct_score > narr_score:
            return "structured"
        
        if narr_score > 0:
            return "narrative"
        
        # Default: check context hint or fall back to structured
        if context and isinstance(context, dict):
            if context.get("structured"):
                return "structured"
            if context.get("narrative"):
                return "narrative"
        
        # Final fallback: structured (most common)
        return "structured"

