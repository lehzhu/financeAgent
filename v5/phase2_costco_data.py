"""
V5 Phase 2: Costco Financial Data Agent

This agent can answer real questions about Costco's financial data
by querying the SQLite database with actual 10-K data.

Focus: Get the business context working!
"""

import sqlite3
import re
import os
from typing import Optional, Dict, Any


class CostcoDataAgent:
    """Agent that understands Costco's financial data."""
    
    def __init__(self, db_path: Optional[str] = None):
        # Resolve DB path with precedence: argument > ENV > default relative path
        if db_path is not None:
            resolved = db_path
        else:
            env_path = os.getenv("FINANCEAGENT_DB")
            if env_path:
                resolved = env_path
            else:
                # default to v5/../data/costco_financial_data.db
                base_dir = os.path.dirname(os.path.abspath(__file__))
                resolved = os.path.normpath(os.path.join(base_dir, "..", "data", "costco_financial_data.db"))
        
        self.db_path = resolved
        
        # Mapping of common question terms to database fields
        self.field_mapping = {
            # Revenue related
            "revenue": "Total Revenue",
            "total revenue": "Total Revenue", 
            "net sales": "Net Sales",
            "sales": "Net Sales",
            
            # Profit related
            "net income": "Net Income",
            "profit": "Net Income",
            "earnings": "Net Income",
            
            # Operating metrics
            "operating income": "Operating Income",
            "operating profit": "Operating Income",
            "gross margin": "Gross Margin",
            
            # Other
            "membership fee": "Membership Fee Revenue",
            "membership fees": "Membership Fee Revenue",
            "membership revenue": "Membership Fee Revenue",
            "merchandise costs": "Merchandise Costs",
            "eps": "Earnings Per Share Diluted",
            "earnings per share": "Earnings Per Share Diluted",
        }
    
    def can_handle(self, question: str) -> bool:
        """Check if this agent can handle the question."""
        question_lower = question.lower()
        
        # Must mention Costco
        if "costco" not in question_lower:
            return False
        
        # Must be asking for financial data
        financial_terms = list(self.field_mapping.keys()) + ["assets", "liabilities", "cash flow"]
        return any(term in question_lower for term in financial_terms)
    
    def answer(self, question: str) -> str:
        """Answer questions about Costco's financial data."""
        try:
            # Extract what they're asking for
            field = self._identify_field(question)
            if not field:
                return "I couldn't identify what financial metric you're asking about."
            
            # Extract year
            year = self._extract_year(question)
            if not year:
                year = 2024  # Default to most recent
            
            # Query database
            result = self._query_database(field, year)
            if result:
                value, unit = result
                return self._format_answer(field, year, value, unit, question)
            else:
                return f"I don't have data for {field} in {year}."
                
        except Exception as e:
            return f"Error retrieving data: {str(e)}"
    
    def _identify_field(self, question: str) -> Optional[str]:
        """Identify which financial field the question is asking about."""
        question_lower = question.lower()
        
        # Special cases (check first to avoid partial matches like 'profit' in 'gross profit')
        if "gross profit" in question_lower:
            return "gross_profit"  # Special flag for gross profit calculation
        
        # Check each mapping
        for term, db_field in self.field_mapping.items():
            if term in question_lower:
                return db_field
        
        return None
    
    def _extract_year(self, question: str) -> Optional[int]:
        """Extract year from the question."""
        # Look for 4-digit years
        year_match = re.search(r'20(2[0-9])', question)
        if year_match:
            return int(year_match.group(0))
        
        # Look for "fiscal 2024", "FY 2024", etc.
        fiscal_match = re.search(r'(?:fiscal|fy)\s*20(2[0-9])', question.lower())
        if fiscal_match:
            return int(fiscal_match.group(0)[-4:])
        
        return None
    
    def _query_database(self, field: str, year: int) -> Optional[tuple]:
        """Query the database for specific field and year."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Special handling for gross profit
            if field == "gross_profit":
                # Gross Profit = Net Sales - Merchandise Costs
                cursor.execute("""
                    SELECT 
                        (SELECT value FROM financial_data WHERE item = 'Net Sales' AND fiscal_year = ?),
                        (SELECT value FROM financial_data WHERE item = 'Merchandise Costs' AND fiscal_year = ?)
                """, (year, year))
                result = cursor.fetchone()
                if result and result[0] and result[1]:
                    gross_profit = result[0] - result[1]
                    return (gross_profit, "millions")
            else:
                # Direct lookup
                cursor.execute("""
                    SELECT value, unit 
                    FROM financial_data 
                    WHERE item = ? AND fiscal_year = ?
                """, (field, year))
                result = cursor.fetchone()
                if result:
                    return result
            
            conn.close()
            
        except Exception as e:
            print(f"Database query error: {e}")
            return None
        
        return None
    
    def _format_answer(self, field: str, year: int, value: float, unit: str, question: str) -> str:
        """Format the answer nicely."""
        # Format the value
        if unit == "millions":
            if value >= 1000:
                formatted_value = f"${value/1000:.1f} billion"
            else:
                formatted_value = f"${value:,.0f} million"
        elif unit == "percent":
            formatted_value = f"{value}%"
        elif unit == "dollars":
            formatted_value = f"${value:.2f}"
        else:
            formatted_value = f"{value:,.2f}"
        
        # Create natural response
        if "fiscal" in question.lower() or "fy" in question.lower():
            year_text = f"fiscal year {year}"
        else:
            year_text = str(year)
        
        # Handle special field names for display
        display_field = field.lower()
        if field == "gross_profit":
            display_field = "gross profit"
        
        return f"Costco's {display_field} for {year_text} was {formatted_value}."


def phase2_costco_agent(question: str) -> str:
    """Phase 2 agent function for Costco data questions."""
    agent = CostcoDataAgent()
    
    if not agent.can_handle(question):
        return "This question doesn't appear to be about Costco's financial data."
    
    return agent.answer(question)


# Test the agent
if __name__ == "__main__":
    agent = CostcoDataAgent()
    
    test_questions = [
        "What was Costco's total revenue in fiscal 2024?",
        "What was Costco's net income for fiscal year 2024?", 
        "What are Costco's net sales in 2024?",
        "What was Costco's gross profit in 2024?",
        "What was Costco's operating income in 2024?",
        "What were Costco's membership fees in 2024?",
    ]
    
    print("Testing Phase 2: Costco Financial Data Agent")
    print("=" * 60)
    
    for question in test_questions:
        if agent.can_handle(question):
            answer = agent.answer(question)
            print(f"Q: {question}")
            print(f"A: {answer}")
        else:
            print(f"Q: {question}")
            print(f"A: Cannot handle this question")
        print()
