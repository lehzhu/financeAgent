"""
V5 Curated Test Questions

Hand-picked questions from FinanceQA dataset analysis to drive transparent, 
incremental development. Focus on what actually works vs what doesn't.

Based on evaluation patterns from v4 and known question types.
"""

import re
import time
from collections import defaultdict


def extract_number(text):
    """Extract numerical value from text - using the proven v4 approach."""
    if text is None:
        return None
    
    text = str(text).strip()
    
    # JSON format parsing
    json_pattern = r'\{"answer":\s*(\d+(?:\.\d+)?),\s*"unit":\s*"([^"]+)"\}'
    json_match = re.search(json_pattern, text)
    if json_match:
        try:
            value = float(json_match.group(1))
            unit = json_match.group(2).lower()
            
            if "million" in unit:
                value *= 1000000
            elif "billion" in unit:
                value *= 1000000000
            elif "thousand" in unit or "k" in unit:
                value *= 1000
                
            return value
        except:
            pass
    
    # Fallback patterns
    patterns = [
        r'(?:is|equals?|=|:)\s*\$?([\d,]+(?:\.\d+)?)',
        r'\$([\d,]+(?:\.\d+)?)\s*(?:million|billion)?',
        r'([\d,]+(?:\.\d+)?)\s*(?:million|billion|%)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            num_str = match.group(1).replace(",", "")
            try:
                value = float(num_str)
                if "million" in text.lower():
                    value *= 1000000 if value < 1000 else 1
                elif "billion" in text.lower():
                    value *= 1000000000 if value < 1000000 else 1
                return value
            except:
                pass
    
    # Last resort: find any number
    numbers = re.findall(r'\d+[,\d]*(?:\.\d+)?', text)
    if numbers:
        for num in reversed(numbers):
            num_clean = num.replace(",", "")
            if len(num_clean) == 4 and num_clean[:2] in ['19', '20']:
                continue  # Skip years
            try:
                return float(num_clean)
            except:
                pass
    
    return None


def answers_match(expected, got, tolerance=0.02):
    """Check if answers match with tolerance."""
    if str(expected).strip() == str(got).strip():
        return True
    
    # Numerical comparison
    expected_num = extract_number(expected)
    got_num = extract_number(got)
    
    if expected_num is not None and got_num is not None:
        if abs(expected_num - got_num) / max(abs(expected_num), 0.01) < tolerance:
            return True
    
    # Text comparison
    expected_lower = str(expected).lower().strip()
    got_lower = str(got).lower().strip()
    
    if expected_lower in ["yes", "no"] and expected_lower in got_lower[:10]:
        return True
    
    if len(expected_lower) > 5 and expected_lower in got_lower:
        return True
    
    return False


# CURATED TEST QUESTIONS
# Based on FinanceQA patterns and v4 evaluation results

PHASE1_PURE_CALCULATION = [
    # Simple percentage calculations
    {
        "question": "What is 15% of 100?",
        "answer": "15",
        "difficulty": 1,
        "category": "percentage",
        "notes": "Basic percentage - should be easiest"
    },
    {
        "question": "Calculate 25% of 200",
        "answer": "50", 
        "difficulty": 1,
        "category": "percentage",
        "notes": "Another basic percentage"
    },
    {
        "question": "What is the growth rate from 100 to 120?",
        "answer": "20%",
        "difficulty": 2,
        "category": "growth_rate", 
        "notes": "Growth rate calculation"
    },
    {
        "question": "Calculate the ratio 50:25",
        "answer": "2",
        "difficulty": 1,
        "category": "ratio",
        "notes": "Simple division ratio"
    },
    {
        "question": "What is 2 + 2 * 3?",
        "answer": "8",
        "difficulty": 1,
        "category": "arithmetic", 
        "notes": "Order of operations"
    }
]

PHASE2_FINANCIAL_DATA = [
    # Direct data lookup questions from Costco
    {
        "question": "What was Costco's total revenue in fiscal 2024?",
        "answer": "$254.5 billion",  # Real expected format
        "difficulty": 2,
        "category": "revenue",
        "notes": "Direct lookup from financial statements"
    },
    {
        "question": "What was Costco's net income for fiscal year 2024?", 
        "answer": "$7.4 billion",  # Real expected format
        "difficulty": 2,
        "category": "net_income",
        "notes": "Basic profit lookup"
    },
    {
        "question": "What were Costco's net sales in 2024?",
        "answer": "$249.6 billion",  # Real expected format
        "difficulty": 2, 
        "category": "net_sales",
        "notes": "Net sales lookup (more specific than total revenue)"
    },
    {
        "question": "What was Costco's operating income in 2024?",
        "answer": "$9.9 billion",  # Real expected format
        "difficulty": 2,
        "category": "operating_income", 
        "notes": "Operating profit lookup"
    }
]

PHASE3_CALCULATION_WITH_DATA = [
    # Questions requiring both data lookup AND calculation
    {
        "question": "What was Costco's profit margin in 2024?",
        "answer": "2.9%",  # Net income / Total Revenue * 100
        "difficulty": 3,
        "category": "margin_calculation",
        "notes": "Net income / total revenue"
    },
    {
        "question": "Calculate Costco's revenue growth rate from 2023 to 2024",
        "answer": "5.0%",  # (Revenue 2024 - Revenue 2023) / Revenue 2023 * 100
        "difficulty": 3,
        "category": "growth_calculation", 
        "notes": "Revenue growth year-over-year"
    },
    {
        "question": "Calculate Costco's revenue growth rate from 2022 to 2023",
        "answer": "6.8%",  # (Revenue 2023 - Revenue 2022) / Revenue 2022 * 100
        "difficulty": 3,
        "category": "growth_calculation", 
        "notes": "Revenue growth 2022->2023"
    },
    {
        "question": "What was Costco's operating margin in 2024?",
        "answer": "3.9%",  # Operating income / Total Revenue * 100
        "difficulty": 3,
        "category": "margin_calculation", 
        "notes": "Operating income / total revenue"
    }
]

PHASE4_NARRATIVE = [
    # Conceptual questions requiring document search
    {
        "question": "What are Costco's main business segments?",
        "answer": "warehouse operations and e-commerce",
        "difficulty": 3,
        "category": "business_description",
        "notes": "Requires narrative understanding"
    },
    {
        "question": "What are the key risk factors for Costco?",
        "answer": "competition, supply chain, economic conditions",
        "difficulty": 4,
        "category": "risk_analysis",
        "notes": "Complex narrative synthesis" 
    }
]


class TransparentTestRunner:
    """Transparent test runner that shows exactly what works and what doesn't."""
    
    def __init__(self):
        self.results = defaultdict(lambda: {'total': 0, 'correct': 0, 'details': []})
    
    def test_phase(self, phase_name, test_questions, agent_function=None):
        """Test a specific phase with full transparency."""
        print(f"\\n{'='*70}")
        print(f"TESTING {phase_name.upper()}")
        print(f"{'='*70}")
        print(f"Questions: {len(test_questions)}")
        print(f"Agent: {'Available' if agent_function else 'NOT IMPLEMENTED'}")
        print()
        
        phase_results = self.results[phase_name]
        
        for i, test_case in enumerate(test_questions):
            question = test_case['question']
            expected = test_case['answer']
            difficulty = test_case['difficulty']
            category = test_case['category']
            notes = test_case.get('notes', '')
            
            phase_results['total'] += 1
            
            print(f"[{i+1}/{len(test_questions)}] Difficulty: {difficulty} | Category: {category}")
            print(f"Question: {question}")
            print(f"Expected: {expected}")
            print(f"Notes: {notes}")
            
            if not agent_function:
                result = "❌ NO AGENT IMPLEMENTED"
                status = "SKIP"
                print(f"Result: {result}")
            else:
                try:
                    start_time = time.time()
                    got = agent_function(question)
                    elapsed = time.time() - start_time
                    
                    exact_match = str(got).strip() == str(expected).strip()
                    smart_match = answers_match(expected, got)
                    
                    if smart_match:
                        phase_results['correct'] += 1
                        status = "✓ CORRECT"
                    else:
                        status = "✗ WRONG"
                    
                    # Show numerical comparison if applicable
                    exp_num = extract_number(expected)
                    got_num = extract_number(got)
                    if exp_num and got_num:
                        diff_pct = abs(exp_num - got_num) / max(abs(exp_num), 0.01) * 100
                        print(f"Numbers: Expected {exp_num}, Got {got_num} (diff: {diff_pct:.1f}%)")
                    
                    print(f"Result: {got}")
                    print(f"Status: {status} ({elapsed:.1f}s)")
                    
                except Exception as e:
                    status = "❌ ERROR"
                    print(f"Result: ERROR - {str(e)}")
                    print(f"Status: {status}")
            
            # Track detailed results
            phase_results['details'].append({
                'question': question,
                'expected': expected,
                'got': result if not agent_function else got,
                'status': status,
                'difficulty': difficulty,
                'category': category
            })
            
            # Running score
            accuracy = (phase_results['correct'] / phase_results['total']) * 100
            print(f"Running: {phase_results['correct']}/{phase_results['total']} = {accuracy:.1f}%")
            print("-" * 70)
            print()
        
        return phase_results
    
    def print_summary(self):
        """Print overall summary across all phases."""
        print("\\n" + "="*70)
        print("OVERALL RESULTS SUMMARY")
        print("="*70)
        
        total_questions = 0
        total_correct = 0
        
        for phase_name, results in self.results.items():
            total = results['total'] 
            correct = results['correct']
            accuracy = (correct / total * 100) if total > 0 else 0
            
            total_questions += total
            total_correct += correct
            
            print(f"{phase_name:25} {correct:2d}/{total:2d} ({accuracy:5.1f}%)")
        
        overall_accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0
        print("-" * 70)
        print(f"{'OVERALL':25} {total_correct:2d}/{total_questions:2d} ({overall_accuracy:5.1f}%)")
        print("="*70)
        
        # Show what's working vs not working
        print("\\nWHAT'S WORKING:")
        working_phases = [name for name, r in self.results.items() if r['correct']/r['total'] >= 0.5]
        if working_phases:
            for phase in working_phases:
                r = self.results[phase]
                print(f"  ✓ {phase}: {r['correct']}/{r['total']} correct")
        else:
            print("  ❌ No phases working well yet")
        
        print("\\nNEEDS WORK:")
        broken_phases = [name for name, r in self.results.items() if r['correct']/r['total'] < 0.5]
        for phase in broken_phases:
            r = self.results[phase]
            print(f"  ❌ {phase}: {r['correct']}/{r['total']} correct")


# Example agent functions for testing
def dummy_calculator(question):
    """Dummy calculator for testing the framework."""
    q_lower = question.lower()
    
    # Very basic pattern matching 
    if "2 + 2" in q_lower:
        return "4"
    elif "15% of 100" in q_lower:
        return "15"
    elif "25% of 200" in q_lower:
        return "50"
    else:
        return "I don't know how to calculate that"


def test_framework_demo():
    """Demonstrate the transparent testing framework."""
    runner = TransparentTestRunner()
    
    # Test Phase 1 with dummy calculator
    print("DEMO: Testing Phase 1 with a simple dummy calculator")
    runner.test_phase("Phase 1: Pure Calculation", PHASE1_PURE_CALCULATION, dummy_calculator)
    
    # Test Phase 2 without agent (show transparency)
    runner.test_phase("Phase 2: Financial Data", PHASE2_FINANCIAL_DATA, None)
    
    # Test Phase 3 without agent  
    runner.test_phase("Phase 3: Calculation + Data", PHASE3_CALCULATION_WITH_DATA, None)
    
    # Test Phase 4 without agent
    runner.test_phase("Phase 4: Narrative", PHASE4_NARRATIVE, None)
    
    # Show summary
    runner.print_summary()
    
    print("\\n" + "="*70)
    print("This demonstrates TRANSPARENT testing:")
    print("- Shows exactly what each agent can/can't do")
    print("- Uses real questions that matter") 
    print("- Clear pass/fail with explanations")
    print("- Incremental: build Phase 1, then 2, then 3...")
    print("="*70)


if __name__ == "__main__":
    test_framework_demo()
