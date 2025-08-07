"""
Analyze and visualize multi-faceted evaluation results.
Creates reports and insights from the hierarchical evaluation metrics.
"""

import json
import os
from typing import Dict, List, Any
from dataclasses import dataclass
import pandas as pd
from pathlib import Path

@dataclass
class ErrorPattern:
    """Represents a common error pattern."""
    pattern_type: str
    frequency: int
    examples: List[Dict]
    severity: str  # 'high', 'medium', 'low'
    suggested_fix: str

class EvaluationAnalyzer:
    """Analyze evaluation results to identify patterns and insights."""
    
    def __init__(self, results_file: str = None):
        """Initialize analyzer with results file."""
        self.results = None
        if results_file:
            self.load_results(results_file)
    
    def load_results(self, filepath: str):
        """Load evaluation results from JSON file."""
        with open(filepath, 'r') as f:
            self.results = json.load(f)
    
    def generate_report(self) -> str:
        """Generate a comprehensive markdown report."""
        if not self.results:
            raise ValueError("No results loaded. Please load results first.")
        
        report = []
        report.append("# Multi-Faceted Evaluation Report\n")
        report.append(f"**Generated:** {self.results['metadata']['timestamp']}\n")
        report.append(f"**Questions Tested:** {self.results['metadata']['total_questions']}\n\n")
        
        # Executive Summary
        report.append("## Executive Summary\n")
        report.append(self._generate_executive_summary())
        report.append("\n")
        
        # Accuracy Tiers
        report.append("## Accuracy Tiers\n")
        report.append(self._generate_accuracy_tiers())
        report.append("\n")
        
        # Performance by Category
        report.append("## Performance by Question Category\n")
        report.append(self._generate_category_performance())
        report.append("\n")
        
        # Error Patterns
        report.append("## Error Pattern Analysis\n")
        patterns = self._identify_error_patterns()
        report.append(self._format_error_patterns(patterns))
        report.append("\n")
        
        # Recommendations
        report.append("## Recommendations for Improvement\n")
        report.append(self._generate_recommendations(patterns))
        report.append("\n")
        
        # Detailed Match Level Breakdown
        report.append("## Detailed Match Level Distribution\n")
        report.append(self._generate_match_level_table())
        
        return "".join(report)
    
    def _generate_executive_summary(self) -> str:
        """Generate executive summary section."""
        summary = self.results['summary']
        
        text = []
        
        # Determine overall performance level
        strict_acc = summary['accuracy_strict']
        acc_2pct = summary['accuracy_2pct']
        
        if strict_acc >= 60:
            performance = "**Excellent**"
            color = "🟢"
        elif strict_acc >= 40:
            performance = "**Good**"
            color = "🟡"
        elif strict_acc >= 20:
            performance = "**Moderate**"
            color = "🟠"
        else:
            performance = "**Needs Improvement**"
            color = "🔴"
        
        text.append(f"### Overall Performance: {color} {performance}\n\n")
        
        # Key metrics
        text.append("**Key Metrics:**\n")
        text.append(f"- **Strict Accuracy:** {strict_acc:.1f}% (exact matches + numeric equivalents)\n")
        text.append(f"- **Practical Accuracy (2% tolerance):** {acc_2pct:.1f}%\n")
        text.append(f"- **Improvement with tolerance:** +{acc_2pct - strict_acc:.1f} percentage points\n")
        
        # Insights
        if acc_2pct - strict_acc > 20:
            text.append("\n⚠️ **Alert:** Large gap between strict and tolerant accuracy suggests formatting issues.\n")
        
        if summary.get('accuracy_with_scale', 0) - acc_2pct > 10:
            text.append("\n⚠️ **Alert:** Significant scale/unit errors detected. Agent struggles with millions/billions.\n")
        
        return "".join(text)
    
    def _generate_accuracy_tiers(self) -> str:
        """Generate accuracy tiers table."""
        summary = self.results['summary']
        
        table = []
        table.append("| Accuracy Level | Percentage | Description |\n")
        table.append("|----------------|------------|-------------|\n")
        table.append(f"| **Strict** | {summary['accuracy_strict']:.1f}% | Exact matches only |\n")
        table.append(f"| **2% Tolerance** | {summary['accuracy_2pct']:.1f}% | Acceptable for most financial reporting |\n")
        table.append(f"| **5% Tolerance** | {summary['accuracy_5pct']:.1f}% | May be acceptable for estimates |\n")
        table.append(f"| **With Scale Errors** | {summary['accuracy_with_scale']:.1f}% | Correct values, wrong units |\n")
        
        return "".join(table)
    
    def _generate_category_performance(self) -> str:
        """Generate performance by category."""
        cat_perf = self.results['category_performance']
        
        # Convert to DataFrame for easier manipulation
        data = []
        for category, stats in cat_perf.items():
            total = stats['total']
            success = stats['success_2pct']
            accuracy = (success / total * 100) if total > 0 else 0
            data.append({
                'Category': category.upper(),
                'Questions': total,
                'Correct (2% tol)': success,
                'Accuracy': f"{accuracy:.1f}%"
            })
        
        # Sort by accuracy
        data.sort(key=lambda x: float(x['Accuracy'].rstrip('%')), reverse=True)
        
        table = []
        table.append("| Category | Questions | Correct | Accuracy |\n")
        table.append("|----------|-----------|---------|----------|\n")
        
        for row in data:
            # Add emoji based on performance
            acc_val = float(row['Accuracy'].rstrip('%'))
            if acc_val >= 70:
                emoji = "✅"
            elif acc_val >= 50:
                emoji = "⚠️"
            else:
                emoji = "❌"
            
            table.append(f"| {row['Category']} | {row['Questions']} | {row['Correct (2% tol)']} | {emoji} {row['Accuracy']} |\n")
        
        return "".join(table)
    
    def _identify_error_patterns(self) -> List[ErrorPattern]:
        """Identify common error patterns from detailed results."""
        patterns = []
        
        if 'detailed_results' not in self.results:
            return patterns
        
        detailed = self.results['detailed_results']
        
        # Pattern 1: Scale/Unit Errors
        scale_errors = [r for r in detailed if r['match_level'] == 'correct_scale_wrong_unit']
        if scale_errors:
            patterns.append(ErrorPattern(
                pattern_type="Scale/Unit Confusion",
                frequency=len(scale_errors),
                examples=scale_errors[:3],
                severity="high",
                suggested_fix="Implement explicit unit detection and conversion logic. Train on more examples with explicit unit specifications."
            ))
        
        # Pattern 2: Large Numeric Deviations
        large_devs = [r for r in detailed 
                     if r.get('numeric_difference_pct') and r['numeric_difference_pct'] > 50]
        if large_devs:
            patterns.append(ErrorPattern(
                pattern_type="Large Numeric Deviations (>50%)",
                frequency=len(large_devs),
                examples=large_devs[:3],
                severity="high",
                suggested_fix="Review calculation logic and ensure proper data source selection. May need better context understanding."
            ))
        
        # Pattern 3: No Answer Provided
        no_answers = [r for r in detailed if r['match_level'] == 'no_answer']
        if no_answers:
            patterns.append(ErrorPattern(
                pattern_type="Unable to Answer",
                frequency=len(no_answers),
                examples=no_answers[:3],
                severity="medium",
                suggested_fix="Expand knowledge base or improve fallback strategies for handling unknown queries."
            ))
        
        # Pattern 4: Hallucinations
        hallucinations = [r for r in detailed if r['match_level'] == 'hallucination']
        if hallucinations:
            patterns.append(ErrorPattern(
                pattern_type="Hallucinated Answers",
                frequency=len(hallucinations),
                examples=hallucinations[:3],
                severity="high",
                suggested_fix="Implement stricter validation and confidence scoring. Consider adding 'I don't know' responses for uncertain cases."
            ))
        
        # Pattern 5: Small but consistent errors (2-5%)
        small_errors = [r for r in detailed if r['match_level'] == 'tolerance_5pct']
        if len(small_errors) > 5:
            patterns.append(ErrorPattern(
                pattern_type="Consistent Small Errors (2-5%)",
                frequency=len(small_errors),
                examples=small_errors[:3],
                severity="low",
                suggested_fix="May be due to rounding differences or slightly different calculation methods. Generally acceptable."
            ))
        
        return patterns
    
    def _format_error_patterns(self, patterns: List[ErrorPattern]) -> str:
        """Format error patterns for the report."""
        if not patterns:
            return "No significant error patterns detected. ✅\n"
        
        text = []
        
        # Sort by severity and frequency
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        patterns.sort(key=lambda x: (severity_order[x.severity], -x.frequency))
        
        for pattern in patterns:
            severity_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}[pattern.severity]
            
            text.append(f"### {severity_emoji} {pattern.pattern_type}\n")
            text.append(f"- **Frequency:** {pattern.frequency} occurrences\n")
            text.append(f"- **Severity:** {pattern.severity.upper()}\n")
            text.append(f"- **Suggested Fix:** {pattern.suggested_fix}\n")
            
            if pattern.examples:
                text.append("- **Examples:**\n")
                for i, ex in enumerate(pattern.examples[:2], 1):
                    text.append(f"  {i}. Question: {ex['question'][:80]}...\n")
                    text.append(f"     Expected: {ex['expected_answer']}\n")
                    text.append(f"     Got: {ex['agent_answer'][:100]}...\n")
            
            text.append("\n")
        
        return "".join(text)
    
    def _generate_recommendations(self, patterns: List[ErrorPattern]) -> str:
        """Generate prioritized recommendations based on patterns."""
        text = []
        
        # Count high severity issues
        high_severity = [p for p in patterns if p.severity == 'high']
        
        if high_severity:
            text.append("### 🚨 Priority 1: Critical Issues\n")
            for pattern in high_severity:
                text.append(f"- **{pattern.pattern_type}:** {pattern.suggested_fix}\n")
            text.append("\n")
        
        text.append("### 📋 General Recommendations\n")
        
        # Based on accuracy gaps
        summary = self.results['summary']
        
        if summary['accuracy_2pct'] - summary['accuracy_strict'] > 20:
            text.append("1. **Improve Output Formatting:** Large gap between strict and tolerant accuracy indicates formatting inconsistencies.\n")
        
        if summary['accuracy_with_scale'] - summary['accuracy_2pct'] > 10:
            text.append("2. **Fix Unit Handling:** Implement robust unit detection and conversion (millions, billions, percentages).\n")
        
        # Category-specific recommendations
        cat_perf = self.results['category_performance']
        weak_categories = [(cat, stats) for cat, stats in cat_perf.items() 
                          if stats['total'] > 0 and (stats['success_2pct'] / stats['total']) < 0.5]
        
        if weak_categories:
            text.append(f"3. **Improve Weak Categories:** Focus on {', '.join([cat.upper() for cat, _ in weak_categories])} questions.\n")
        
        text.append("4. **Add Confidence Scoring:** Implement confidence thresholds to avoid hallucinations.\n")
        text.append("5. **Expand Test Coverage:** Test with more diverse question types and edge cases.\n")
        
        return "".join(text)
    
    def _generate_match_level_table(self) -> str:
        """Generate detailed match level distribution table."""
        counts = self.results['match_level_counts']
        total = self.results['metadata']['total_questions']
        
        table = []
        table.append("| Match Level | Count | Percentage | Description |\n")
        table.append("|-------------|-------|------------|-------------|\n")
        
        # Define order and descriptions
        level_info = {
            'exact_match': ('Exact Match', '✅', 'Perfect match'),
            'numeric_equivalent': ('Numeric Equivalent', '✅', 'Same value, different format'),
            'tolerance_2pct': ('2% Tolerance', '👍', 'Within acceptable tolerance'),
            'tolerance_5pct': ('5% Tolerance', '⚠️', 'Slightly off'),
            'correct_scale_wrong_unit': ('Scale Error', '⚠️', 'Right value, wrong unit'),
            'partial_correct': ('Partial', '❓', 'Some correct information'),
            'hallucination': ('Hallucination', '❌', 'Incorrect answer'),
            'no_answer': ('No Answer', '❌', 'Unable to answer'),
            'error': ('Error', '💥', 'Technical failure')
        }
        
        for level_key, (level_name, emoji, desc) in level_info.items():
            count = counts.get(level_key, 0)
            if count > 0:
                pct = count / total * 100
                table.append(f"| {emoji} {level_name} | {count} | {pct:.1f}% | {desc} |\n")
        
        return "".join(table)
    
    def save_report(self, output_path: str = None):
        """Save the report to a markdown file."""
        if output_path is None:
            # Generate filename based on timestamp
            timestamp = self.results['metadata']['timestamp']
            output_path = f"evaluation_report_{timestamp}.md"
        
        report = self.generate_report()
        
        with open(output_path, 'w') as f:
            f.write(report)
        
        print(f"Report saved to: {output_path}")
        return output_path

def find_latest_results(directory: str = ".") -> str:
    """Find the most recent evaluation results file."""
    import glob
    
    pattern = os.path.join(directory, "evaluation_multifaceted_*.json")
    files = glob.glob(pattern)
    
    if not files:
        # Also check /tmp directory
        pattern = "/tmp/evaluation_multifaceted_*.json"
        files = glob.glob(pattern)
    
    if not files:
        raise FileNotFoundError("No evaluation results found. Please run evaluate_multifaceted.py first.")
    
    # Get the most recent file
    latest = max(files, key=os.path.getctime)
    return latest

def main():
    """Main entry point for analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze multi-faceted evaluation results")
    parser.add_argument("--results-file", type=str, help="Path to results JSON file")
    parser.add_argument("--output", type=str, help="Output path for report")
    parser.add_argument("--latest", action="store_true", help="Use latest results file")
    
    args = parser.parse_args()
    
    # Determine which results file to use
    if args.results_file:
        results_file = args.results_file
    elif args.latest:
        try:
            results_file = find_latest_results()
            print(f"Using latest results: {results_file}")
        except FileNotFoundError as e:
            print(str(e))
            return
    else:
        print("Please specify --results-file or use --latest flag")
        return
    
    # Analyze results
    analyzer = EvaluationAnalyzer(results_file)
    
    # Generate and save report
    output_path = analyzer.save_report(args.output)
    
    # Print summary to console
    print("\n" + "="*60)
    print("EVALUATION ANALYSIS COMPLETE")
    print("="*60)
    
    summary = analyzer.results['summary']
    print(f"Strict Accuracy: {summary['accuracy_strict']:.1f}%")
    print(f"With 2% Tolerance: {summary['accuracy_2pct']:.1f}%")
    print(f"Report saved to: {output_path}")

if __name__ == "__main__":
    main()
