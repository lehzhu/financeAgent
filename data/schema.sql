-- SQLite schema for expanded Costco financial data

DROP TABLE IF EXISTS financial_data;
CREATE TABLE IF NOT EXISTS financial_data (
    item TEXT NOT NULL,
    fiscal_year INTEGER NOT NULL,
    value REAL NOT NULL,
    unit TEXT NOT NULL,
    source TEXT DEFAULT 'ingest',
    note TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_item ON financial_data(item);
CREATE INDEX IF NOT EXISTS idx_year ON financial_data(fiscal_year);

-- Canonical alias mapping for query matching
DROP TABLE IF EXISTS aliases;
CREATE TABLE IF NOT EXISTS aliases (
    alias TEXT PRIMARY KEY,
    item TEXT NOT NULL
);

-- View that scales values to actual_value (millions -> absolute)
DROP VIEW IF EXISTS financial_summary;
CREATE VIEW IF NOT EXISTS financial_summary AS
SELECT 
    item,
    fiscal_year,
    value,
    unit,
    CASE 
        WHEN unit = 'millions' THEN value * 1000000
        ELSE value
    END AS actual_value,
    source,
    note
FROM financial_data
ORDER BY item, fiscal_year DESC;

