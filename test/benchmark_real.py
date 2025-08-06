#!/usr/bin/env python3
"""
Real FinanceQA benchmark evaluation using the actual deployed agent.
Tests the agent against the real FinanceQA dataset.
"""

import modal
from datasets import load_dataset
import re
import time
import json
from datetime import datetime
import os
import requests

# Define the Modal app
app = modal.App(
    "finance-benchmark-real",
    image=modal.Image.debian_slim().pip_install(
        "datasets", "requests"
    )
)

def extract_number(text):
    """Extract numerical value from text, handling various formats."""
    if text is None:
        return None
    
    # Convert to string and clean
    text = str(text).strip()
    
    # Remove common prefixes/suffixes
    text = text.replace("$", "").replace(",", "").replace("%", "")
    text = text.replace("(in millions)", "").replace("million", "")
    text = text.replace("billion", "000").replace("x", "")
    
    # Try to find a number
    numbers = re.findall(r'-?\d+\.?\d*', text)
    if numbers:
        try:
            return float(numbers[0])
        except:
            return None
    return None

def answers_match(expected, got, tolerance=0.02):
    """Check if answers match with some tolerance for numerical values."""
    if expected == got:
        return True
    
    # Try numerical comparison
    expected_num = extract_number(expected)
    got_num = extract_number(got)
    
    if expected_num is not None and got_num is not None:
        # Allow 2% tolerance for numerical answers
        if abs(expected_num - got_num) / max(abs(expected_num), 0.01) < tolerance:
            return True
    
    # Check for Yes/No questions
    expected_lower = str(expected).lower().strip()
    got_lower = str(got).lower().strip()
    
    if expected_lower in ["yes", "no"]:
        if expected_lower in got_lower:
            return True
    
    # Check if the expected answer is contained in the response
    if expected_lower in got_lower:
        return True
    
    return False

@app.function(timeout=3600)
def run_benchmark(test_size=20, agent_url=None):
    """
    Run the official FinanceQA benchmark evaluation against the deployed agent.
    
    Args:
        test_size: Number of questions to test (default: 20, max: 148)
        agent_url: URL of the deployed agent API
    """
    
    # Load the FinanceQA test set
    print("Loading FinanceQA dataset...")
    dataset = load_dataset("AfterQuery/FinanceQA", split="test")
    
    # If no agent URL provided, use the Modal deployment
    if not agent_url:
        # This would be the URL of your deployed Modal agent
        agent_url = "https://lehzhu--finance-agent-api.modal.run"
    
    def call_agent(question, context=""):
        """Call the deployed agent API."""
        try:
            # Prepare the request
            payload = {
                "question": question,
                "context": context[:4000] if len(context) > 4000 else context  # Truncate if needed
            }
            
            # Call the agent API
            response = requests.post(
                f"{agent_url}/process",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("answer", "")
            else:
                print(f"Agent returned status {response.status_code}")
                return ""
                
        except Exception as e:
            print(f"Error calling agent: {e}")
            return ""
    
    # Limit test_size to dataset size
    test_size = min(test_size, len(dataset))
    
    correct = 0
    errors = 0
    close_matches = 0
    
    results_by_type = {
        "tactical": {"correct": 0, "total": 0},
        "calculation": {"correct": 0, "total": 0},
        "conceptual": {"correct": 0, "total": 0}
    }
    
    all_results = []
    
    print("="*70)
    print("FINANCEQA BENCHMARK EVALUATION")
    print("="*70)
    print(f"Testing {test_size} questions from official dataset")
    print(f"Total dataset size: {len(dataset)} questions")
    print(f"Target accuracy: 56.8% (baseline from paper)")
    print(f"Previous best: 46.7% (with enhanced agent)")
    print("="*70)
    print()
    
    for i in range(test_size):
        row = dataset[i]
        question = row["question"]
        context = row.get("context", "")
        expected = row["answer"]
        
        # Determine question type
        if any(word in question.lower() for word in ["calculate", "compute", "what is the", "how much"]):
            q_type = "calculation" if "calculate" in question.lower() else "tactical"
        else:
            q_type = "conceptual"
        
        results_by_type[q_type]["total"] += 1
        
        try:
            print(f"[{i+1}/{test_size}] Type: {q_type.upper()}")
            print(f"Q: {question[:80]}...")
            if context:
                print(f"Context: {context[:100]}...")
            
            start_time = time.time()
            
            # Call our deployed agent
            result = call_agent(question, context)
            
            elapsed = time.time() - start_time
            
            # Extract the answer from the result
            if result:
                # Look for the answer pattern
                import re
                answer_match = re.search(r'(?:answer|result).*?([0-9$,.\-%]+|yes|no)', result.lower())
                if answer_match:
                    result = answer_match.group(1)
            
            # Check if answers match
            exact_match = (result == expected)
            smart_match = answers_match(expected, result)
            
            if smart_match:
                correct += 1
                results_by_type[q_type]["correct"] += 1
                if not exact_match:
                    close_matches += 1
            
            # Show results
            print(f"Expected: {expected}")
            print(f"Got:      {result[:100] if result else 'No answer'}...")
            
            # Show numerical comparison if applicable
            exp_num = extract_number(expected)
            got_num = extract_number(result)
            if exp_num is not None and got_num is not None:
                diff = abs(exp_num - got_num) / max(abs(exp_num), 0.01) * 100
                print(f"Numbers:  {exp_num} vs {got_num} (diff: {diff:.2f}%)")
            
            match_type = '✓ EXACT' if exact_match else '✓ SMART' if smart_match else '✗ FAIL'
            print(f"Result:   {match_type}")
            print(f"Time:     {elapsed:.1f}s")
            print(f"Running:  {(correct/(i+1)*100):.1f}% accurate")
            print("-"*70)
            
            # Store result
            all_results.append({
                "question": question,
                "context": context[:500],  # Store truncated context
                "expected": expected,
                "got": result,
                "type": q_type,
                "match": smart_match,
                "exact": exact_match,
                "time": elapsed
            })
            
            # Pause to avoid rate limits
            if (i + 1) % 5 == 0:
                time.sleep(2)
                
        except Exception as e:
            errors += 1
            print(f"ERROR: {str(e)[:200]}")
            print("-"*70)
            
            all_results.append({
                "question": question,
                "type": q_type,
                "error": str(e),
                "match": False
            })
            
            if "rate_limit" in str(e).lower():
                print("Waiting 60 seconds for rate limit...")
                time.sleep(60)
    
    # Calculate final results
    overall_accuracy = (correct / test_size * 100) if test_size > 0 else 0
    
    print("\n" + "="*70)
    print("BENCHMARK RESULTS")
    print("="*70)
    
    # Results by type
    for q_type, stats in results_by_type.items():
        if stats["total"] > 0:
            accuracy = (stats["correct"] / stats["total"]) * 100
            print(f"\n{q_type.upper()}:")
            print(f"  Correct: {stats['correct']}/{stats['total']}")
            print(f"  Accuracy: {accuracy:.1f}%")
    
    print(f"\nOVERALL:")
    print(f"  Questions tested: {test_size}")
    print(f"  Correct answers:  {correct} ({overall_accuracy:.1f}%)")
    print(f"    - Exact matches: {correct - close_matches}")
    print(f"    - Smart matches: {close_matches}")
    print(f"  Errors: {errors}")
    
    print("\n" + "="*70)
    print("COMPARISON WITH BASELINE")
    print("="*70)
    print(f"Our Agent:      {overall_accuracy:.1f}%")
    print(f"Previous best:  46.7%")
    print(f"Target (paper): 56.8%")
    print(f"Gap from best:  {46.7 - overall_accuracy:.1f}%")
    print(f"Gap from target: {56.8 - overall_accuracy:.1f}%")
    
    if overall_accuracy >= 56.8:
        print("\n🎉 SUCCESS! We beat the baseline!")
    elif overall_accuracy >= 46.7:
        print("\n✅ Maintained our previous performance level")
    elif overall_accuracy >= 40:
        print("\n📊 Reasonable performance, close to our best")
    else:
        print("\n⚠️ Performance degraded - need to check the agent")
    
    # Save detailed results
    results_file = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": test_size,
            "correct": correct,
            "accuracy": overall_accuracy,
            "exact_matches": correct - close_matches,
            "smart_matches": close_matches,
            "errors": errors
        },
        "by_type": results_by_type,
        "previous_best": 46.7,
        "target": 56.8,
        "gap_from_best": 46.7 - overall_accuracy,
        "gap_from_target": 56.8 - overall_accuracy,
        "detailed": all_results
    }
    
    # Save locally
    with open("benchmark_results_real.json", "w") as f:
        json.dump(results_file, f, indent=2)
    
    print(f"\nDetailed results saved to benchmark_results_real.json")
    print("="*70)
    
    return overall_accuracy

@app.local_entrypoint()
def main(test_size: int = 20):
    """
    Run the benchmark evaluation.
    
    Args:
        test_size: Number of questions to test (default: 20)
    """
    print(f"\nStarting FinanceQA benchmark with {test_size} questions...")
    print("Testing against the REAL deployed agent (not a simplified version)")
    accuracy = run_benchmark.remote(test_size)
    print(f"\nFinal accuracy: {accuracy:.1f}%")
    
    if accuracy < 40:
        print("\n⚠️ WARNING: Significant performance regression detected!")
        print("The standalone benchmark was using a simplified agent.")
        print("We need to ensure we're testing the actual multi-agent system.")
    
    return accuracy
