#!/usr/bin/env python3
"""
Preprocess 10-K data to separate structured XBRL data from narrative text.
Creates a SQLite database for structured data and saves narrative text separately.
"""

import re
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict, Optional

class TenKPreprocessor:
    def __init__(self, input_file: str, output_dir: str = None):
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir or self.input_file.parent)
        self.output_dir.mkdir(exist_ok=True)
        
        # Output files
        self.db_file = self.output_dir / "costco_structured_data.db"
        self.narrative_file = self.output_dir / "costco_narrative.txt"
        self.structured_csv = self.output_dir / "costco_structured_data.csv"
        
    def parse_10k(self):
        """Parse 10-K file and separate structured data from narrative text."""
        with open(self.input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find where narrative text begins (usually after "Table of Contents")
        narrative_start = None
        for i, line in enumerate(lines):
            if "Table of Contents" in line:
                narrative_start = i
                break
        
        if narrative_start is None:
            # If no clear separator, use a heuristic
            narrative_start = self._find_narrative_start_heuristic(lines)
        
        # Split data
        structured_lines = lines[:narrative_start]
        narrative_lines = lines[narrative_start:]
        
        # Process structured data
        structured_data = self._extract_structured_data(structured_lines)
        
        # Save narrative text
        self._save_narrative_text(narrative_lines)
        
        # Save structured data to SQLite and CSV
        self._save_structured_data(structured_data)
        
        return structured_data, len(narrative_lines)
    
    def _find_narrative_start_heuristic(self, lines: List[str]) -> int:
        """Find where narrative text likely begins using heuristics."""
        # Look for common 10-K section headers
        markers = ["UNITED STATES", "SECURITIES AND EXCHANGE COMMISSION", 
                  "FORM 10-K", "ANNUAL REPORT"]
        
        for i, line in enumerate(lines):
            if any(marker in line.upper() for marker in markers):
                return i
        
        # Default to 25% through the file if no markers found
        return len(lines) // 4
    
    def _extract_structured_data(self, lines: List[str]) -> List[Dict]:
        """Extract structured XBRL-like data from lines."""
        data = []
        
        # Pattern for detecting potential data tuples
        # Looking for patterns like entity IDs, dates, member references, values
        entity_pattern = r'^\d{10}$'  # CIK number
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'  # ISO date
        member_pattern = r'^[\w-]+:[\w-]+Member$'  # XBRL member reference
        value_pattern = r'^[\d,.-]+$'  # Numeric values
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Try to build a data record
            record = {}
            
            # Check if this looks like an entity ID
            if re.match(entity_pattern, line):
                record['entity_id'] = line
                
                # Look ahead for associated data
                j = i + 1
                while j < len(lines) and j < i + 10:  # Look ahead up to 10 lines
                    next_line = lines[j].strip()
                    
                    if not next_line:
                        j += 1
                        continue
                    
                    # Check for member reference
                    if re.match(member_pattern, next_line):
                        record['member'] = next_line
                        j += 1
                        continue
                    
                    # Check for date
                    if re.match(date_pattern, next_line):
                        if 'start_date' not in record:
                            record['start_date'] = next_line
                        elif 'end_date' not in record:
                            record['end_date'] = next_line
                        else:
                            record['date'] = next_line
                        j += 1
                        continue
                    
                    # Check for value
                    if re.match(value_pattern, next_line):
                        # Clean numeric value
                        clean_value = next_line.replace(',', '')
                        try:
                            if '.' in clean_value:
                                record['value'] = float(clean_value)
                            else:
                                record['value'] = int(clean_value)
                        except ValueError:
                            record['value'] = next_line
                        j += 1
                        break
                    
                    # If we hit another entity ID or unrecognized pattern, stop
                    if re.match(entity_pattern, next_line):
                        break
                    
                    j += 1
                
                if len(record) > 1:  # Only add if we found associated data
                    data.append(record)
                    i = j  # Skip processed lines
                else:
                    i += 1
            else:
                # Try to parse standalone values with context
                if ':' in line and not line.startswith('http'):
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        data.append({
                            'category': parts[0].strip(),
                            'item': parts[1].strip()
                        })
                i += 1
        
        return data
    
    def _save_narrative_text(self, lines: List[str]):
        """Save narrative text to file."""
        with open(self.narrative_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"Narrative text saved to: {self.narrative_file}")
    
    def _save_structured_data(self, data: List[Dict]):
        """Save structured data to SQLite database and CSV."""
        if not data:
            print("No structured data found to save.")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Save to CSV
        df.to_csv(self.structured_csv, index=False)
        print(f"Structured data saved to CSV: {self.structured_csv}")
        
        # Save to SQLite
        conn = sqlite3.connect(self.db_file)
        
        # Create main data table
        df.to_sql('structured_data', conn, if_exists='replace', index=True)
        
        # Create indexes for common queries
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_entity_id 
            ON structured_data(entity_id)
        ''')
        
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_member 
            ON structured_data(member)
        ''')
        
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_dates 
            ON structured_data(start_date, end_date)
        ''')
        
        # Create a summary view for easier querying
        conn.execute('''
            CREATE VIEW IF NOT EXISTS data_summary AS
            SELECT 
                entity_id,
                member,
                start_date,
                end_date,
                value,
                CASE 
                    WHEN member LIKE '%Revenue%' THEN 'Revenue'
                    WHEN member LIKE '%Sales%' THEN 'Sales'
                    WHEN member LIKE '%Income%' THEN 'Income'
                    WHEN member LIKE '%Asset%' THEN 'Asset'
                    WHEN member LIKE '%Liability%' THEN 'Liability'
                    WHEN member LIKE '%Equity%' THEN 'Equity'
                    ELSE 'Other'
                END as category
            FROM structured_data
            WHERE value IS NOT NULL
        ''')
        
        conn.commit()
        conn.close()
        
        print(f"Structured data saved to SQLite: {self.db_file}")
        print(f"Total records: {len(df)}")
        print(f"Columns: {', '.join(df.columns)}")
        
        # Display sample data
        print("\nSample structured data:")
        print(df.head(10))


def main():
    """Run the preprocessing."""
    preprocessor = TenKPreprocessor(
        input_file="/Users/zhu/documents/financeAgent/data/costco_10k_full.txt"
    )
    
    print("Starting 10-K preprocessing...")
    structured_data, narrative_lines = preprocessor.parse_10k()
    
    print(f"\nPreprocessing complete!")
    print(f"Structured data records: {len(structured_data)}")
    print(f"Narrative text lines: {narrative_lines}")


if __name__ == "__main__":
    main()
