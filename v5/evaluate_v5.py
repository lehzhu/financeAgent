from __future__ import annotations
import os
import json
from typing import Optional

from modal import Image, Secret, App, Volume

# Build image with dependencies
image = (
    Image.debian_slim()
    .pip_install_from_requirements("requirements.txt")
    .add_local_dir(".", remote_path="/root/app")
)

# Modal volume to persist eval artifacts (optional)
results_volume = Volume.from_name("financeagent-v5-results", create_if_missing=True)

app = App("financeagent-v5-eval", image=image)

DATASET_ENV = "FINANCEQA_DATASET_URL"  # optional: URL to dataset json


def _load_local_dataset(path: str):
    with open(path, "r") as f:
        return json.load(f)


def _maybe_fetch_dataset(url: Optional[str]):
    if not url:
        return None
    import requests
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()


def _load_hf_dataset(name: str, split: Optional[str] = None):
    """Load a dataset from Hugging Face and map to our expected list of items.
    Attempts to pick a default split if not provided: prefer 'test', then 'validation', then 'train'.
    """
    from datasets import load_dataset, DatasetDict
    ds = load_dataset(name)
    if isinstance(ds, DatasetDict):
        # DatasetDict with splits
        split_order = [split] if split else ["test", "validation", "train"]
        chosen = None
        for s in split_order:
            if s and s in ds:
                chosen = ds[s]
                break
        if chosen is None:
            # take first available split deterministically
            first_key = sorted(list(ds.keys()))[0]
            chosen = ds[first_key]
        ds_iter = chosen
    else:
        # Single-split dataset returned
        ds_iter = ds

    items = []
    for idx, row in enumerate(ds_iter):
        q = row.get("question") or row.get("prompt") or row.get("Question") or ""
        ctx = row.get("context") if isinstance(row.get("context"), dict) else None
        item_id = str(row.get("id") or idx)
        # Optionally include gold answer if present
        gold = row.get("answer") or row.get("final_answer")
        entry = {"id": item_id, "question": q}
        if ctx:
            entry["context"] = ctx
        if gold is not None:
            entry["final_answer"] = gold
        items.append(entry)
    return items


@app.function(
    cpu=1.0,
    memory= "2Gi",
    volumes={"/root/results": results_volume},
    timeout=60*30,
)
def run_eval(dataset_path: str = "data/financeqa.json", limit: int = 0, out_path: str = "/root/results/results.json"):
    """Run the v5 evaluation inside Modal and persist results to a volume path.
    dataset_path: local path within repo image, or a URL if startswith http(s)
    limit: optional size cap
    out_path: path under /root/results to write JSON
    """
    import os
    import json

    # Resolve dataset: prefer explicit path or env URL, else try Hugging Face
    dataset = None
    if dataset_path.startswith("http://") or dataset_path.startswith("https://"):
        dataset = _maybe_fetch_dataset(dataset_path)
    elif os.path.exists(dataset_path):
        dataset = _load_local_dataset(dataset_path)
    elif dataset_path.startswith("hf:"):
        name = dataset_path.split(":", 1)[1]
        dataset = _load_hf_dataset(name, os.getenv("FINANCEQA_SPLIT"))
    else:
        # Try interpreting the value as an HF dataset name (e.g., "AfterQuery/FinanceQA")
        try:
            dataset = _load_hf_dataset(dataset_path, os.getenv("FINANCEQA_SPLIT"))
        except Exception:
            if os.getenv(DATASET_ENV):
                dataset = _maybe_fetch_dataset(os.getenv(DATASET_ENV))
            else:
                raise FileNotFoundError(f"Dataset not found or loadable: {dataset_path}")

    if limit:
        dataset = dataset[:limit]

    import sys
    sys.path.insert(0, "/root/app")
    from agent.orchestrator import Orchestrator, OrchestratorConfig

    orch = Orchestrator(OrchestratorConfig(model="gpt-4o-mini"))

    results = []
    for item in dataset:
        results.append(orch.answer(item))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    return {"count": len(results), "out": out_path}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="data/financeqa.json")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--out", default="/root/results/results.json")
    args = parser.parse_args()

    with app.run():
        out = run_eval.remote(args.dataset, args.limit, args.out)
        print(out)

