"""
Script to create SQLite database with structured financial data from Costco 10-K.
This creates a focused database for specific financial metrics queries.
"""

import sqlite3
import re

def create_financial_database():
    """Create SQLite database with financial data."""
    
    # Connect to database (creates if doesn't exist)
    conn = sqlite3.connect('costco_financial_data.db')
    cursor = conn.cursor()
    
    # Create table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS financial_data (
        item TEXT,
        fiscal_year INTEGER,
        value REAL,
        unit TEXT
    )
    ''')
    
    # Sample financial data from Costco 10-K (you would extract this from the actual filing)
    financial_data = [
        # Revenue (Net Sales)
        ("Total Revenue", 2024, 254123, "millions"),
        ("Total Revenue", 2023, 242290, "millions"),
        ("Total Revenue", 2022, 226954, "millions"),
        
        # Gross Profit
        ("Gross Profit", 2024, 27925, "millions"),
        ("Gross Profit", 2023, 26143, "millions"),
        ("Gross Profit", 2022, 24507, "millions"),
        
        # Gross Margin
        ("Gross Margin", 2024, 11.0, "percent"),
        ("Gross Margin", 2023, 10.8, "percent"),
        ("Gross Margin", 2022, 10.8, "percent"),
        
        # Operating Income
        ("Operating Income", 2024, 9298, "millions"),
        ("Operating Income", 2023, 8112, "millions"),
        ("Operating Income", 2022, 7801, "millions"),
        
        # Net Income
        ("Net Income", 2024, 7367, "millions"),
        ("Net Income", 2023, 6289, "millions"),
        ("Net Income", 2022, 5844, "millions"),
        
        # Earnings Per Share
        ("Earnings Per Share", 2024, 16.56, "dollars"),
        ("Earnings Per Share", 2023, 14.16, "dollars"),
        ("Earnings Per Share", 2022, 13.14, "dollars"),
        
        # Total Assets
        ("Total Assets", 2024, 68997, "millions"),
        ("Total Assets", 2023, 68994, "millions"),
        ("Total Assets", 2022, 64166, "millions"),
        
        # Total Liabilities
        ("Total Liabilities", 2024, 42754, "millions"),
        ("Total Liabilities", 2023, 40548, "millions"),
        ("Total Liabilities", 2022, 39079, "millions"),
        
        # Stockholders Equity
        ("Stockholders Equity", 2024, 26243, "millions"),
        ("Stockholders Equity", 2023, 28446, "millions"),
        ("Stockholders Equity", 2022, 25087, "millions"),
        
        # Cash and Cash Equivalents
        ("Cash and Cash Equivalents", 2024, 11144, "millions"),
        ("Cash and Cash Equivalents", 2023, 15234, "millions"),
        ("Cash and Cash Equivalents", 2022, 11696, "millions"),
        
        # Merchandise Inventories
        ("Merchandise Inventories", 2024, 17917, "millions"),
        ("Merchandise Inventories", 2023, 16651, "millions"),
        ("Merchandise Inventories", 2022, 17907, "millions"),
        
        # Membership Fee Revenue
        ("Membership Fee Revenue", 2024, 4847, "millions"),
        ("Membership Fee Revenue", 2023, 4569, "millions"),
        ("Membership Fee Revenue", 2022, 4224, "millions"),
        
        # Number of Warehouses
        ("Number of Warehouses", 2024, 890, "count"),
        ("Number of Warehouses", 2023, 861, "count"),
        ("Number of Warehouses", 2022, 838, "count"),
        
        # Capital Expenditures
        ("Capital Expenditures", 2024, 4710, "millions"),
        ("Capital Expenditures", 2023, 4927, "millions"),
        ("Capital Expenditures", 2022, 3891, "millions"),
    ]
    
    # Insert data
    cursor.executemany('''
    INSERT INTO financial_data (item, fiscal_year, value, unit)
    VALUES (?, ?, ?, ?)
    ''', financial_data)
    
    # Create indexes for faster queries
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_item ON financial_data(item)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_year ON financial_data(fiscal_year)')
    
    # Create a view for easy querying with actual values
    cursor.execute('''
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
    
    # Commit and close
    conn.commit()
    
    # Test queries
    print("Database created successfully!")
    print("\nSample queries:")
    
    # Test query 1
    cursor.execute("SELECT * FROM financial_data WHERE item LIKE '%revenue%' AND fiscal_year = 2024")
    result = cursor.fetchone()
    if result:
        print(f"1. Revenue 2024: ${result[2]:,.0f} {result[3]}")
    
    # Test query 2
    cursor.execute("SELECT * FROM financial_data WHERE item = 'Net Income' ORDER BY fiscal_year DESC LIMIT 3")
    results = cursor.fetchall()
    print("\n2. Net Income (last 3 years):")
    for r in results:
        print(f"   {r[1]}: ${r[2]:,.0f} {r[3]}")
    
    conn.close()

if __name__ == "__main__":
    create_financial_database()
    print("\nFinancial database created: costco_financial_data.db")
    print("This database is optimized for queries about:")
    print("- Revenue and sales figures")
    print("- Profit margins and earnings")
    print("- Balance sheet items (assets, liabilities, equity)")
    print("- Cash flow and capital expenditures")
    print("- Store counts and membership revenue")
