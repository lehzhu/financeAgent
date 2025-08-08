#!/usr/bin/env python3
import json
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="eval/results.json")
    parser.add_argument("--out", default="eval/report.json")
    args = parser.parse_args()

    with open(args.results) as f:
        results = json.load(f)

    # very small report with breakdown by answer type
    by_type = {}
    for r in results:
        t = r.get("final_answer", {}).get("type", "text")
        by_type.setdefault(t, 0)
        by_type[t] += 1

    report = {
        "count": len(results),
        "by_type": by_type
    }

    with open(args.out, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()

