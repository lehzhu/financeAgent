"""
Multi-faceted Evaluation Framework for Finance Agent
Implements hierarchical metrics beyond simple accuracy to better understand agent performance.
"""

import modal
from datasets import load_dataset
import os
import re
import time
import json
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict
import datetime

# Define the Modal app
app = modal.App(
    "finance-evaluate-multifaceted",
    image=modal.Image.debian_slim().pip_install("datasets", "openai"),
    secrets=[modal.Secret.from_name("openai-key-1")]
)

class MatchLevel(Enum):
    """Hierarchy of match quality levels."""
    EXACT_MATCH = "exact_match"           # Answer is identical
    NUMERIC_EQUIV = "numeric_equivalent"   # Same number, different format
    TOLERANCE_2PCT = "tolerance_2pct"      # Within 2% tolerance
    TOLERANCE_5PCT = "tolerance_5pct"      # Within 5% tolerance
    CORRECT_SCALE = "correct_scale_wrong_unit"  # Right value, wrong unit (e.g., 254 vs 254M)
    PARTIAL_CORRECT = "partial_correct"    # Contains some correct info
    HALLUCINATION = "hallucination"        # Plausible but wrong
    NO_ANSWER = "no_answer"               # Agent couldn't answer
    ERROR = "error"                        # Technical error occurred

@dataclass
class EvaluationResult:
    """Detailed evaluation result for a single question."""
    question_id: int
    question: str
    expected_answer: str
    agent_answer: str
    match_level: MatchLevel
    category: str
    response_time: float
    extracted_expected_value: Optional[float]
    extracted_agent_value: Optional[float]
    numeric_difference_pct: Optional[float]
    error_details: Optional[str]
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['match_level'] = self.match_level.value
        return result

class FinanceValueExtractor:
    """Enhanced value extraction with unit handling."""
    
    UNIT_MULTIPLIERS = {
        'k': 1e3,
        'thousand': 1e3,
        'thousands': 1e3,
        'm': 1e6,
        'million': 1e6,
        'millions': 1e6,
        'b': 1e9,
        'billion': 1e9,
        'billions': 1e9,
        't': 1e12,
        'trillion': 1e12,
        'trillions': 1e12,
    }
    
    @classmethod
    def extract_value_and_unit(cls, text: str) -> Tuple[Optional[float], Optional[str]]:
        """Extract numerical value and unit from text."""
        if text is None:
            return None, None
        
        text = str(text).strip()
        
        # Try JSON format first
        json_pattern = r'\{"answer":\s*([\d.]+),\s*"unit":\s*"([^"]+)"\}'
        json_match = re.search(json_pattern, text)
        if json_match:
            try:
                value = float(json_match.group(1))
                unit = json_match.group(2).lower()
                return value, unit
            except:
                pass
        
        # Look for patterns like "$254 billion" or "254M"
        patterns = [
            (r'\$?([\d,]+(?:\.\d+)?)\s*(k|m|b|t|thousand|million|billion|trillion)s?\b', True),
            (r'\$?([\d,]+(?:\.\d+)?)', False),  # Just number, no unit
            (r'([\d,]+(?:\.\d+)?)\s*(?:in\s+)?(thousand|million|billion)s?', True),
        ]
        
        for pattern, has_unit in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    num_str = match.group(1).replace(",", "")
                    value = float(num_str)
                    
                    if has_unit and len(match.groups()) > 1:
                        unit = match.group(2).lower()
                        return value, unit
                    else:
                        # Try to infer unit from context
                        unit = cls._infer_unit_from_context(text)
                        return value, unit
                except:
                    continue
        
        return None, None
    
    @classmethod
    def _infer_unit_from_context(cls, text: str) -> Optional[str]:
        """Infer unit from surrounding context."""
        text_lower = text.lower()
        
        # Check for explicit unit mentions
        for unit in ['trillion', 'billion', 'million', 'thousand']:
            if unit in text_lower:
                return unit
        
        # Check for percentage
        if '%' in text or 'percent' in text_lower:
            return 'percent'
        
        return None
    
    @classmethod
    def normalize_value(cls, value: float, unit: Optional[str]) -> float:
        """Normalize value to base units."""
        if unit is None:
            return value
        
        unit_lower = unit.lower()
        
        # Handle percentages separately
        if 'percent' in unit_lower or '%' in unit_lower:
            return value  # Keep as is
        
        # Apply multiplier
        for key, multiplier in cls.UNIT_MULTIPLIERS.items():
            if key in unit_lower:
                return value * multiplier
        
        return value

class MultiFacetedEvaluator:
    """Main evaluator with hierarchical metrics."""
    
    def __init__(self):
        self.extractor = FinanceValueExtractor()
    
    def evaluate_answer(self, expected: str, agent_answer: str, question: str) -> EvaluationResult:
        """Evaluate an answer at multiple levels."""
        
        # Extract values and units
        exp_value, exp_unit = self.extractor.extract_value_and_unit(expected)
        agent_value, agent_unit = self.extractor.extract_value_and_unit(agent_answer)
        
        # Normalize values
        if exp_value is not None:
            exp_normalized = self.extractor.normalize_value(exp_value, exp_unit)
        else:
            exp_normalized = None
            
        if agent_value is not None:
            agent_normalized = self.extractor.normalize_value(agent_value, agent_unit)
        else:
            agent_normalized = None
        
        # Determine match level
        match_level = self._determine_match_level(
            expected, agent_answer,
            exp_normalized, agent_normalized,
            exp_value, agent_value,
            exp_unit, agent_unit
        )
        
        # Calculate numeric difference if both values exist
        numeric_diff = None
        if exp_normalized is not None and agent_normalized is not None:
            if exp_normalized != 0:
                numeric_diff = abs(exp_normalized - agent_normalized) / abs(exp_normalized) * 100
        
        return EvaluationResult(
            question_id=0,  # Will be set by caller
            question=question[:200],  # Truncate for storage
            expected_answer=expected,
            agent_answer=agent_answer[:500] if agent_answer else "",  # Truncate long answers
            match_level=match_level,
            category="",  # Will be set by caller
            response_time=0,  # Will be set by caller
            extracted_expected_value=exp_normalized,
            extracted_agent_value=agent_normalized,
            numeric_difference_pct=numeric_diff,
            error_details=None
        )
    
    def _determine_match_level(
        self,
        expected_str: str,
        agent_str: str,
        exp_norm: Optional[float],
        agent_norm: Optional[float],
        exp_value: Optional[float],
        agent_value: Optional[float],
        exp_unit: Optional[str],
        agent_unit: Optional[str]
    ) -> MatchLevel:
        """Determine the match level between expected and agent answers."""
        
        # Check for exact string match
        if expected_str.strip().lower() == agent_str.strip().lower():
            return MatchLevel.EXACT_MATCH
        
        # Check for no answer
        if not agent_str or agent_str.lower() in ["i don't know", "unable to answer", "error"]:
            return MatchLevel.NO_ANSWER
        
        # For non-numeric answers (e.g., Yes/No)
        if exp_norm is None or agent_norm is None:
            exp_lower = expected_str.lower().strip()
            agent_lower = agent_str.lower().strip()
            
            # Check Yes/No questions
            if exp_lower in ["yes", "no"]:
                if exp_lower in agent_lower[:20]:  # Check beginning of answer
                    return MatchLevel.EXACT_MATCH
                else:
                    return MatchLevel.HALLUCINATION
            
            # Check if expected is contained in agent answer
            if len(exp_lower) > 5 and exp_lower in agent_lower:
                return MatchLevel.PARTIAL_CORRECT
            
            return MatchLevel.HALLUCINATION
        
        # For numeric answers
        if exp_norm == agent_norm:
            return MatchLevel.NUMERIC_EQUIV
        
        # Calculate percentage difference
        if exp_norm != 0:
            diff_pct = abs(exp_norm - agent_norm) / abs(exp_norm) * 100
        else:
            diff_pct = float('inf')
        
        # Check tolerance levels
        if diff_pct < 0.01:  # Less than 0.01% difference
            return MatchLevel.NUMERIC_EQUIV
        elif diff_pct <= 2:
            return MatchLevel.TOLERANCE_2PCT
        elif diff_pct <= 5:
            return MatchLevel.TOLERANCE_5PCT
        
        # Check if it's a scale error (off by factor of 1000, 1M, etc)
        scale_factors = [1000, 1000000, 1000000000]
        for factor in scale_factors:
            if (abs(exp_norm - agent_norm * factor) / abs(exp_norm) < 0.01 or
                abs(exp_norm * factor - agent_norm) / abs(agent_norm if agent_norm != 0 else 1) < 0.01):
                return MatchLevel.CORRECT_SCALE
        
        # Check if the raw values match but units are wrong
        if exp_value is not None and agent_value is not None:
            if abs(exp_value - agent_value) / max(abs(exp_value), 0.01) < 0.01:
                return MatchLevel.CORRECT_SCALE
        
        # If values are somewhat close (within 50%), consider it partial
        if diff_pct <= 50:
            return MatchLevel.PARTIAL_CORRECT
        
        return MatchLevel.HALLUCINATION

def categorize_question(question: str) -> str:
    """Categorize question type for analysis."""
    question_lower = question.lower()
    
    if any(term in question_lower for term in ['calculate', 'compute', 'what is % of', 'growth rate']):
        return 'calculation'
    elif any(term in question_lower for term in ['revenue', 'income', 'profit', 'assets', 'eps', 'margin', 'ebitda']):
        return 'financial_metric'
    elif any(term in question_lower for term in ['risk', 'strategy', 'describe', 'what are', 'how does']):
        return 'narrative'
    elif any(term in question_lower for term in ['yes', 'no', 'is ', 'are ', 'does ', 'did ']):
        return 'yes_no'
    else:
        return 'other'

@app.function(timeout=1800)
def evaluate_with_hierarchy(test_size: int = 30, save_detailed: bool = True):
    """Run evaluation with hierarchical metrics.
    
    Args:
        test_size: Number of questions to test
        save_detailed: Whether to save detailed results to file
    """
    # Load dataset
    dataset = load_dataset("AfterQuery/FinanceQA", split="test")
    
    # Sample questions
    import random
    indices = random.sample(range(len(dataset)), min(test_size, len(dataset)))
    
    # Get deployed function
    process_question = modal.Function.from_name("finance-agent-v4-new", "process_question_v4")
    
    # Initialize evaluator
    evaluator = MultiFacetedEvaluator()
    
    # Track results
    all_results: List[EvaluationResult] = []
    
    # Statistics by match level
    stats = {level: 0 for level in MatchLevel}
    category_stats = {}
    
    print("="*80)
    print("MULTI-FACETED EVALUATION FRAMEWORK")
    print(f"Testing {test_size} questions with hierarchical metrics")
    print("="*80)
    print()
    
    for idx, i in enumerate(indices):
        row = dataset[i]
        question = row["question"]
        expected = row["answer"]
        
        # Categorize question
        category = categorize_question(question)
        if category not in category_stats:
            category_stats[category] = {level: 0 for level in MatchLevel}
        
        try:
            start_time = time.time()
            
            # Call agent
            agent_answer = process_question.remote(question)
            
            elapsed = time.time() - start_time
            
            # Evaluate answer
            result = evaluator.evaluate_answer(expected, agent_answer, question)
            result.question_id = i
            result.category = category
            result.response_time = elapsed
            
            all_results.append(result)
            stats[result.match_level] += 1
            category_stats[category][result.match_level] += 1
            
            # Print progress
            print(f"[{idx+1}/{test_size}] Question #{i}")
            print(f"Category: {category.upper()}")
            print(f"Q: {question[:100]}...")
            print(f"Expected: {expected}")
            print(f"Got: {agent_answer[:200]}..." if len(agent_answer) > 200 else f"Got: {agent_answer}")
            print(f"Match Level: {result.match_level.value}")
            
            if result.numeric_difference_pct is not None:
                print(f"Numeric Difference: {result.numeric_difference_pct:.2f}%")
                if result.extracted_expected_value and result.extracted_agent_value:
                    print(f"Values: {result.extracted_expected_value:,.2f} vs {result.extracted_agent_value:,.2f}")
            
            print(f"Time: {elapsed:.1f}s")
            print("-"*60)
            print()
            
            # Rate limit handling
            if (idx + 1) % 5 == 0:
                time.sleep(2)
                
        except Exception as e:
            # Record error
            result = EvaluationResult(
                question_id=i,
                question=question[:200],
                expected_answer=expected,
                agent_answer="",
                match_level=MatchLevel.ERROR,
                category=category,
                response_time=0,
                extracted_expected_value=None,
                extracted_agent_value=None,
                numeric_difference_pct=None,
                error_details=str(e)[:500]
            )
            all_results.append(result)
            stats[MatchLevel.ERROR] += 1
            category_stats[category][MatchLevel.ERROR] += 1
            
            print(f"[{idx+1}/{test_size}] ERROR on Question #{i}")
            print(f"Error: {str(e)[:200]}")
            print("-"*60)
            print()
            
            if "rate_limit" in str(e).lower():
                print("Waiting 30 seconds for rate limit...")
                time.sleep(30)
    
    # Calculate aggregate metrics
    total = len(all_results)
    
    # Define success tiers
    success_strict = sum(stats[level] for level in [MatchLevel.EXACT_MATCH, MatchLevel.NUMERIC_EQUIV])
    success_2pct = success_strict + stats[MatchLevel.TOLERANCE_2PCT]
    success_5pct = success_2pct + stats[MatchLevel.TOLERANCE_5PCT]
    success_scale = success_5pct + stats[MatchLevel.CORRECT_SCALE]
    
    # Print summary
    print("="*80)
    print("EVALUATION SUMMARY")
    print("="*80)
    print(f"Total Questions: {total}")
    print()
    
    print("ACCURACY TIERS:")
    print(f"  Strict (Exact + Numeric Equiv):     {success_strict}/{total} = {success_strict/total*100:.1f}%")
    print(f"  With 2% Tolerance:                   {success_2pct}/{total} = {success_2pct/total*100:.1f}%")
    print(f"  With 5% Tolerance:                   {success_5pct}/{total} = {success_5pct/total*100:.1f}%")
    print(f"  Including Scale Errors:              {success_scale}/{total} = {success_scale/total*100:.1f}%")
    print()
    
    print("DETAILED BREAKDOWN:")
    for level in MatchLevel:
        count = stats[level]
        if count > 0:
            print(f"  {level.value:30} {count:3d} ({count/total*100:5.1f}%)")
    print()
    
    print("PERFORMANCE BY CATEGORY:")
    for category, cat_stats in category_stats.items():
        cat_total = sum(cat_stats.values())
        if cat_total > 0:
            cat_success = sum(cat_stats[level] for level in 
                            [MatchLevel.EXACT_MATCH, MatchLevel.NUMERIC_EQUIV, MatchLevel.TOLERANCE_2PCT])
            print(f"  {category.upper():20} Total: {cat_total:3d}, Success: {cat_success:3d} ({cat_success/cat_total*100:.1f}%)")
    
    # Analyze common error patterns
    print()
    print("ERROR ANALYSIS:")
    
    # Scale errors
    scale_errors = [r for r in all_results if r.match_level == MatchLevel.CORRECT_SCALE]
    if scale_errors:
        print(f"  Scale/Unit Errors: {len(scale_errors)} questions")
        for err in scale_errors[:3]:  # Show first 3 examples
            print(f"    - Q{err.question_id}: Expected {err.extracted_expected_value:,.2f}, Got {err.extracted_agent_value:,.2f}")
    
    # Large deviations
    large_deviations = [r for r in all_results 
                       if r.numeric_difference_pct and r.numeric_difference_pct > 50]
    if large_deviations:
        print(f"  Large Deviations (>50%): {len(large_deviations)} questions")
    
    # No answers
    no_answers = [r for r in all_results if r.match_level == MatchLevel.NO_ANSWER]
    if no_answers:
        print(f"  No Answer Provided: {len(no_answers)} questions")
    
    # Save detailed results if requested
    if save_detailed:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"evaluation_multifaceted_{timestamp}.json"
        
        results_dict = {
            "metadata": {
                "timestamp": timestamp,
                "test_size": test_size,
                "total_questions": total
            },
            "summary": {
                "accuracy_strict": success_strict/total*100,
                "accuracy_2pct": success_2pct/total*100,
                "accuracy_5pct": success_5pct/total*100,
                "accuracy_with_scale": success_scale/total*100
            },
            "match_level_counts": {level.value: stats[level] for level in MatchLevel},
            "category_performance": {
                cat: {
                    "total": sum(cat_stats.values()),
                    "success_2pct": sum(cat_stats[level] for level in 
                                      [MatchLevel.EXACT_MATCH, MatchLevel.NUMERIC_EQUIV, MatchLevel.TOLERANCE_2PCT])
                }
                for cat, cat_stats in category_stats.items()
            },
            "detailed_results": [r.to_dict() for r in all_results]
        }
        
        with open(f"/tmp/{filename}", "w") as f:
            json.dump(results_dict, f, indent=2)
        
        print(f"\nDetailed results saved to: {filename}")
    
    print("="*80)
    
    return {
        "total": total,
        "success_strict": success_strict,
        "success_2pct": success_2pct,
        "success_5pct": success_5pct,
        "stats": stats,
        "category_stats": category_stats
    }

# Local entrypoint
@app.local_entrypoint()
def main(test_size: int = 30, save_detailed: bool = True):
    """Run multi-faceted evaluation.
    
    Args:
        test_size: Number of questions to test (default: 30)
        save_detailed: Save detailed results to JSON file (default: True)
    """
    results = evaluate_with_hierarchy.remote(test_size, save_detailed)
    
    print(f"\nEvaluation complete!")
    print(f"Strict accuracy: {results['success_strict']/results['total']*100:.1f}%")
    print(f"With 2% tolerance: {results['success_2pct']/results['total']*100:.1f}%")
