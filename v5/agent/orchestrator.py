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
        
        # Try to extract values from the question for simple calculations
        import re
        if alias["metric_id"] == "PERCENTAGE_OF":
            # Extract numbers from question like "15% of 1000000"
            numbers = re.findall(r'\d+', q)
            if len(numbers) >= 2:
                # First number is the percentage, second is the whole
                inputs["PART"] = str(float(numbers[0]) * float(numbers[1]) / 100)
                inputs["WHOLE"] = numbers[1]
        
        for req in alias.get("requires", []):
            if req not in inputs:  # Only fill if not already extracted
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
        
        # Determine if this is a percentage result
        metric_id = alias["metric_id"]
        is_percent = any([
            "MARGIN" in metric_id,
            "GROWTH" in metric_id,
            "PERCENTAGE" in metric_id,
            "RATIO" in metric_id and metric_id not in ["CURRENT_RATIO", "QUICK_RATIO", "DEBT_RATIO"],
            metric_id in ["ROE", "ROA", "ROIC", "FCF_CONVERSION", "CAGR"]
        ])
        
        return {
            "id": item.get("id"),
            "final_answer": {
                "type": "percent" if is_percent else "number",
                "value": str(final_value)
            },
            "trace": comp.get("trace", []) + [
                {"op": "ASSUMPTIONS", "args": assumptions, "result": adjusted}
            ],
            "assumptions": rationales,
            "sources": sources
        }

    def _handle_structured(self, q: str, item: Dict[str, Any]) -> Dict[str, Any]:
        """Handle structured data lookup from SQLite database."""
        from tools.structured_lookup import StructuredDataLookup
        
        try:
            lookup = StructuredDataLookup()
            result = lookup.query(q)
            
            # Parse the result to extract the value and units
            value = None
            unit = "USD"
            
            if result and result != "No data found for the specified query.":
                # Extract value and unit from formatted result
                # Example: "Total Revenue (2024): $254,123 million"
                import re
                # Look for pattern like "(year): $value unit" or "(year): value unit"
                match = re.search(r'\(\d{4}\):\s*\$?([\d,\.]+)\s*(million|billion|thousand|percent|%)?', result)
                if match:
                    value = match.group(1).replace(',', '')
                    unit_text = match.group(2) if match.group(2) else "USD"
                    if unit_text in ['million', 'millions']:
                        unit = "millions of USD"
                    elif unit_text in ['billion', 'billions']:
                        unit = "billions of USD"
                    elif unit_text in ['percent', '%']:
                        unit = "percent"
            
            if value:
                return {
                    "id": item.get("id"),
                    "final_answer": {
                        "type": "number" if unit != "percent" else "percent",
                        "value": str(value),
                        "unit": unit
                    },
                    "trace": [{"op": "STRUCTURED_LOOKUP", "query": q, "result": result}],
                    "assumptions": [],
                    "sources": ["SQLite: costco_financial_data.db"]
                }
            else:
                return {
                    "id": item.get("id"),
                    "final_answer": {"type": "text", "value": result or "No data found"},
                    "trace": [{"op": "STRUCTURED_LOOKUP", "query": q, "result": result}],
                    "assumptions": [],
                    "sources": ["SQLite: costco_financial_data.db"]
                }
                
        except Exception as e:
            logger.exception("Structured lookup failure")
            return {
                "id": item.get("id"),
                "final_answer": {"type": "text", "value": f"Error: {str(e)}"},
                "trace": [{"op": "STRUCTURED_LOOKUP_ERROR", "error": str(e)}],
                "assumptions": [],
                "sources": []
            }

    def _handle_narrative(self, q: str, item: Dict[str, Any]) -> Dict[str, Any]:
        """Handle narrative/conceptual questions using FAISS vector search."""
        from tools.narrative_search import NarrativeSearch
        
        try:
            search = NarrativeSearch()
            result = search.search(q)
            
            if result and "No relevant" not in result:
                # Summarize the narrative content
                summary = self._summarize_narrative(q, result)
                return {
                    "id": item.get("id"),
                    "final_answer": {"type": "text", "value": summary},
                    "trace": [{"op": "NARRATIVE_SEARCH", "query": q, "docs_retrieved": 5}],
                    "assumptions": [],
                    "sources": ["FAISS: Costco 10-K narrative sections"]
                }
            else:
                return {
                    "id": item.get("id"),
                    "final_answer": {"type": "text", "value": "No relevant information found in narrative sections."},
                    "trace": [{"op": "NARRATIVE_SEARCH", "query": q, "result": "no_docs"}],
                    "assumptions": [],
                    "sources": []
                }
                
        except Exception as e:
            logger.exception("Narrative search failure")
            return {
                "id": item.get("id"),
                "final_answer": {"type": "text", "value": f"Error: {str(e)}"},
                "trace": [{"op": "NARRATIVE_SEARCH_ERROR", "error": str(e)}],
                "assumptions": [],
                "sources": []
            }
    
    def _summarize_narrative(self, question: str, narrative_content: str) -> str:
        """Summarize narrative content to answer the question."""
        # For now, return a simple extraction
        # In production, this would use an LLM to synthesize
        lines = narrative_content.split('\n')
        relevant_lines = []
        for line in lines:
            if len(line.strip()) > 50:  # Skip short lines
                relevant_lines.append(line.strip())
                if len(relevant_lines) >= 3:  # Return first 3 relevant sentences
                    break
        
        if relevant_lines:
            return " ".join(relevant_lines)
        return "Information found but unable to extract relevant summary."

    def _call_llm(self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Wire up to your LLM. Must return function-call directives or JSON content."""
        raise NotImplementedError

