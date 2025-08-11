"""
Structured Data Lookup Tool
Queries financial metrics from SQLite database
"""

import sqlite3
import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger("finance_agent.structured_lookup")

class StructuredDataLookup:
    """Tool for querying specific financial metrics from SQLite database."""
    
    def __init__(self, db_path: str = None):
        if db_path:
            self.db_path = db_path
        else:
            # Try multiple paths: Modal volume, local data directory, or mock
            import os
            possible_paths = [
                "/data/costco_financial_data.db",  # Modal volume
                "data/costco_financial_data.db",    # Local relative
                "../data/costco_financial_data.db", # Parent directory
                os.path.expanduser("~/Documents/financeAgent/data/costco_financial_data.db")  # Absolute local
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    self.db_path = path
                    logger.info(f"Using database at: {path}")
                    break
            else:
                # No database found, use mock mode
                self.db_path = None
                logger.warning("No database found, using mock mode")
        
        # Common financial metrics mapping
        self.metric_mapping = {
            'revenue': ['total revenue', 'net sales', 'revenue'],
            'gross profit': ['gross profit', 'gross margin'],
            'net income': ['net income', 'net earnings', 'profit'],
            'operating income': ['operating income', 'operating profit'],
            'eps': ['earnings per share', 'eps'],
            'total assets': ['total assets', 'assets'],
            'total liabilities': ['total liabilities', 'liabilities'],
            'stockholders equity': ['stockholders equity', 'equity', 'shareholders equity'],
            'cash': ['cash and cash equivalents', 'cash'],
            'inventory': ['merchandise inventories', 'inventory'],
            'cost of goods': ['cost of goods sold', 'cogs', 'cost of sales'],
            'operating expenses': ['operating expenses', 'sg&a', 'selling general'],
            'depreciation': ['depreciation', 'amortization', 'd&a'],
            'working capital': ['working capital', 'current assets', 'current liabilities'],
            'long term debt': ['long term debt', 'long-term debt', 'lt debt'],
            'retained earnings': ['retained earnings', 'accumulated earnings'],
        }
        
    def query(self, question: str) -> str:
        """Query structured financial data based on the question."""
        try:
            # Check if we're in mock mode
            if self.db_path is None:
                return self._mock_query(question)
            
            # Extract key information from the question
            query_info = self._extract_query_info(question)
            
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build and execute query
            sql = self._build_sql_query(query_info)
            logger.debug(f"Executing SQL: {sql}")
            cursor.execute(sql)
            
            results = cursor.fetchall()
            conn.close()
            
            # Format results
            if results:
                return self._format_results(results, query_info)
            else:
                return "No data found for the specified query."
                
        except Exception as e:
            logger.error(f"Error querying structured data: {str(e)}")
            return f"Error querying structured data: {str(e)}"
    
    def _extract_query_info(self, question: str) -> Dict:
        """Extract metric, year, and other info from question."""
        question_lower = question.lower()
        
        # Extract metric
        metric = None
        for key, patterns in self.metric_mapping.items():
            for pattern in patterns:
                if pattern in question_lower:
                    metric = key
                    break
            if metric:
                break
        
        # Extract year(s)
        years = []
        year_matches = re.findall(r'20\d{2}', question)
        if year_matches:
            years = [int(y) for y in year_matches]
        
        # Check for time range indicators
        is_trend = any(word in question_lower for word in ['trend', 'last', 'past', 'recent', 'years', 'history'])
        
        # Check for comparison indicators
        is_comparison = any(word in question_lower for word in ['compare', 'versus', 'vs', 'between', 'difference'])
        
        return {
            'metric': metric, 
            'years': years,
            'is_trend': is_trend,
            'is_comparison': is_comparison
        }
    
    def _build_sql_query(self, query_info: Dict) -> str:
        """Build SQL query based on extracted information."""
        base_query = "SELECT item, fiscal_year, value, unit FROM financial_data"
        conditions = []
        
        if query_info['metric']:
            conditions.append(f"LOWER(item) LIKE '%{query_info['metric'].lower()}%'")
        
        if query_info['years']:
            if len(query_info['years']) == 1:
                conditions.append(f"fiscal_year = {query_info['years'][0]}")
            else:
                year_list = ','.join(str(y) for y in query_info['years'])
                conditions.append(f"fiscal_year IN ({year_list})")
        elif query_info['is_trend']:
            # Get last 3-5 years if trend requested but no specific years
            conditions.append("fiscal_year >= 2020")
        
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        
        base_query += " ORDER BY fiscal_year DESC"
        
        # Limit results based on query type
        if not query_info['is_trend'] and not query_info['is_comparison']:
            base_query += " LIMIT 1"
        else:
            base_query += " LIMIT 10"
            
        return base_query
    
    def _format_results(self, results: List, query_info: Dict) -> str:
        """Format SQL results into readable text."""
        if not results:
            return "No results found."
        
        # Single result
        if len(results) == 1:
            item, year, value, unit = results[0]
            return self._format_single_result(item, year, value, unit)
        
        # Multiple results - format as trend or comparison
        formatted = []
        for item, year, value, unit in results:
            formatted.append(self._format_single_result(item, year, value, unit))
        
        return "\n".join(formatted)
    
    def _format_single_result(self, item: str, year: int, value: float, unit: str) -> str:
        """Format a single result row."""
        if unit == 'millions':
            return f"{item} ({year}): ${value:,.0f} million"
        elif unit == 'billions':
            return f"{item} ({year}): ${value:,.2f} billion"
        elif unit == 'percent':
            return f"{item} ({year}): {value}%"
        elif unit == 'dollars':
            return f"{item} ({year}): ${value:.2f}"
        elif unit == 'ratio':
            return f"{item} ({year}): {value:.2f}"
        else:
            return f"{item} ({year}): {value} {unit}"
    
    def _mock_query(self, question: str) -> str:
        """Return mock data for testing when database is not available."""
        question_lower = question.lower()
        
        # Mock data for common queries
        if "revenue" in question_lower and "2024" in question:
            return "Total Revenue (2024): $254,123 million"
        elif "revenue" in question_lower and "2023" in question:
            return "Total Revenue (2023): $242,290 million"
        elif "gross profit" in question_lower:
            return "Gross Profit (2024): $36,789 million"
        elif "net income" in question_lower:
            return "Net Income (2024): $7,367 million"
        elif "operating income" in question_lower:
            return "Operating Income (2024): $9,275 million"
        elif "cash" in question_lower:
            return "Cash and Cash Equivalents (2024): $17,862 million"
        elif "assets" in question_lower:
            return "Total Assets (2024): $68,925 million"
        elif "eps" in question_lower:
            return "Earnings Per Share (2024): $16.63"
        else:
            return "Mock data: Financial metric would be retrieved from database"
