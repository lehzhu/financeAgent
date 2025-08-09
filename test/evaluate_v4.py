"""
Evaluation script for the three-tool finance agent (v4).
Tests the agent's ability to route questions appropriately and provide accurate answers.
"""

import modal
from datasets import load_dataset
import os
import re
import time
import json

# Define the Modal app
app = modal.App(
    "finance-evaluate-v4",
    image=modal.Image.debian_slim().pip_install("datasets", "openai"),
    secrets=[modal.Secret.from_name("openai-key-1")]
)

def extract_number(text):
    """Extract numerical value from text, handling various formats including JSON."""
    if text is None:
        return None
    
    # Convert to string and clean
    text = str(text).strip()
    
    # First, check if the text contains our structured JSON format
    json_pattern = r'\{"answer":\s*(\d+(?:\.\d+)?),\s*"unit":\s*"([^"]+)"\}'
    json_match = re.search(json_pattern, text)
    if json_match:
        try:
            value = float(json_match.group(1))
            unit = json_match.group(2).lower()
            
            # Convert based on unit
            if "million" in unit:
                value *= 1000000
            elif "billion" in unit:
                value *= 1000000000
            elif "thousand" in unit or "k" in unit:
                value *= 1000
            elif "percent" in unit or "%" in unit:
                # Percentages are kept as-is
                pass
                
            return value
        except:
            pass
    
    # Try parsing as complete JSON
    try:
        # Find JSON object in the text
        json_start = text.find('{')
        json_end = text.rfind('}')
        if json_start >= 0 and json_end > json_start:
            json_str = text[json_start:json_end+1]
            data = json.loads(json_str)
            if isinstance(data, dict) and 'answer' in data:
                value = float(data['answer'])
                unit = data.get('unit', '').lower()
                
                if "million" in unit:
                    value *= 1000000
                elif "billion" in unit:
                    value *= 1000000000
                elif "thousand" in unit or "k" in unit:
                    value *= 1000
                    
                return value
    except:
        pass
    
    # Fallback to original patterns
    patterns = [
        r'(?:is|equals?|=|:)\s*\$?([\d,]+(?:\.\d+)?)',
        r'\$([\d,]+(?:\.\d+)?)\s*(?:million|billion)?',
        r'([\d,]+(?:\.\d+)?)\s*(?:million|billion)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Clean and return the number
            num_str = match.group(1).replace(",", "")
            try:
                value = float(num_str)
                # Handle million/billion
                if "million" in text.lower():
                    value *= 1000000 if value < 1000 else 1  # Avoid double conversion
                elif "billion" in text.lower():
                    value *= 1000000000 if value < 1000000 else 1
                return value
            except:
                pass
    
    # Fallback: get the last number in the text (often the answer)
    numbers = re.findall(r'\d+[,\d]*(?:\.\d+)?', text)
    if numbers:
        # Skip years (4 digits starting with 19 or 20)
        for num in reversed(numbers):
            num_clean = num.replace(",", "")
            if len(num_clean) == 4 and num_clean[:2] in ['19', '20']:
                continue
            try:
                return float(num_clean)
            except:
                pass
    
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
        if expected_lower in got_lower[:10]:  # Check at beginning
            return True
    
    # Check if the expected answer is contained in the response
    if len(expected_lower) > 5 and expected_lower in got_lower:
        return True
    
    return False

def categorize_question(question):
    """Categorize question type for analysis."""
    question_lower = question.lower()
    
    if any(term in question_lower for term in ['calculate', 'compute', 'what is % of', 'growth rate']):
        return 'calculation'
    elif any(term in question_lower for term in ['revenue', 'income', 'profit', 'assets', 'eps', 'margin']):
        return 'structured_data'
    elif any(term in question_lower for term in ['risk', 'strategy', 'describe', 'what are', 'how does']):
        return 'narrative'
    else:
        return 'other'

# Evaluation function
@app.function(timeout=1800)
def evaluate_agent_v4(test_size=10):
    """Evaluate the three-tool finance agent.
    
    Args:
        test_size: Number of questions to test (default: 10)
    """
    # Coerce test_size to int (Modal may pass strings)
    try:
        test_size = int(test_size)
    except Exception:
        test_size = 10
    
    # Load the FinanceQA test set
    dataset = load_dataset("AfterQuery/FinanceQA", split="test")
    
    # Randomly select test_size questions
    import random
    total = len(dataset)
    n = min(test_size, total)
    indices = random.sample(range(total), n)
    
    # Import Modal to call the deployed agent
    import modal
    
    # Get the deployed function - use the newly deployed v4
    process_question = modal.Function.from_name("finance-agent-v4-new", "process_question_v4")
    
    # Track results by category
    results = {
        'total': 0,
        'correct': 0,
        'errors': 0,
        'by_category': {
            'calculation': {'total': 0, 'correct': 0},
            'structured_data': {'total': 0, 'correct': 0},
            'narrative': {'total': 0, 'correct': 0},
            'other': {'total': 0, 'correct': 0}
        }
    }
    
    print("="*60)
    print("FINANCE AGENT V4 EVALUATION (Three-Tool Architecture)")
    print(f"Testing {test_size} questions")
    print(f"Dataset size: {len(dataset)} questions")
    print("="*60)
    print()
    
    for idx, i in enumerate(indices):
        row = dataset[i]
        question = row["question"]
        expected = row["answer"]
        context = row.get("context", "")
        
        # Categorize question
        category = categorize_question(question)
        results['total'] += 1
        results['by_category'][category]['total'] += 1
        
        try:
            start_time = time.time()
            
            # For v4, we don't pass context as it uses its own data sources
            result = process_question.remote(question)
            
            elapsed = time.time() - start_time
            
            # Check if answers match
            exact_match = (result == expected)
            smart_match = answers_match(expected, result)
            
            if smart_match:
                results['correct'] += 1
                results['by_category'][category]['correct'] += 1
            
            # Detailed output
            print(f"[Question {idx+1}/{test_size} (#{i} from dataset)] Category: {category.upper()}")
            print(f"Q: {question[:100]}...")
            print(f"Expected: {expected}")
            print(f"Got:      {result[:200]}..." if len(result) > 200 else f"Got:      {result}")
            
            # Show numerical extraction for debugging
            exp_num = extract_number(expected)
            got_num = extract_number(result)
            if exp_num is not None and got_num is not None:
                diff = abs(exp_num - got_num) / max(abs(exp_num), 0.01) * 100
                print(f"Numbers:  {exp_num} vs {got_num} (diff: {diff:.2f}%)")
            
            print(f"Match:    {'✓ EXACT' if exact_match else '✓ SMART' if smart_match else '✗ NO MATCH'}")
            print(f"Time:     {elapsed:.1f}s")
            print(f"Running:  {(results['correct']/results['total']*100):.1f}% accurate")
            print("-"*60)
            print()
            
            # Small delay every 5 questions
            if (idx + 1) % 5 == 0:
                time.sleep(2)
                
        except Exception as e:
            results['errors'] += 1
            print(f"[Question {idx+1}/{test_size} (#{i} from dataset)] ERROR")
            print(f"Q: {question[:100]}...")
            print(f"Error: {str(e)[:200]}")
            print("-"*60)
            print()
            
            if "rate_limit" in str(e).lower():
                print("Waiting 30 seconds for rate limit...")
                time.sleep(30)

    # Print final results
    print("="*60)
    print("FINAL RESULTS - V4 Three-Tool Architecture")
    print("="*60)
    print(f"Questions tested:  {results['total']}")
    print(f"Correct answers:   {results['correct']} ({results['correct']/results['total']*100:.1f}%)")
    print(f"Errors:           {results['errors']}")
    print()
    print("Results by Category:")
    for cat, data in results['by_category'].items():
        if data['total'] > 0:
            accuracy = data['correct'] / data['total'] * 100
            print(f"  {cat.upper():15} - Total: {data['total']:3d}, Correct: {data['correct']:3d} ({accuracy:.1f}%)")
    print("="*60)
    
    return results

# Test specific question types
@app.function()
def test_question_types():
    """Test specific types of questions to verify the three-tool routing."""
    import modal
    
    process_question = modal.Function.lookup("finance-agent-v4", "process_question_v4")
    
    test_cases = [
        # Structured data lookup questions
        {
            "question": "What was Costco's revenue in 2024?",
            "expected_tool": "structured_data_lookup",
            "type": "financial_metric"
        },
        {
            "question": "Show me the net income for the last 3 years",
            "expected_tool": "structured_data_lookup",
            "type": "historical_data"
        },
        
        # Narrative/conceptual questions
        {
            "question": "What are Costco's main risk factors?",
            "expected_tool": "document_search",
            "type": "risk_analysis"
        },
        {
            "question": "Describe Costco's business strategy",
            "expected_tool": "document_search",
            "type": "strategy"
        },
        
        # Calculation questions
        {
            "question": "Calculate 15% of 254 billion",
            "expected_tool": "python_calculator",
            "type": "simple_calculation"
        },
        {
            "question": "What's the growth rate if revenue went from 230B to 254B?",
            "expected_tool": "python_calculator",
            "type": "growth_calculation"
        }
    ]
    
    print("="*60)
    print("TESTING THREE-TOOL ROUTING")
    print("="*60)
    
    for test in test_cases:
        print(f"\nType: {test['type']}")
        print(f"Question: {test['question']}")
        print(f"Expected Tool: {test['expected_tool']}")
        
        try:
            answer = process_question.remote(test['question'])
            print(f"Answer: {answer[:200]}..." if len(answer) > 200 else f"Answer: {answer}")
        except Exception as e:
            print(f"Error: {str(e)}")
        
        print("-"*40)

# Local entrypoint
@app.local_entrypoint()
def main(test_size: int = 30, test_routing: bool = False):
    """Run evaluation with specified number of questions.
    
    Args:
        test_size: Number of questions to test
        test_routing: If True, test specific routing examples
    """
    if test_routing:
        test_question_types.remote()
    else:
        results = evaluate_agent_v4.remote(test_size)
        print(f"\nEvaluation complete. Overall accuracy: {results['correct']/results['total']*100:.1f}%")
