#!/usr/bin/env python3
"""
Enhanced parser for XBRL data from 10-K filings.
Extracts financial data into a structured format.
"""

import re
import sqlite3
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json

class XBRLParser:
    def __init__(self, input_file: str):
        self.input_file = Path(input_file)
        self.output_dir = self.input_file.parent
        
        # Output files
        self.db_file = self.output_dir / "costco_financial_data.db"
        self.narrative_file = self.output_dir / "costco_narrative.txt"
        self.financial_csv = self.output_dir / "costco_financial_data.csv"
        
        # Known financial items mapping
        self.financial_items = {
            # Revenue items
            'us-gaap:SalesRevenueNet': 'Net Sales',
            'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax': 'Revenue',
            'us-gaap:Revenues': 'Total Revenue',
            
            # Cost items
            'us-gaap:CostOfGoodsAndServicesSold': 'Cost of Goods Sold',
            'us-gaap:CostOfRevenue': 'Cost of Revenue',
            
            # Income items
            'us-gaap:NetIncomeLoss': 'Net Income',
            'us-gaap:GrossProfit': 'Gross Profit',
            'us-gaap:OperatingIncomeLoss': 'Operating Income',
            'us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest': 'Income Before Tax',
            
            # Asset items
            'us-gaap:Assets': 'Total Assets',
            'us-gaap:AssetsCurrent': 'Current Assets',
            'us-gaap:CashAndCashEquivalentsAtCarryingValue': 'Cash and Cash Equivalents',
            'us-gaap:InventoryNet': 'Inventory',
            
            # Liability items
            'us-gaap:Liabilities': 'Total Liabilities',
            'us-gaap:LiabilitiesCurrent': 'Current Liabilities',
            'us-gaap:LongTermDebt': 'Long Term Debt',
            
            # Equity items
            'us-gaap:StockholdersEquity': 'Stockholders Equity',
            'us-gaap:CommonStockSharesOutstanding': 'Common Stock Outstanding',
            
            # Per share items
            'us-gaap:EarningsPerShareBasic': 'EPS Basic',
            'us-gaap:EarningsPerShareDiluted': 'EPS Diluted',
        }
        
    def parse_file(self) -> Tuple[pd.DataFrame, int]:
        """Parse the 10-K file and extract financial data."""
        with open(self.input_file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.splitlines()
        
        # Find where narrative begins
        narrative_start = self._find_narrative_start(lines)
        
        # Split content
        xbrl_content = '\n'.join(lines[:narrative_start])
        narrative_content = '\n'.join(lines[narrative_start:])
        
        # Save narrative text
        with open(self.narrative_file, 'w', encoding='utf-8') as f:
            f.write(narrative_content)
        print(f"Narrative text saved to: {self.narrative_file}")
        
        # Extract financial data
        financial_data = self._extract_financial_data(xbrl_content)
        
        # Create DataFrame
        df = pd.DataFrame(financial_data)
        
        # Save to files
        self._save_financial_data(df)
        
        return df, len(lines[narrative_start:])
    
    def _find_narrative_start(self, lines: List[str]) -> int:
        """Find where narrative text begins."""
        for i, line in enumerate(lines):
            if "Table of Contents" in line or "UNITED STATES" in line:
                return i
        return len(lines) // 4  # Fallback
    
    def _extract_financial_data(self, content: str) -> List[Dict]:
        """Extract financial data from XBRL content."""
        data = []
        
        # Split content into potential data blocks
        blocks = content.split('0000909832')  # Using CIK as delimiter
        
        for block in blocks[1:]:  # Skip first empty block
            lines = block.strip().split('\n')
            if len(lines) < 2:
                continue
            
            record = {'entity_id': '0000909832'}
            
            # Parse the block
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if not line:
                    i += 1
                    continue
                
                # Check for XBRL member
                if ':' in line and 'Member' in line:
                    record['xbrl_tag'] = line
                    # Map to friendly name if available
                    tag_base = line.split('Member')[0]
                    record['item'] = self.financial_items.get(tag_base, line)
                    i += 1
                    continue
                
                # Check for date
                if re.match(r'^\d{4}-\d{2}-\d{2}$', line):
                    if 'period_start' not in record:
                        record['period_start'] = line
                    else:
                        record['period_end'] = line
                    i += 1
                    continue
                
                # Check for numeric value
                if re.match(r'^-?[\d,]+\.?\d*$', line):
                    value_str = line.replace(',', '')
                    try:
                        record['value'] = float(value_str)
                    except:
                        record['value'] = value_str
                    i += 1
                    break
                
                i += 1
            
            # Only add records with meaningful data
            if 'value' in record and ('xbrl_tag' in record or 'item' in record):
                # Determine fiscal year from dates
                if 'period_end' in record:
                    year = record['period_end'][:4]
                    record['fiscal_year'] = int(year)
                elif 'period_start' in record:
                    year = record['period_start'][:4]
                    record['fiscal_year'] = int(year)
                
                data.append(record)
        
        return data
    
    def _save_financial_data(self, df: pd.DataFrame):
        """Save financial data to SQLite and CSV."""
        if df.empty:
            print("No financial data extracted.")
            return
        
        # Save to CSV
        df.to_csv(self.financial_csv, index=False)
        print(f"Financial data saved to CSV: {self.financial_csv}")
        
        # Save to SQLite
        conn = sqlite3.connect(self.db_file)
        
        # Create main table
        df.to_sql('financial_data', conn, if_exists='replace', index=False)
        
        # Create indexes
        conn.execute('CREATE INDEX IF NOT EXISTS idx_item ON financial_data(item)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_year ON financial_data(fiscal_year)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_xbrl ON financial_data(xbrl_tag)')
        
        # Create aggregated view for common queries
        conn.execute('''
            CREATE VIEW IF NOT EXISTS financial_summary AS
            SELECT 
                item,
                fiscal_year,
                MAX(value) as value,
                period_start,
                period_end
            FROM financial_data
            WHERE item IS NOT NULL
            GROUP BY item, fiscal_year
            ORDER BY item, fiscal_year DESC
        ''')
        
        conn.commit()
        conn.close()
        
        print(f"Financial data saved to SQLite: {self.db_file}")
        print(f"Total records: {len(df)}")
        
        # Show sample
        print("\nSample financial data:")
        if 'item' in df.columns:
            sample = df[df['item'].notna()].head(10)
            print(sample[['item', 'fiscal_year', 'value']])


class StructuredDataLookup:
    """Tool for querying structured financial data without using LLM."""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path(__file__).parent / "costco_financial_data.db"
        self.db_path = db_path
        
        # Common query patterns
        self.query_patterns = {
            'net sales': ['Net Sales', 'Revenue', 'Total Revenue'],
            'revenue': ['Revenue', 'Net Sales', 'Total Revenue'],
            'income': ['Net Income', 'Operating Income', 'Income Before Tax'],
            'assets': ['Total Assets', 'Current Assets'],
            'liabilities': ['Total Liabilities', 'Current Liabilities'],
            'cost': ['Cost of Goods Sold', 'Cost of Revenue'],
            'eps': ['EPS Basic', 'EPS Diluted'],
            'cash': ['Cash and Cash Equivalents'],
        }
    
    def lookup(self, query: str) -> Dict:
        """
        Perform structured lookup of financial data.
        
        Args:
            query: Natural language query like "Net sales 2024" or "Total assets"
            
        Returns:
            Dictionary with results
        """
        query_lower = query.lower()
        
        # Extract year if present
        year_match = re.search(r'20\d{2}', query)
        year = int(year_match.group()) if year_match else None
        
        # Determine what to look for
        items_to_search = []
        for pattern, items in self.query_patterns.items():
            if pattern in query_lower:
                items_to_search.extend(items)
        
        # If no pattern matched, try direct search
        if not items_to_search:
            # Try to extract capitalized terms
            words = query.split()
            potential_item = ' '.join([w for w in words if w[0].isupper() or w.isdigit()])
            if potential_item:
                items_to_search = [potential_item]
        
        # Query database
        results = self._query_database(items_to_search, year)
        
        return {
            'query': query,
            'results': results,
            'items_searched': items_to_search,
            'year_filter': year
        }
    
    def _query_database(self, items: List[str], year: Optional[int]) -> List[Dict]:
        """Query the SQLite database."""
        if not Path(self.db_path).exists():
            return [{'error': f'Database not found at {self.db_path}'}]
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        results = []
        
        try:
            # Build query
            if year:
                query = '''
                    SELECT item, fiscal_year, value, period_start, period_end
                    FROM financial_summary
                    WHERE item IN ({}) AND fiscal_year = ?
                    ORDER BY item, fiscal_year DESC
                '''.format(','.join(['?'] * len(items)))
                params = items + [year]
            else:
                query = '''
                    SELECT item, fiscal_year, value, period_start, period_end
                    FROM financial_summary
                    WHERE item IN ({})
                    ORDER BY item, fiscal_year DESC
                    LIMIT 10
                '''.format(','.join(['?'] * len(items)))
                params = items
            
            cursor = conn.execute(query, params)
            
            for row in cursor:
                results.append({
                    'item': row['item'],
                    'fiscal_year': row['fiscal_year'],
                    'value': row['value'],
                    'period_start': row['period_start'],
                    'period_end': row['period_end']
                })
            
        except Exception as e:
            results.append({'error': str(e)})
        finally:
            conn.close()
        
        return results
    
    def get_available_items(self) -> List[str]:
        """Get list of available financial items in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute('SELECT DISTINCT item FROM financial_summary WHERE item IS NOT NULL ORDER BY item')
        items = [row[0] for row in cursor]
        conn.close()
        return items


def main():
    """Run the enhanced parser."""
    parser = XBRLParser("/Users/zhu/documents/financeAgent/data/costco_10k_full.txt")
    df, narrative_lines = parser.parse_file()
    
    print(f"\nParsing complete!")
    print(f"Financial data records: {len(df)}")
    print(f"Narrative lines: {narrative_lines}")
    
    # Test the lookup tool
    print("\n" + "="*50)
    print("Testing Structured Data Lookup Tool")
    print("="*50)
    
    lookup = StructuredDataLookup()
    
    # Test queries
    test_queries = [
        "Net sales 2024",
        "Total assets",
        "Net income 2023",
        "Revenue 2024"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = lookup.lookup(query)
        print(f"Results: {json.dumps(results, indent=2)}")


if __name__ == "__main__":
    main()
