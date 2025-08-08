"""
V5 unified test runner
- Runs phase tests with real questions
- No external deps besides stdlib and project files
- Single entry point for transparency
"""

from curated_tests import TransparentTestRunner, PHASE1_PURE_CALCULATION, PHASE2_FINANCIAL_DATA, PHASE3_CALCULATION_WITH_DATA, PHASE4_NARRATIVE
from phase1_calculator import phase1_calculator
from phase2_costco_data import phase2_costco_agent
from phase3_metrics import phase3_metrics_agent


def run_all():
    runner = TransparentTestRunner()
    runner.test_phase("Phase 1: Pure Calculation", PHASE1_PURE_CALCULATION, phase1_calculator)
    runner.test_phase("Phase 2: Costco Financial Data", PHASE2_FINANCIAL_DATA, phase2_costco_agent)
    runner.test_phase("Phase 3: Calculation + Data", PHASE3_CALCULATION_WITH_DATA, phase3_metrics_agent)
    runner.test_phase("Phase 4: Narrative", PHASE4_NARRATIVE, None)
    runner.print_summary()


if __name__ == "__main__":
    run_all()

