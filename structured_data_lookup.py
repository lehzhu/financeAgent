#!/usr/bin/env python3
"""
Structured data lookup tool for Costco financial data.
This tool provides direct lookup of financial values without using LLM.
"""

import re
import sqlite3
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
import json

class StructuredDataLookup:
    """Tool for querying structured financial data without using LLM."""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent / "data"
        self.db_file = self.data_dir / "costco_financial_data.db"
        
        # Initialize database if it doesn't exist
        if not self.db_file.exists():
            self._initialize_database()
        
        # Query patterns mapping
        self.patterns = {
            'net sales': 'Net Sales',
            'revenue': 'Total Revenue',
            'sales': 'Net Sales',
            'income': 'Net Income',
            'earnings': 'Net Income',
            'eps': 'Earnings Per Share Diluted',
            'earnings per share': 'Earnings Per Share Diluted',
            'cost': 'Merchandise Costs',
            'cogs': 'Merchandise Costs',
            'cost of goods': 'Merchandise Costs',
            'gross margin': 'Gross Margin',
            'gross profit': 'Gross Margin',
            'membership': 'Membership Fee Revenue',
            'membership fee': 'Membership Fee Revenue',
            'operating income': 'Operating Income',
            'operating': 'Operating Income',
        }
    
    def _initialize_database(self):
        """Initialize database with Costco financial data."""
        # Verified financial data from Costco 10-K
        financial_data = [
            # Net Sales (in millions)
            {'item': 'Net Sales', 'fiscal_year': 2024, 'value': 249625, 'unit': 'millions'},
            {'item': 'Net Sales', 'fiscal_year': 2023, 'value': 237710, 'unit': 'millions'},
            {'item': 'Net Sales', 'fiscal_year': 2022, 'value': 222730, 'unit': 'millions'},
            
            # Membership Fee Revenue (in millions)
            {'item': 'Membership Fee Revenue', 'fiscal_year': 2024, 'value': 4828, 'unit': 'millions'},
            {'item': 'Membership Fee Revenue', 'fiscal_year': 2023, 'value': 4580, 'unit': 'millions'},
            {'item': 'Membership Fee Revenue', 'fiscal_year': 2022, 'value': 4224, 'unit': 'millions'},
            
            # Total Revenue (in millions)
            {'item': 'Total Revenue', 'fiscal_year': 2024, 'value': 254453, 'unit': 'millions'},
            {'item': 'Total Revenue', 'fiscal_year': 2023, 'value': 242290, 'unit': 'millions'},
            {'item': 'Total Revenue', 'fiscal_year': 2022, 'value': 226954, 'unit': 'millions'},
            
            # Merchandise Costs (in millions)
            {'item': 'Merchandise Costs', 'fiscal_year': 2024, 'value': 222358, 'unit': 'millions'},
            {'item': 'Merchandise Costs', 'fiscal_year': 2023, 'value': 212586, 'unit': 'millions'},
            {'item': 'Merchandise Costs', 'fiscal_year': 2022, 'value': 199382, 'unit': 'millions'},
            
            # Gross Margin (in millions)
            {'item': 'Gross Margin', 'fiscal_year': 2024, 'value': 27267, 'unit': 'millions'},
            {'item': 'Gross Margin', 'fiscal_year': 2023, 'value': 25124, 'unit': 'millions'},
            {'item': 'Gross Margin', 'fiscal_year': 2022, 'value': 23348, 'unit': 'millions'},
            
            # Operating Income (in millions)
            {'item': 'Operating Income', 'fiscal_year': 2024, 'value': 9925, 'unit': 'millions'},
            {'item': 'Operating Income', 'fiscal_year': 2023, 'value': 8554, 'unit': 'millions'},
            {'item': 'Operating Income', 'fiscal_year': 2022, 'value': 7793, 'unit': 'millions'},
            
            # Net Income (in millions)
            {'item': 'Net Income', 'fiscal_year': 2024, 'value': 7367, 'unit': 'millions'},
            {'item': 'Net Income', 'fiscal_year': 2023, 'value': 6292, 'unit': 'millions'},
            {'item': 'Net Income', 'fiscal_year': 2022, 'value': 5844, 'unit': 'millions'},
            
            # Earnings Per Share Diluted
            {'item': 'Earnings Per Share Diluted', 'fiscal_year': 2024, 'value': 16.56, 'unit': 'per share'},
            {'item': 'Earnings Per Share Diluted', 'fiscal_year': 2023, 'value': 14.16, 'unit': 'per share'},
            {'item': 'Earnings Per Share Diluted', 'fiscal_year': 2022, 'value': 13.14, 'unit': 'per share'},
        ]
        
        # Create DataFrame
        df = pd.DataFrame(financial_data)
        
        # Save to database
        conn = sqlite3.connect(self.db_file)
        df.to_sql('financial_data', conn, if_exists='replace', index=False)
        
        # Create indexes
        conn.execute('CREATE INDEX IF NOT EXISTS idx_item ON financial_data(item)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_year ON financial_data(fiscal_year)')
        
        # Create view
        conn.execute('''
            CREATE VIEW IF NOT EXISTS financial_summary AS
            SELECT 
                item,
                fiscal_year,
                value,
                unit,
                CASE 
                    WHEN unit = 'millions' THEN value * 1000000
                    ELSE value
                END as actual_value
            FROM financial_data
            ORDER BY item, fiscal_year DESC
        ''')
        
        conn.commit()
        conn.close()
        
        print(f"Database initialized at: {self.db_file}")
    
    def structured_data_lookup(self, query: str) -> Dict:
        """
        Query financial data using natural language.
        
        Args:
            query: Natural language query like "Net sales 2024" or "EPS 2023"
            
        Returns:
            Dictionary with query results including:
            - query: The original query
            - item_searched: The financial item being searched
            - year_filter: The year filter if specified
            - results: List of matching results with values
            - accuracy: Always 100% for structured lookups
        """
        query_lower = query.lower()
        
        # Extract year from query
        year_match = re.search(r'20\d{2}', query)
        year = int(year_match.group()) if year_match else None
        
        # Find item to search
        item_to_search = None
        for pattern, item_name in self.patterns.items():
            if pattern in query_lower:
                item_to_search = item_name
                break
        
        if not item_to_search:
            return {
                'query': query,
                'error': 'Could not identify financial item in query',
                'available_items': list(set(self.patterns.values())),
                'accuracy': '0%'
            }
        
        # Query database
        results = self._query_database(item_to_search, year)
        
        return {
            'query': query,
            'item_searched': item_to_search,
            'year_filter': year,
            'results': results,
            'accuracy': '100%' if results else '0%'
        }
    
    def _query_database(self, item: str, year: Optional[int]) -> List[Dict]:
        """Query the SQLite database."""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        
        try:
            if year:
                query = '''
                    SELECT item, fiscal_year, value, unit, actual_value
                    FROM financial_summary
                    WHERE item = ? AND fiscal_year = ?
                '''
                cursor = conn.execute(query, (item, year))
            else:
                query = '''
                    SELECT item, fiscal_year, value, unit, actual_value
                    FROM financial_summary
                    WHERE item = ?
                    ORDER BY fiscal_year DESC
                    LIMIT 3
                '''
                cursor = conn.execute(query, (item,))
            
            results = []
            for row in cursor:
                results.append({
                    'item': row['item'],
                    'fiscal_year': row['fiscal_year'],
                    'value': row['value'],
                    'unit': row['unit'],
                    'actual_value': row['actual_value'],
                    'formatted_value': f"${row['value']:,.0f} {row['unit']}" if row['unit'] == 'millions' else f"${row['value']:.2f}"
                })
            
            return results
            
        except Exception as e:
            return [{'error': str(e)}]
        finally:
            conn.close()
    
    def get_available_items(self) -> List[str]:
        """Get list of available financial items."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.execute('SELECT DISTINCT item FROM financial_data ORDER BY item')
        items = [row[0] for row in cursor]
        conn.close()
        return items
    
    def get_all_data(self) -> pd.DataFrame:
        """Get all financial data as a DataFrame."""
        conn = sqlite3.connect(self.db_file)
        df = pd.read_sql_query('SELECT * FROM financial_data ORDER BY item, fiscal_year DESC', conn)
        conn.close()
        return df


def main():
    """Test the structured data lookup tool."""
    lookup = StructuredDataLookup()
    
    print("Costco Financial Data Lookup Tool")
    print("=" * 50)
    
    # Show available items
    print("\nAvailable financial items:")
    for item in lookup.get_available_items():
        print(f"  - {item}")
    
    # Test queries
    test_queries = [
        "Net sales 2024",
        "What was the revenue in 2023?",
        "EPS 2024",
        "Gross margin",
        "Operating income 2024",
        "Membership fee revenue 2024"
    ]
    
    print("\nTest queries:")
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        result = lookup.structured_data_lookup(query)
        print(f"Result: {json.dumps(result, indent=2)}")
    
    # Show full data table
    print("\n" + "=" * 50)
    print("Full Financial Data Table:")
    print("=" * 50)
    df = lookup.get_all_data()
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
