import os
import re
import sqlite3
from typing import List, Tuple, Dict

DATA_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(DATA_DIR, 'costco_financial_data.db')
SCHEMA_PATH = os.path.join(DATA_DIR, 'schema.sql')

# Canonical items and regex patterns to extract values from text sources
EXTRACT_PATTERNS: Dict[str, List[Tuple[str, str]]] = {
    # item -> list of (regex with capture, unit)
    'Total Revenue': [
        (r"Total\s+Revenue\s*\(\$?([\d,]+)\s*million\)", 'millions'),
        (r"Net\s+Sales\s*\(\$?([\d,]+)\s*million\)", 'millions'),
        (r"Net\s+Sales[^\d]*\$?([\d,]+)\s*million", 'millions'),
    ],
    'Gross Profit': [
        (r"Gross\s+Profit\s*\(\$?([\d,]+)\s*million\)", 'millions'),
    ],
    'Operating Income': [
        (r"Operating\s+Income\s*\(\$?([\d,]+)\s*million\)", 'millions'),
        (r"Operating\s+Profit\s*\(\$?([\d,]+)\s*million\)", 'millions'),
    ],
    'Net Income': [
        (r"Net\s+Income\s*\(\$?([\d,]+)\s*million\)", 'millions'),
    ],
    'Earnings Per Share': [
        (r"Diluted\s+EPS\s*\$?([\d\.]+)", 'dollars'),
        (r"Earnings\s+per\s+share\s*\$?([\d\.]+)", 'dollars'),
    ],
    'Total Assets': [
        (r"Total\s+Assets\s*\(\$?([\d,]+)\s*million\)", 'millions'),
    ],
    'Total Liabilities': [
        (r"Total\s+Liabilities\s*\(\$?([\d,]+)\s*million\)", 'millions'),
    ],
    'Stockholders Equity': [
        (r"Stockholders'?\s+Equity\s*\(\$?([\d,]+)\s*million\)", 'millions'),
    ],
    'Cash and Cash Equivalents': [
        (r"Cash\s+and\s+Cash\s+Equivalents\s*\(\$?([\d,]+)\s*million\)", 'millions'),
    ],
    'Merchandise Inventories': [
        (r"Merchandise\s+Inventories\s*\(\$?([\d,]+)\s*million\)", 'millions'),
    ],
    'Membership Fee Revenue': [
        (r"Membership\s+Fee\s+Revenue\s*\(\$?([\d,]+)\s*million\)", 'millions'),
    ],
    'Capital Expenditures': [
        (r"Capital\s+Expenditures\s*\(\$?([\d,]+)\s*million\)", 'millions'),
    ],
    'Operating Cash Flow': [
        (r"Net\s+cash\s+provided\s+by\s+operating\s+activities[^\d]*\$?([\d,]+)\s*million", 'millions'),
    ],
    'Interest Expense': [
        (r"Interest\s+expense[^\d]*\$?([\d,]+)\s*million", 'millions'),
    ],
    'Total Debt': [
        (r"Total\s+debt[^\d]*\$?([\d,]+)\s*million", 'millions'),
        (r"Long[-\s]*term\s+debt[^\d]*\$?([\d,]+)\s*million", 'millions'),
    ],
    'Operating Lease Liabilities': [
        (r"Operating\s+lease\s+liabilities[^\d]*\$?([\d,]+)\s*million", 'millions'),
    ],
    'Goodwill': [
        (r"Goodwill[^\d]*\$?([\d,]+)\s*million", 'millions'),
    ],
    'Number of Warehouses': [
        (r"(?:As\s+of\s+[A-Za-z]+\s+\d{1,2},\s+20\d{2}.*?we\s+operated\s+)([\d]{2,4})\s+warehouses", 'count'),
        (r"we\s+operated\s+([\d]{2,4})\s+warehouses", 'count')
    ],
}

ALIASES = {
    # alias -> canonical item
    'revenue': 'Total Revenue',
    'net sales': 'Total Revenue',
    'sales': 'Total Revenue',
    'gross margin': 'Gross Profit',
    'operating profit': 'Operating Income',
    'operating income': 'Operating Income',
    'net income': 'Net Income',
    'eps': 'Earnings Per Share',
    'earnings per share': 'Earnings Per Share',
    'cash': 'Cash and Cash Equivalents',
    'inventory': 'Merchandise Inventories',
    'membership revenue': 'Membership Fee Revenue',
}

TEXT_SOURCES = [
    os.path.join(DATA_DIR, 'costco_10k_full.txt'),
    os.path.join(DATA_DIR, 'costco_10k_summary.txt'),
]


def _load_schema(conn: sqlite3.Connection):
    with open(SCHEMA_PATH, 'r') as f:
        conn.executescript(f.read())


def _insert_aliases(conn: sqlite3.Connection):
    rows = [(alias, item) for alias, item in ALIASES.items()]
    conn.executemany("INSERT OR REPLACE INTO aliases(alias, item) VALUES(?,?)", rows)


def _insert_row(conn: sqlite3.Connection, item: str, year: int, value: float, unit: str, source: str, note: str):
    conn.execute(
        "INSERT INTO financial_data(item, fiscal_year, value, unit, source, note) VALUES(?,?,?,?,?,?)",
        (item, year, value, unit, source, note)
    )


def _extract_from_text(conn: sqlite3.Connection, text: str, year: int, source: str):
    for item, patterns in EXTRACT_PATTERNS.items():
        for regex, unit in patterns:
            for m in re.finditer(regex, text, flags=re.IGNORECASE):
                val_str = m.group(1).replace(',', '')
                try:
                    value = float(val_str)
                except Exception:
                    continue
                _insert_row(conn, item, year, value, unit, source, f"regex:{regex[:40]}")


def _compute_derived(conn: sqlite3.Connection):
    cur = conn.cursor()
    # Derive margins if inputs exist per year
    cur.execute("SELECT DISTINCT fiscal_year FROM financial_data")
    years = [r[0] for r in cur.fetchall()]
    for y in years:
        # Gross Margin = Gross Profit / Total Revenue * 100
        cur.execute("SELECT value, unit FROM financial_data WHERE item='Gross Profit' AND fiscal_year=?", (y,))
        gp = cur.fetchone()
        cur.execute("SELECT value, unit FROM financial_data WHERE item='Total Revenue' AND fiscal_year=?", (y,))
        rev = cur.fetchone()
        if gp and rev and gp[1] == rev[1] and rev[0] != 0:
            margin = (gp[0] / rev[0]) * 100.0
            _insert_row(conn, 'Gross Margin', y, margin, 'percent', 'derived', 'gross_profit/revenue')
        # Operating Margin = Operating Income / Total Revenue * 100
        cur.execute("SELECT value, unit FROM financial_data WHERE item='Operating Income' AND fiscal_year=?", (y,))
        op = cur.fetchone()
        if op and rev and op[1] == rev[1] and rev[0] != 0:
            om = (op[0] / rev[0]) * 100.0
            _insert_row(conn, 'Operating Margin', y, om, 'percent', 'derived', 'operating_income/revenue')


def ingest():
    # Build DB fresh
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    _load_schema(conn)

    # Try to detect year context from filenames or content
    years = [2024, 2023, 2022]
    for path in TEXT_SOURCES:
        if not os.path.exists(path):
            continue
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            txt = f.read()
        counts = {y: len(re.findall(str(y), txt)) for y in years}
        assigned = max(counts, key=counts.get) if counts else 2024
        _extract_from_text(conn, txt, assigned, os.path.basename(path))

    _compute_derived(conn)
    _insert_aliases(conn)
    conn.commit()

    # Quick density report
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM financial_data")
    total = cur.fetchone()[0]
    print(f"Ingested rows: {total}")
    cur.execute("SELECT item, COUNT(*) c FROM financial_data GROUP BY item ORDER BY c DESC LIMIT 10")
    print("Top items:")
    for row in cur.fetchall():
        print("  ", row)

    conn.close()

if __name__ == '__main__':
    ingest()

