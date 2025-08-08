import json
import argparse
from typing import Dict, Any

from agent.orchestrator import Orchestrator, OrchestratorConfig


def load_dataset(path: str):
    with open(path, "r") as f:
        return json.load(f)


def evaluate(dataset_path: str, limit: int = 0):
    cfg = OrchestratorConfig(model="gpt-4o-mini")
    orch = Orchestrator(cfg)

    data = load_dataset(dataset_path)
    if limit:
        data = data[:limit]

    results = []
    for item in data:
        res = orch.answer(item)
        results.append(res)

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--out", default="eval/results.json")
    args = parser.parse_args()

    results = evaluate(args.dataset, args.limit)

    # Ensure out dir exists
    import os
    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    with open(args.out, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Wrote {len(results)} results to {args.out}")


if __name__ == "__main__":
    main()

