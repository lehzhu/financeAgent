from typing import Dict, Any, List

SCHEMAS = {
    "answer": {
        "id": str,
        "final_answer": dict,
        "trace": list,
        "assumptions": list,
        "sources": list
    }
}

class AnswerFormatter:
    def ensure_schema(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        # enforce keys and safe defaults
        return {
            "id": str(obj.get("id", "")),
            "final_answer": self._ensure_final(obj.get("final_answer", {})),
            "trace": obj.get("trace", []),
            "assumptions": obj.get("assumptions", []),
            "sources": obj.get("sources", [])
        }

    def _ensure_final(self, fa: Dict[str, Any]) -> Dict[str, Any]:
        t = fa.get("type", "text")
        v = str(fa.get("value", ""))
        if t in ("number", "percent", "ratio"):
            # ensure numeric returned as string
            try:
                _ = str(v)
            except Exception:
                v = "0"
        return {"type": t, "value": v}

