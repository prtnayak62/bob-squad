#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build History Tracker
Tracks failed builds and accumulated issues across commits
"""

import argparse
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class BuildHistoryTracker:
    """Tracks build history and accumulated issues"""
    
    def __init__(self, history_file: str = "build-history.json"):
        self.history_file = history_file
        self.history = self.load_history()
    
    def load_history(self) -> Dict[str, Any]:
        """Load build history from file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Warning: Could not load history: {e}")
                return self.create_empty_history()
        return self.create_empty_history()
    
    def create_empty_history(self) -> Dict[str, Any]:
        """Create empty history structure"""
        return {
            "builds": [],
            "unresolved_issues": {},
            "last_successful_commit": None,
            "consecutive_failures": 0
        }
    
    def save_history(self):
        """Save history to file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2)
            print(f"✅ History saved to {self.history_file}")
        except Exception as e:
            print(f"❌ Error saving history: {e}")
    
    def add_build(self, commit: str, author: str, status: str, 
                  review_data: Dict[str, Any], gate_data: Dict[str, Any]):
        """Add a new build to history"""
        build_record = {
            "commit": commit,
            "author": author,
            "timestamp": datetime.utcnow().isoformat(),
            "status": status,
            "scores": review_data.get('scores', {}),
            "issues": review_data.get('issues', []),
            "quality_gate": gate_data.get('status', 'UNKNOWN')
        }
        
        self.history["builds"].append(build_record)
        
        # Update consecutive failures
        if status == "FAILED":
            self.history["consecutive_failures"] += 1
        else:
            self.history["consecutive_failures"] = 0
            self.history["last_successful_commit"] = commit
        
        # Track unresolved issues
        self.update_unresolved_issues(commit, review_data.get('issues', []), status)
        
        # Keep only last 50 builds
        if len(self.history["builds"]) > 50:
            self.history["builds"] = self.history["builds"][-50:]
        
        self.save_history()
    
    def update_unresolved_issues(self, commit: str, issues: List[Dict], status: str):
        """Track issues that haven't been resolved"""
        if status == "FAILED":
            self._add_failed_build_issues(commit, issues)
        else:
            self._resolve_fixed_issues(commit, issues)
    
    def _add_failed_build_issues(self, commit: str, issues: List[Dict]):
        """Add new issues from failed build"""
        for issue in issues:
            issue_key = self._create_issue_key(issue)
            if issue_key not in self.history["unresolved_issues"]:
                self.history["unresolved_issues"][issue_key] = {
                    "first_seen": commit,
                    "last_seen": commit,
                    "occurrences": 1,
                    "issue": issue,
                    "status": "UNRESOLVED"
                }
            else:
                self.history["unresolved_issues"][issue_key]["last_seen"] = commit
                self.history["unresolved_issues"][issue_key]["occurrences"] += 1
    
    def _resolve_fixed_issues(self, commit: str, issues: List[Dict]):
        """Remove issues that have been fixed in reviewed files"""
        reviewed_files = {issue.get('file', 'unknown') for issue in issues}
        resolved_keys = []
        
        for issue_key, data in self.history["unresolved_issues"].items():
            issue_file = data["issue"].get('file', 'unknown')
            
            # Only check files that were reviewed in this commit
            if issue_file in reviewed_files:
                if not self._issue_still_exists(issue_key, issues):
                    resolved_keys.append(issue_key)
                    print(f"✅ Resolved issue in {issue_file}")
        
        # Remove resolved issues
        for key in resolved_keys:
            del self.history["unresolved_issues"][key]
    
    def _create_issue_key(self, issue: Dict) -> str:
        """Create unique key for an issue"""
        return f"{issue.get('file', 'unknown')}:{issue.get('line', 0)}:{issue.get('message', '')[:50]}"
    
    def _issue_still_exists(self, issue_key: str, current_issues: List[Dict]) -> bool:
        """Check if an issue still exists in current issues"""
        for current_issue in current_issues:
            current_key = self._create_issue_key(current_issue)
            if current_key == issue_key:
                return True
        return False
    
    def get_unresolved_issues(self) -> List[Dict[str, Any]]:
        """Get all unresolved issues"""
        issues = []
        for issue_key, data in self.history["unresolved_issues"].items():
            issue = data["issue"].copy()
            issue["first_seen_commit"] = data["first_seen"]
            issue["last_seen_commit"] = data["last_seen"]
            issue["occurrences"] = data["occurrences"]
            issues.append(issue)
        return issues
    
    def get_build_trend(self, last_n: int = 10) -> Dict[str, Any]:
        """Get build trend for last N builds"""
        recent_builds = self.history["builds"][-last_n:]
        
        if not recent_builds:
            return {
                "total_builds": 0,
                "passed": 0,
                "failed": 0,
                "success_rate": 0,
                "average_score": 0
            }
        
        passed = sum(1 for b in recent_builds if b["status"] != "FAILED")
        failed = len(recent_builds) - passed
        
        total_score = 0
        score_count = 0
        for build in recent_builds:
            if build.get("scores", {}).get("overall"):
                total_score += build["scores"]["overall"]
                score_count += 1
        
        avg_score = total_score / score_count if score_count > 0 else 0
        
        return {
            "total_builds": len(recent_builds),
            "passed": passed,
            "failed": failed,
            "success_rate": (passed / len(recent_builds)) * 100,
            "average_score": round(avg_score, 1),
            "consecutive_failures": self.history["consecutive_failures"]
        }
    
    def should_block_build(self) -> tuple[bool, str]:
        """Determine if build should be blocked based on history"""
        # Block if there are ANY unresolved issues from previous failed builds
        unresolved = self.get_unresolved_issues()
        
        if unresolved:
            critical_issues = [i for i in unresolved if i.get('severity') == 'CRITICAL']
            high_issues = [i for i in unresolved if i.get('severity') == 'HIGH']
            
            if critical_issues:
                return True, f"Build blocked: {len(critical_issues)} CRITICAL unresolved issues from previous commits must be fixed first"
            
            if high_issues:
                return True, f"Build blocked: {len(high_issues)} HIGH severity unresolved issues from previous commits must be fixed first"
            
            # For medium/low issues, warn but don't block
            if len(unresolved) > 0:
                return True, f"Build blocked: {len(unresolved)} unresolved issues from previous failed builds must be addressed"
        
        # Block if too many consecutive failures
        if self.history["consecutive_failures"] >= 3:
            return True, f"Build blocked: {self.history['consecutive_failures']} consecutive failures - fix issues before proceeding"
        
        return False, ""
    
    def generate_history_report(self) -> Dict[str, Any]:
        """Generate comprehensive history report"""
        return {
            "summary": {
                "total_builds": len(self.history["builds"]),
                "last_successful_commit": self.history["last_successful_commit"],
                "consecutive_failures": self.history["consecutive_failures"],
                "unresolved_issues_count": len(self.history["unresolved_issues"])
            },
            "unresolved_issues": self.get_unresolved_issues(),
            "build_trend": self.get_build_trend(10),
            "recent_builds": self.history["builds"][-10:]
        }


def main():
    parser = argparse.ArgumentParser(description="Build History Tracker")
    parser.add_argument("--action", required=True, 
                       choices=['add', 'check', 'report', 'clear'],
                       help="Action to perform")
    parser.add_argument("--commit", help="Git commit hash")
    parser.add_argument("--author", help="Commit author")
    parser.add_argument("--status", choices=['PASSED', 'FAILED', 'WARNING'],
                       help="Build status")
    parser.add_argument("--review-file", help="Review report JSON file")
    parser.add_argument("--quality-gate-file", help="Quality gate result JSON file")
    parser.add_argument("--output-file", default="history-report.json",
                       help="Output file for report")
    
    args = parser.parse_args()
    
    tracker = BuildHistoryTracker()
    
    if args.action == 'add':
        # Add new build to history
        if not all([args.commit, args.author, args.status, args.review_file, args.quality_gate_file]):
            print("❌ Error: --commit, --author, --status, --review-file, and --quality-gate-file required for 'add' action")
            return 1
        
        try:
            with open(args.review_file, 'r', encoding='utf-8') as f:
                review_data = json.load(f)
            with open(args.quality_gate_file, 'r', encoding='utf-8') as f:
                gate_data = json.load(f)
        except Exception as e:
            print(f"❌ Error loading files: {e}")
            return 1
        
        tracker.add_build(args.commit, args.author, args.status, review_data, gate_data)
        print(f"✅ Build {args.commit} added to history with status: {args.status}")
        
        # Show unresolved issues
        unresolved = tracker.get_unresolved_issues()
        if unresolved:
            print(f"\n⚠️ {len(unresolved)} unresolved issues from previous commits:")
            for issue in unresolved[:5]:  # Show first 5
                file_name = issue.get('file', 'unknown')
                message = issue.get('message', 'No message')
                message_preview = message[:60] if message else 'No message'
                print(f"  - {file_name}: {message_preview}...")
                print(f"    First seen: {issue.get('first_seen_commit')}, Occurrences: {issue.get('occurrences')}")
    
    elif args.action == 'check':
        # Check if build should be blocked
        should_block, reason = tracker.should_block_build()
        
        if should_block:
            print(f"❌ {reason}")
            return 1
        else:
            print("✅ Build can proceed")
            
            # Show warnings if any
            unresolved = tracker.get_unresolved_issues()
            if unresolved:
                print(f"\n⚠️ Warning: {len(unresolved)} unresolved issues from previous commits")
            
            return 0
    
    elif args.action == 'report':
        # Generate history report
        report = tracker.generate_history_report()
        
        with open(args.output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ History report generated: {args.output_file}")
        print(f"\nSummary:")
        print(f"  Total builds: {report['summary']['total_builds']}")
        print(f"  Consecutive failures: {report['summary']['consecutive_failures']}")
        print(f"  Unresolved issues: {report['summary']['unresolved_issues_count']}")
        print(f"  Build trend (last 10): {report['build_trend']['success_rate']:.1f}% success rate")
    
    elif args.action == 'clear':
        # Clear history
        tracker.history = tracker.create_empty_history()
        tracker.save_history()
        print("✅ Build history cleared")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
