#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quality Gate Evaluation Script
Evaluates code review scores against defined thresholds
"""

import argparse
import json
import sys
import os
from typing import Dict, List, Any
from datetime import datetime

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class QualityGate:
    """Evaluates quality metrics against thresholds"""
    
    def __init__(self, thresholds: Dict[str, int]):
        self.thresholds = thresholds
        self.failed_criteria = []
        self.warning_criteria = []
        self.passed_criteria = []
    
    def evaluate(self, scores: Dict[str, int]) -> Dict[str, Any]:
        """Evaluate scores against thresholds"""
        results = self._initialize_results(scores)
        
        # Evaluate each metric
        for metric, score in scores.items():
            self._evaluate_metric(results, metric, score)
        
        # Determine overall status
        self._set_overall_status(results)
        return results
    
    def _initialize_results(self, scores: Dict[str, int]) -> Dict[str, Any]:
        """Initialize results structure"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "PASSED",
            "message": "",
            "scores": scores,
            "thresholds": self.thresholds,
            "failed_criteria": [],
            "warning_criteria": [],
            "passed_criteria": [],
            "details": {}
        }
    
    def _evaluate_metric(self, results: Dict[str, Any], metric: str, score: int):
        """Evaluate a single metric against threshold"""
        threshold = self.thresholds.get(metric, 0)
        criterion = f"{metric}: {score}/100 (threshold: {threshold}/100"
        
        if score < threshold:
            diff = threshold - score
            results["failed_criteria"].append(f"{criterion}, deficit: {diff})")
            results["details"][metric] = {
                "status": "FAILED", "score": score, "threshold": threshold, "deficit": diff
            }
        elif score < threshold + 10:
            margin = score - threshold
            results["warning_criteria"].append(f"{criterion}, margin: {margin})")
            results["details"][metric] = {
                "status": "WARNING", "score": score, "threshold": threshold, "margin": margin
            }
        else:
            margin = score - threshold
            results["passed_criteria"].append(f"{criterion}, margin: {margin})")
            results["details"][metric] = {
                "status": "PASSED", "score": score, "threshold": threshold, "margin": margin
            }
    
    def _set_overall_status(self, results: Dict[str, Any]):
        """Determine overall status based on criteria"""
        if results["failed_criteria"]:
            results["status"] = "FAILED"
            results["message"] = f"Quality Gate FAILED: {len(results['failed_criteria'])} criteria not met"
        elif results["warning_criteria"]:
            results["status"] = "WARNING"
            results["message"] = f"Quality Gate PASSED with warnings: {len(results['warning_criteria'])} criteria close to threshold"
        else:
            results["status"] = "PASSED"
            results["message"] = "Quality Gate PASSED: All criteria met"
    
    def print_summary(self, results: Dict[str, Any]):
        """Print evaluation summary"""
        self._print_header(results)
        self._print_metric_details(results["details"])
        self._print_criteria_lists(results)
        print("\n" + "="*70)
    
    def _print_header(self, results: Dict[str, Any]):
        """Print summary header with status"""
        print("\n" + "="*70)
        print("🚦 QUALITY GATE EVALUATION")
        print("="*70)
        
        status_emoji = {"PASSED": "✅", "WARNING": "⚠️", "FAILED": "❌"}
        print(f"\nStatus: {status_emoji.get(results['status'], '❓')} {results['status']}")
        print(f"Message: {results['message']}")
    
    def _print_metric_details(self, details: Dict[str, Any]):
        """Print detailed metrics"""
        print("\n" + "-"*70)
        print("METRIC DETAILS")
        print("-"*70)
        
        status_symbol = {"PASSED": "✅", "WARNING": "⚠️", "FAILED": "❌"}
        
        for metric, detail in details.items():
            metric_name = metric.replace('_', ' ').title()
            print(f"\n{status_symbol.get(detail['status'], '❓')} {metric_name}")
            print(f"   Score:     {detail['score']}/100")
            print(f"   Threshold: {detail['threshold']}/100")
            
            if detail['status'] == 'FAILED':
                print(f"   Deficit:   {detail['deficit']} points")
            else:
                print(f"   Margin:    {detail['margin']} points")
    
    def _print_criteria_lists(self, results: Dict[str, Any]):
        """Print criteria lists by status"""
        criteria_sections = [
            ("failed_criteria", "❌ FAILED CRITERIA"),
            ("warning_criteria", "⚠️  WARNING CRITERIA"),
            ("passed_criteria", "✅ PASSED CRITERIA")
        ]
        
        for key, title in criteria_sections:
            if results.get(key):
                print("\n" + "-"*70)
                print(title)
                print("-"*70)
                for criterion in results[key]:
                    print(f"  • {criterion}")


def main():
    parser = argparse.ArgumentParser(description="Quality Gate Evaluation")
    
    # Support both methods: reading from review file OR individual scores
    parser.add_argument("--review-file", help="Review report JSON file (preferred method)")
    parser.add_argument("--code-quality-score", type=int,
                       help="Code quality score (0-100)")
    parser.add_argument("--security-score", type=int,
                       help="Security score (0-100)")
    parser.add_argument("--maintainability-score", type=int,
                       help="Maintainability score (0-100)")
    parser.add_argument("--code-threshold", type=int, default=70,
                       help="Code quality threshold (default: 70)")
    parser.add_argument("--security-threshold", type=int, default=80,
                       help="Security threshold (default: 80)")
    parser.add_argument("--maintainability-threshold", type=int, default=75,
                       help="Maintainability threshold (default: 75)")
    parser.add_argument("--output-file", default="quality-gate-result.json",
                       help="Output file path")
    
    args = parser.parse_args()
    
    # Prepare scores - read from review file if provided, otherwise use individual scores
    if args.review_file:
        print(f"📖 Reading scores from review file: {args.review_file}")
        try:
            with open(args.review_file, 'r', encoding='utf-8') as f:
                review_data = json.load(f)
            
            scores = review_data.get('scores', {})
            print(f"✅ Loaded scores from review file")
            print(f"   Code Quality: {scores.get('code_quality', 0)}")
            print(f"   Security: {scores.get('security', 0)}")
            print(f"   Maintainability: {scores.get('maintainability', 0)}")
            print(f"   Overall: {scores.get('overall', 0)}")
            print(f"\n   DEBUG: Full review data scores: {review_data.get('scores', {})}")
        except Exception as e:
            print(f"❌ Error reading review file: {e}")
            print(f"   Falling back to command-line scores if provided")
            if not all([args.code_quality_score, args.security_score, args.maintainability_score]):
                print(f"❌ Error: No valid scores available")
                return 1
            scores = {
                "code_quality": args.code_quality_score,
                "security": args.security_score,
                "maintainability": args.maintainability_score
            }
    else:
        # Use individual scores from command line
        if not all([args.code_quality_score is not None,
                   args.security_score is not None,
                   args.maintainability_score is not None]):
            print("❌ Error: Either --review-file or all individual scores (--code-quality-score, --security-score, --maintainability-score) must be provided")
            return 1
        
        print(f"📊 Using scores from command-line arguments")
        scores = {
            "code_quality": args.code_quality_score,
            "security": args.security_score,
            "maintainability": args.maintainability_score
        }
    
    thresholds = {
        "code_quality": args.code_threshold,
        "security": args.security_threshold,
        "maintainability": args.maintainability_threshold
    }
    
    # Evaluate quality gate
    gate = QualityGate(thresholds)
    results = gate.evaluate(scores)
    
    # Print summary
    gate.print_summary(results)
    
    # Save results
    with open(args.output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {args.output_file}\n")
    
    # Return exit code based on status
    if results["status"] == "FAILED":
        return 1
    elif results["status"] == "WARNING":
        return 0  # Warning is not a failure
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
