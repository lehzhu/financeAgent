"""
FinanceAgent v5 - Minimal main entrypoint

Simple router that delegates to implemented phases.
- Phase 1: Calculator
- Phase 2: Costco data

Keep this minimal and dependency-free.
"""

import os
from typing import Callable
from phase1_calculator import phase1_calculator
from phase2_costco_data import phase2_costco_agent
from phase3_metrics import phase3_metrics_agent


def route(question: str) -> str:
    q = question.lower()
    if "costco" in q:
        # If clearly a calculated metric, try Phase 3, else Phase 2
        if any(t in q for t in ["margin", "growth", "growth rate"]):
            return phase3_metrics_agent(question)
        return phase2_costco_agent(question)
    # Fallback to calculator
    return phase1_calculator(question)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="FinanceAgent v5")
    parser.add_argument('--question', type=str, help='Ask a single question')
    args = parser.parse_args()

    if args.question:
        print(route(args.question))
    else:
        # Interactive mode
        print("FinanceAgent v5 - Interactive (Ctrl+C to exit)")
        while True:
            try:
                q = input("Q: ").strip()
                if not q:
                    continue
                print(route(q))
            except KeyboardInterrupt:
                print("\nBye!")
                break


if __name__ == '__main__':
    main()

