from __future__ import annotations
import json
import logging
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

# NOTE: Plug in your LLM provider in the _call_llm method. The orchestrator assumes
# function-calling like behavior where tools can be invoked with JSON in/out.

logger = logging.getLogger("finance_agent.orchestrator")

@dataclass
class OrchestratorConfig:
    model: str
    temperature: float = 0.2
    max_tokens: int = 1500
    json_mode: bool = True

class Orchestrator:
    def __init__(self, config: OrchestratorConfig):
        self.config = config
        # Lazy imports to keep this file light
        from tools.formatters import AnswerFormatter
        from agent.router.simple_router import SimpleRouter
        self.formatter = AnswerFormatter()
        self.router = SimpleRouter()

    def answer(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        item: {"id": str, "question": str, "context": Optional[Dict], ...}
        Returns strict JSON: {"id","final_answer","trace","assumptions","sources"}
        """
        q = item.get("question", "").strip()
        route = self.router.route(q, item.get("context"))
        try:
            if route == "calc" or route == "assumption-calc":
                result = self._handle_calc(q, item)
            elif route == "structured":
                result = self._handle_structured(q, item)
            else:
                result = self._handle_narrative(q, item)
        except Exception as e:
            logger.exception("orchestrator failure")
            result = {
                "id": item.get("id"),
                "final_answer": {
                    "type": "text",
                    "value": "ERROR"
                },
                "trace": ["exception: " + repr(e)],
                "assumptions": [],
                "sources": []
            }
        return self.formatter.ensure_schema(result)

    def _handle_calc(self, q: str, item: Dict[str, Any]) -> Dict[str, Any]:
        from tools.aliases import resolve_alias
        from tools.filings import fetch_filing_table
        from tools.units import normalize_units
        from tools.finance_math import compute_formula
        from tools.assumptions import apply_assumptions
        from tools.verifier import verify_consistency

        alias = resolve_alias({"metric": q})

        # If metric is unsupported by engine, fall back gracefully
        from tools.finance_math import FORMULAS
        if alias.get("metric_id") not in FORMULAS:
            return {
                "id": item.get("id"),
                "final_answer": {"type": "text", "value": "Metric not supported by engine (baseline)."},
                "trace": [f"unsupported metric_id: {alias.get('metric_id')}"] ,
                "assumptions": [],
                "sources": []
            }

        # For prototype, assume inputs embedded in context or table
        context = item.get("context", {})
        filing_link = context.get("filing_link")
        company = context.get("company")
        table_hint = context.get("table_hint", alias.get("metric_id"))
        period = context.get("period", {"type": "FY", "end": "1900-01-01"})

        sources = []
        table = None
        if filing_link and company:
            fetch = fetch_filing_table({
                "company": company,
                "filing_link": filing_link,
                "table_hint": table_hint,
                "period": period
            })
            sources.append(filing_link)
            table = fetch.get("table", [])

        # Assemble inputs from context or table
        inputs = {}
        for req in alias.get("requires", []):
            # naive extraction: look in context first, else 0
            val = None
            if "inputs" in context and req in context["inputs"]:
                val = context["inputs"][req]
            if val is None:
                val = "0"
            # normalize to USD if units provided
            from_units = context.get("units", {}).get(req)
            if from_units:
                norm = normalize_units({
                    "value": str(val),
                    "from_units": from_units,
                    "to_units": "USD",
                    "percent": False
                })
                inputs[req] = norm["value"]
            else:
                inputs[req] = str(val)

        comp = compute_formula({
            "metric_id": alias["metric_id"],
            "period": period,
            "inputs": inputs,
            "output_units": "USD" if "MARGIN" not in alias["metric_id"] else "percent",
            "rounding": {"quantize": "0.01", "mode": "ROUND_HALF_EVEN"}
        })

        assumptions = context.get("assumptions", [])
        adjusted = {}
        rationales = []
        if assumptions:
            adj = apply_assumptions({
                "assumptions": assumptions,
                "context": {"company": company or "", "period": period},
                "base_values": {alias["metric_id"]: comp["value"], **inputs}
            })
            adjusted = adj.get("adjusted_values", {})
            rationales = adj.get("rationales", [])

        verification = verify_consistency({
            "metric_id": alias["metric_id"],
            "computed": adjusted.get(alias["metric_id"], comp["value"]),
            "inputs": inputs
        })

        final_value = adjusted.get(alias["metric_id"], comp["value"])
        return {
            "id": item.get("id"),
            "final_answer": {
                "type": "number" if "MARGIN" not in alias["metric_id"] else "percent",
                "value": str(final_value)
            },
            "trace": comp.get("trace", []) + [
                {"op": "ASSUMPTIONS", "args": assumptions, "result": adjusted}
            ],
            "assumptions": rationales,
            "sources": sources
        }

    def _handle_structured(self, q: str, item: Dict[str, Any]) -> Dict[str, Any]:
        # Placeholder structured lookup path
        return {
            "id": item.get("id"),
            "final_answer": {"type": "text", "value": "N/A"},
            "trace": ["structured path not yet implemented"],
            "assumptions": [],
            "sources": []
        }

    def _handle_narrative(self, q: str, item: Dict[str, Any]) -> Dict[str, Any]:
        # Minimal baseline: echo with no hallucinations.
        return {
            "id": item.get("id"),
            "final_answer": {"type": "text", "value": "Cannot compute without structured context."},
            "trace": ["narrative fallback"],
            "assumptions": [],
            "sources": []
        }

    def _call_llm(self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Wire up to your LLM. Must return function-call directives or JSON content."""
        raise NotImplementedError

