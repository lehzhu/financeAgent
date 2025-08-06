#!/usr/bin/env python3
"""
Quick 20-question test for the Finance Agent.
Tests a variety of question types: tactical, conceptual, and calculation.
"""

import modal
import json
import time
from datetime import datetime

# Test questions - variety of types
TEST_QUESTIONS = [
    # Tactical (fact-based) questions
    {
        "question": "What was Costco's total revenue in fiscal 2024?",
        "expected_keywords": ["254", "billion", "revenue"],
        "type": "tactical"
    },
    {
        "question": "How many warehouses does Costco operate globally?",
        "expected_keywords": ["871", "warehouses"],
        "type": "tactical"
    },
    {
        "question": "What is Costco's membership fee revenue?",
        "expected_keywords": ["4.8", "billion", "membership"],
        "type": "tactical"
    },
    {
        "question": "What was Costco's net income for 2024?",
        "expected_keywords": ["7", "billion", "income"],
        "type": "tactical"
    },
    {
        "question": "What is Costco's gross margin percentage?",
        "expected_keywords": ["10", "11", "margin", "%"],
        "type": "tactical"
    },
    {
        "question": "How much did Costco spend on capital expenditures?",
        "expected_keywords": ["capital", "billion"],
        "type": "tactical"
    },
    {
        "question": "What was the year-over-year revenue growth rate?",
        "expected_keywords": ["5", "growth", "%"],
        "type": "tactical"
    },
    
    # Calculation questions
    {
        "question": "Calculate Costco's profit margin if revenue is $254B and net income is $7.4B",
        "expected_keywords": ["2.9", "3", "margin"],
        "type": "calculation"
    },
    {
        "question": "What is the operating margin if operating income is $9.3B and revenue is $254B?",
        "expected_keywords": ["3.6", "3.7", "margin"],
        "type": "calculation"
    },
    {
        "question": "Calculate NOPAT with EBIT of $9.3B and tax rate of 25%",
        "expected_keywords": ["6.9", "7", "NOPAT"],
        "type": "calculation"
    },
    
    # Conceptual questions
    {
        "question": "What are Costco's main competitive advantages?",
        "expected_keywords": ["membership", "bulk", "value"],
        "type": "conceptual"
    },
    {
        "question": "How does Costco's business model differ from traditional retailers?",
        "expected_keywords": ["membership", "warehouse", "bulk"],
        "type": "conceptual"
    },
    {
        "question": "What are the key risk factors for Costco?",
        "expected_keywords": ["competition", "economic", "supply"],
        "type": "conceptual"
    },
    {
        "question": "Is Costco profitable?",
        "expected_keywords": ["yes", "profitable", "income"],
        "type": "conceptual"
    },
    {
        "question": "Does Costco pay dividends to shareholders?",
        "expected_keywords": ["yes", "dividend"],
        "type": "conceptual"
    },
    
    # Mixed/Complex questions
    {
        "question": "Compare Costco's revenue growth to its profit growth",
        "expected_keywords": ["revenue", "profit", "growth"],
        "type": "complex"
    },
    {
        "question": "What percentage of revenue comes from membership fees?",
        "expected_keywords": ["1.8", "2", "membership", "%"],
        "type": "complex"
    },
    {
        "question": "How efficient is Costco's inventory management?",
        "expected_keywords": ["inventory", "turnover", "days"],
        "type": "complex"
    },
    {
        "question": "What is Costco's return on equity?",
        "expected_keywords": ["ROE", "return", "equity", "%"],
        "type": "complex"
    },
    {
        "question": "Analyze Costco's debt-to-equity ratio",
        "expected_keywords": ["debt", "equity", "ratio"],
        "type": "complex"
    }
]

def check_answer_quality(answer: str, expected_keywords: list) -> tuple:
    """
    Check if answer contains expected keywords.
    Returns (is_correct, matched_keywords)
    """
    if not answer:
        return False, []
    
    answer_lower = answer.lower()
    matched = []
    
    for keyword in expected_keywords:
        if keyword.lower() in answer_lower:
            matched.append(keyword)
    
    # Consider correct if at least 50% of keywords are found
    is_correct = len(matched) >= len(expected_keywords) * 0.5
    return is_correct, matched

def run_test():
    """Run the 20-question test."""
    
    print("=" * 70)
    print("FINANCE AGENT - QUICK 20-QUESTION TEST")
    print("=" * 70)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Import the agent
    from agent.main import process_question_enhanced
    
    results = {
        "tactical": {"correct": 0, "total": 0},
        "calculation": {"correct": 0, "total": 0},
        "conceptual": {"correct": 0, "total": 0},
        "complex": {"correct": 0, "total": 0}
    }
    
    all_results = []
    
    for i, test_case in enumerate(TEST_QUESTIONS, 1):
        print(f"\n[{i}/20] Testing: {test_case['question'][:60]}...")
        print(f"Type: {test_case['type'].upper()}")
        
        start_time = time.time()
        
        try:
            # Process the question
            answer = process_question_enhanced.remote(test_case["question"])
            
            elapsed = time.time() - start_time
            
            # Check answer quality
            is_correct, matched = check_answer_quality(answer, test_case["expected_keywords"])
            
            # Update results
            results[test_case["type"]]["total"] += 1
            if is_correct:
                results[test_case["type"]]["correct"] += 1
                print(f"✅ CORRECT - Matched: {matched}")
            else:
                print(f"❌ INCORRECT - Expected: {test_case['expected_keywords']}")
            
            print(f"Time: {elapsed:.1f}s")
            print(f"Answer preview: {answer[:150]}...")
            
            # Store detailed result
            all_results.append({
                "question": test_case["question"],
                "type": test_case["type"],
                "answer": answer,
                "correct": is_correct,
                "matched": matched,
                "time": elapsed
            })
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            results[test_case["type"]]["total"] += 1
            all_results.append({
                "question": test_case["question"],
                "type": test_case["type"],
                "error": str(e),
                "correct": False
            })
        
        # Brief pause to avoid rate limits
        if i < 20:
            time.sleep(1)
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST RESULTS SUMMARY")
    print("=" * 70)
    
    total_correct = 0
    total_questions = 0
    
    for q_type, stats in results.items():
        if stats["total"] > 0:
            accuracy = (stats["correct"] / stats["total"]) * 100
            print(f"\n{q_type.upper()}:")
            print(f"  Correct: {stats['correct']}/{stats['total']}")
            print(f"  Accuracy: {accuracy:.1f}%")
            total_correct += stats["correct"]
            total_questions += stats["total"]
    
    overall_accuracy = (total_correct / total_questions) * 100 if total_questions > 0 else 0
    
    print(f"\nOVERALL:")
    print(f"  Total Correct: {total_correct}/{total_questions}")
    print(f"  Overall Accuracy: {overall_accuracy:.1f}%")
    
    # Save detailed results
    with open("dump/quick_test_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": total_questions,
                "correct": total_correct,
                "accuracy": overall_accuracy
            },
            "by_type": results,
            "detailed": all_results
        }, f, indent=2)
    
    print(f"\nDetailed results saved to dump/quick_test_results.json")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return overall_accuracy

# Create Modal app
app = modal.App("quick-test")

@app.local_entrypoint()
def main():
    """Run the test as a Modal local entrypoint."""
    accuracy = run_test()
    
    print("\n" + "=" * 70)
    if accuracy >= 60:
        print("🎉 EXCELLENT! Accuracy exceeds 60% target!")
    elif accuracy >= 50:
        print("✅ GOOD! Approaching the baseline target.")
    else:
        print("⚠️ NEEDS IMPROVEMENT. Below 50% accuracy.")
    print("=" * 70)
    
    return accuracy
