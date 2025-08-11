#!/usr/bin/env python3
"""
Integration test for v5 implementation
Tests all three paths: structured, narrative, and calculations
Run with: python3 v5/test_integration.py
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.orchestrator import Orchestrator, OrchestratorConfig

def test_integration():
    """Run integration tests for all three paths."""
    print("\n" + "="*60)
    print("V5 Finance Agent - Integration Tests")
    print("="*60)
    
    # Initialize orchestrator
    config = OrchestratorConfig(
        model="gpt-4o-mini",
        temperature=0.2,
        json_mode=True
    )
    orchestrator = Orchestrator(config)
    
    # Test cases covering all three paths
    test_cases = [
        # Structured data queries
        {
            "id": "struct1",
            "question": "What was Costco's revenue in 2024?",
            "expected_type": "number",
            "expected_path": "structured"
        },
        {
            "id": "struct2",
            "question": "Show me net income for 2024",
            "expected_type": "number",
            "expected_path": "structured"
        },
        
        # Narrative queries
        {
            "id": "narr1",
            "question": "What are the main risk factors?",
            "expected_type": "text",
            "expected_path": "narrative"
        },
        {
            "id": "narr2",
            "question": "Describe the business strategy",
            "expected_type": "text",
            "expected_path": "narrative"
        },
        
        # Calculation queries
        {
            "id": "calc1",
            "question": "Calculate gross margin from gross profit of 36789 million and revenue of 254123 million",
            "context": {
                "inputs": {
                    "GROSS_PROFIT": "36789000000",
                    "REVENUE": "254123000000"
                }
            },
            "expected_type": "percent",
            "expected_path": "calc"
        },
        {
            "id": "calc2",
            "question": "Calculate YoY growth from 242290 million to 254123 million",
            "context": {
                "inputs": {
                    "VALUE_CURRENT": "254123000000",
                    "VALUE_PRIOR": "242290000000"
                }
            },
            "expected_type": "percent",
            "expected_path": "calc"
        },
        {
            "id": "calc3",
            "question": "What is 15% of 1000000?",
            "context": {
                "inputs": {
                    "PART": "150000",
                    "WHOLE": "1000000"
                }
            },
            "expected_type": "percent",
            "expected_path": "calc"
        }
    ]
    
    # Run tests
    results = []
    for test_case in test_cases:
        print(f"\n--- Test {test_case['id']}: {test_case['question'][:50]}...")
        
        try:
            result = orchestrator.answer(test_case)
            
            # Check result structure
            assert "final_answer" in result, "Missing final_answer"
            assert "trace" in result, "Missing trace"
            assert "sources" in result, "Missing sources"
            
            answer = result["final_answer"]
            assert "type" in answer, "Missing answer type"
            assert "value" in answer, "Missing answer value"
            
            # Check answer type matches expected
            if answer["type"] == test_case["expected_type"]:
                status = "✓"
            else:
                status = f"✗ (got {answer['type']}, expected {test_case['expected_type']})"
            
            # Extract routing from trace
            path_taken = "unknown"
            if result["trace"]:
                first_op = result["trace"][0]
                if isinstance(first_op, dict):
                    op = first_op.get("op", "")
                    if "STRUCTURED" in op:
                        path_taken = "structured"
                    elif "NARRATIVE" in op:
                        path_taken = "narrative"
                    elif "COMPUTE" in op or "CALC" in op:
                        path_taken = "calc"
            
            print(f"  Status: {status}")
            print(f"  Path: {path_taken} (expected: {test_case['expected_path']})")
            print(f"  Answer: {answer['value'][:100] if len(str(answer['value'])) > 100 else answer['value']}")
            if answer.get("unit"):
                print(f"  Unit: {answer['unit']}")
            
            results.append({
                "test_id": test_case["id"],
                "passed": status == "✓",
                "result": result
            })
            
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            results.append({
                "test_id": test_case["id"],
                "passed": False,
                "error": str(e)
            })
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary:")
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    print(f"  Passed: {passed}/{total} ({100*passed/total:.1f}%)")
    
    # Show failed tests
    failed = [r for r in results if not r["passed"]]
    if failed:
        print("\nFailed tests:")
        for r in failed:
            print(f"  - {r['test_id']}: {r.get('error', 'Type mismatch')}")
    
    print("="*60)
    
    return results

def main():
    """Run all integration tests."""
    results = test_integration()
    
    # Save results for analysis
    with open("v5/test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to v5/test_results.json")

if __name__ == "__main__":
    main()
