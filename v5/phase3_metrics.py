"""
Phase 3: Metrics Agent (Calculation + Data)

Computes:
- Profit margin (Net Income / Total Revenue * 100)
- Revenue growth ( (Revenue Y - Revenue X) / Revenue X * 100 )

Small, dependency-free, uses the same DB as Phase 2.
"""

import re
from typing import Optional
from phase2_costco_data import CostcoDataAgent


class MetricsAgent:
    def __init__(self, db_path: Optional[str] = None):
        self.data = CostcoDataAgent(db_path=db_path)
    
    def can_handle(self, question: str) -> bool:
        q = question.lower()
        # Needs to mention Costco and a metric we support
        if "costco" not in q:
            return False
        return any(term in q for term in ["margin", "growth", "growth rate"]) 
    
    def answer(self, question: str) -> str:
        q = question.lower()
        # Profit margin related
        if "margin" in q:
            year = self._extract_years(question)[-1] if self._extract_years(question) else 2024
            # Different margin types
            if "operating" in q:
                num = self._get_value("Operating Income", year)
                den = self._get_value("Total Revenue", year)
            elif "gross" in q:
                # Direct percent from DB if available
                gross = self._get_value("Gross Margin", year)
                if gross is not None:
                    return f"{gross:.1f}%"
                # fallback compute from sales-costs is not here; Phase 2 handles gross profit
                return "I couldn't find data to compute gross margin."
            else:
                # net profit margin
                num = self._get_value("Net Income", year)
                den = self._get_value("Total Revenue", year)
            
            if num is None or den is None or den == 0:
                return "I couldn't find the necessary data to compute margin."
            margin = (num / den) * 100
            return f"{margin:.1f}%"
        
        # Revenue growth YoY
        if "growth" in q:
            years = self._extract_years(question)
            if len(years) >= 2:
                y1, y2 = years[0], years[1]  # ordered by occurrence or via from/to detection below
                # If pattern 'from X to Y' exists, enforce mapping
                m = re.search(r"from\s+(20\d{2})\s+to\s+(20\d{2})", question.lower())
                if m:
                    y1, y2 = int(m.group(1)), int(m.group(2))
                else:
                    # otherwise, sort and pick min->max
                    y1, y2 = min(years), max(years)
            else:
                # single or no year -> assume latest and previous
                y2 = years[-1] if years else 2024
                y1 = y2 - 1
            rev2 = self._get_value("Total Revenue", y2)
            rev1 = self._get_value("Total Revenue", y1)
            if rev1 is None or rev2 is None or rev1 == 0:
                return "I couldn't find the necessary data to compute revenue growth."
            growth = ((rev2 - rev1) / rev1) * 100
            return f"{growth:.1f}%"
        
        return "Unsupported metric for Phase 3."
    
    def _extract_years(self, question: str):
        years = [int(y) for y in re.findall(r"(20\d{2})", question)]
        return years
    
    def _extract_year(self, question: str) -> Optional[int]:
        m = re.search(r"(20\d{2})", question)
        return int(m.group(1)) if m else None
    
    def _get_value(self, field: str, year: int) -> Optional[float]:
        # Reuse Phase 2 data layer
        result = self.data._query_database(field, year)
        if result:
            value, unit = result
            # values are stored in millions for financial metrics
            if unit == "millions":
                return value
            return value
        return None


def phase3_metrics_agent(question: str) -> str:
    agent = MetricsAgent()
    if not agent.can_handle(question):
        return "This question doesn't appear to be a Costco calculated metric."
    return agent.answer(question)

