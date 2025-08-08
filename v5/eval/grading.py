import json
from decimal import Decimal
from typing import List, Dict, Any


def load_results(path: str) -> List[Dict[str, Any]]:
    with open(path, "r") as f:
        return json.load(f)


def grade(results: List[Dict[str, Any]], gold_path: str) -> Dict[str, Any]:
    with open(gold_path, "r") as f:
        gold = {str(x["id"]): x for x in json.load(f)}

    total = 0
    correct = 0
    calc_total = 0
    calc_correct = 0

    per_item = []

    for r in results:
        qid = str(r.get("id"))
        g = gold.get(qid)
        if not g:
            continue
        total += 1
        r_final = r.get("final_answer", {})
        g_final = g.get("final_answer", {})

        r_type = r_final.get("type")
        g_type = g_final.get("type")

        ok = False
        if r_type == g_type == "text":
            ok = (str(r_final.get("value", "")).strip().lower() == str(g_final.get("value", "")).strip().lower())
        else:
            try:
                rv = Decimal(str(r_final.get("value", "0")))
                gv = Decimal(str(g_final.get("value", "0")))
                tol = Decimal("0.01")
                ok = abs(rv - gv) <= tol
                calc_total += 1
                if ok:
                    calc_correct += 1
            except Exception:
                ok = False

        if ok:
            correct += 1

        per_item.append({
            "id": qid,
            "pred": r_final,
            "gold": g_final,
            "ok": ok
        })

    overall = {
        "total": total,
        "correct": correct,
        "accuracy": (correct / total) if total else 0.0,
        "calc_total": calc_total,
        "calc_correct": calc_correct,
        "calc_accuracy": (calc_correct / calc_total) if calc_total else 0.0,
        "items": per_item
    }

    return overall

