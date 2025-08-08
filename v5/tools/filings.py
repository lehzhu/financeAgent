from typing import Dict, Any

# In v5 scope: use dataset-provided links and cached tables only. No live crawl.

def fetch_filing_table(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Stub implementation that tries to load a cached CSV or JSON under data/edgar_cache.
    Input schema per PRD. Output returns a units hint and a flattened table list.
    """
    import os, json, csv

    company = payload.get("company", "").replace(" ", "_")
    table_hint = payload.get("table_hint", "table").replace(" ", "_")
    base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "edgar_cache", company)

    # prefer JSON cache
    json_path = os.path.join(base_dir, f"{table_hint}.json")
    csv_path = os.path.join(base_dir, f"{table_hint}.csv")

    table = []
    units_hint = "USD"
    raw_text = ""

    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            data = json.load(f)
            table = data.get("table", [])
            units_hint = data.get("units_hint", "USD")
            raw_text = data.get("raw_text", "")
    elif os.path.exists(csv_path):
        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # expect columns: row, col, value
                table.append({"row": row.get("row", ""), "col": row.get("col", ""), "value": row.get("value", "")})
        # leave default units_hint
    else:
        # not found; return empty stub
        pass

    return {"units_hint": units_hint, "table": table, "raw_text": raw_text}

