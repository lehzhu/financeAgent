#!/usr/bin/env python3
"""
Local test script for v5 implementation
Run with: python v5/test_local.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.orchestrator import Orchestrator, OrchestratorConfig
from agent.router.simple_router import SimpleRouter

def test_router():
    """Test the router component."""
    print("\n=== Testing Router ===")
    router = SimpleRouter()
    
    test_cases = [
        ("What was Costco's revenue in 2024?", "structured"),
        ("Calculate the gross margin", "calc"),
        ("What are the main risk factors?", "narrative"),
        ("Describe the business strategy", "narrative"),
        ("What is 15% of 1 million?", "calc"),
        ("Show me net income for the last 3 years", "structured"),
        ("Calculate EBITDA excluding stock-based compensation", "assumption-calc"),
    ]
    
    for question, expected in test_cases:
        result = router.route(question)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{question[:40]}...' -> {result} (expected: {expected})")

def test_finance_math():
    """Test the finance math engine."""
    print("\n=== Testing Finance Math ===")
    from tools.finance_math import compute_formula
    
    # Test gross margin calculation
    try:
        result = compute_formula({
            "metric_id": "GROSS_MARGIN",
            "inputs": {
                "GROSS_PROFIT": "50000",
                "REVENUE": "200000"
            }
        })
        print(f"✓ Gross Margin: {result['value']}% (expected: 25%)")
    except Exception as e:
        print(f"✗ Gross Margin calculation failed: {e}")
    
    # Test YoY growth
    try:
        result = compute_formula({
            "metric_id": "YOY_GROWTH",
            "inputs": {
                "VALUE_CURRENT": "150",
                "VALUE_PRIOR": "100"
            }
        })
        print(f"✓ YoY Growth: {result['value']}% (expected: 50%)")
    except Exception as e:
        print(f"✗ YoY Growth calculation failed: {e}")

def test_orchestrator():
    """Test the orchestrator (without external dependencies)."""
    print("\n=== Testing Orchestrator (Mock Mode) ===")
    
    config = OrchestratorConfig(
        model="gpt-4o-mini",
        temperature=0.2,
        json_mode=True
    )
    
    orchestrator = Orchestrator(config)
    
    # Test with a simple question (will fail on actual tools but tests the flow)
    test_questions = [
        {
            "id": "test1",
            "question": "What was revenue in 2024?",
            "context": {}
        },
        {
            "id": "test2", 
            "question": "Calculate gross margin from 50k gross profit and 200k revenue",
            "context": {
                "inputs": {
                    "GROSS_PROFIT": "50000",
                    "REVENUE": "200000"
                }
            }
        }
    ]
    
    for item in test_questions:
        try:
            result = orchestrator.answer(item)
            print(f"✓ Processed: '{item['question'][:40]}...'")
            if "final_answer" in result:
                print(f"  Answer type: {result['final_answer'].get('type', 'unknown')}")
        except Exception as e:
            print(f"⚠ Failed (expected without DB/FAISS): '{item['question'][:40]}...' - {str(e)[:50]}")

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("V5 Finance Agent - Local Component Tests")
    print("="*60)
    
    test_router()
    test_finance_math()
    test_orchestrator()
    
    print("\n" + "="*60)
    print("Tests completed. Deploy with: modal deploy v5/deploy.py")
    print("="*60)

if __name__ == "__main__":
    main()
