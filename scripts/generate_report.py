#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline Report Generator - Jenkins Compatible
Creates HTML reports with simple visual elements that work in Jenkins
"""

import argparse
import html as html_mod   # GUARDRAIL: HTML-escape all untrusted content
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class ReportGenerator:
    """Generates HTML reports with simple charts from pipeline results"""
    
    def __init__(self):
        """Initialize report generator and load HTML template"""
        template_path = os.path.join(os.path.dirname(__file__), 'report_template.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            self.template = f.read()
    
    def get_score_class(self, score: int) -> str:
        """Determine CSS class based on score"""
        if score >= 85:
            return "score-excellent"
        elif score >= 70:
            return "score-good"
        elif score >= 50:
            return "score-warning"
        else:
            return "score-poor"
    
    def generate_score_rows(self, scores: Dict[str, int]) -> str:
        """Generate table rows for scores"""
        metrics = [
            ('Code Quality', scores.get('code_quality', 0)),
            ('Security', scores.get('security', 0)),
            ('Maintainability', scores.get('maintainability', 0)),
            ('Overall', scores.get('overall', 0))
        ]
        
        rows = ""
        for label, score in metrics:
            score_class = self.get_score_class(score)
            rows += f"""
                    <tr>
                        <td><strong>{label}</strong></td>
                        <td><strong>{score}/100</strong></td>
                        <td>
                            <div class="score-bar">
                                <div class="score-bar-fill {score_class}" style="width: {score}%;">
                                    {score}%
                                </div>
                            </div>
                        </td>
                    </tr>
"""
        return rows
    
    def generate_bar_chart(self, scores: Dict[str, int]) -> str:
        """Generate simple bar chart using table"""
        metrics = [
            ('Code Quality', scores.get('code_quality', 0)),
            ('Security', scores.get('security', 0)),
            ('Maintainability', scores.get('maintainability', 0)),
            ('Overall', scores.get('overall', 0))
        ]
        
        bars = ""
        for label, score in metrics:
            score_class = self.get_score_class(score)
            bars += f"""
                                <div class="bar-row">
                                    <div class="bar-label-cell">{label}</div>
                                    <div class="bar-cell">
                                        <div class="score-bar">
                                            <div class="score-bar-fill {score_class}" style="width: {score}%;">
                                                {score}
                                            </div>
                                        </div>
                                    </div>
                                </div>
"""
        return bars
    
    def generate_comparison_rows(self, scores: Dict[str, int], thresholds: Dict[str, int], details: Dict[str, Any]) -> str:
        """Generate comparison table rows"""
        metrics = [
            ('Code Quality', 'code_quality'),
            ('Security', 'security'),
            ('Maintainability', 'maintainability')
        ]
        
        rows = ""
        for label, key in metrics:
            score = scores.get(key, 0)
            threshold = thresholds.get(key, 0)
            detail = details.get(key, {}) if details else {}
            status = detail.get('status', 'UNKNOWN')
            
            if status == 'PASSED':
                status_icon = '✅'
                status_color = '#28a745'
            elif status == 'WARNING':
                status_icon = '⚠️'
                status_color = '#ffc107'
            else:
                status_icon = '❌'
                status_color = '#dc3545'
            
            rows += f"""
                                <tr>
                                    <td><strong>{label}</strong></td>
                                    <td><strong>{score}/100</strong></td>
                                    <td>{threshold}/100</td>
                                    <td style="color: {status_color}; font-weight: bold;">{status_icon} {status}</td>
                                </tr>
"""
        return rows
    
    def generate_issue_html(self, issue: Dict[str, Any]) -> str:
        """Generate HTML for an issue — all dynamic content is HTML-escaped (GUARDRAIL)."""
        severity = issue.get('severity', 'MEDIUM').upper()
        # Whitelist severity to a known safe value to prevent class injection
        if severity not in ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW'):
            severity = 'MEDIUM'
        severity_class = f"severity-{severity.lower()}"
        issue_class = f"issue-{severity.lower()}"

        # GUARDRAIL: escape all untrusted values before embedding in HTML
        safe_file    = html_mod.escape(str(issue.get('file', 'N/A')))
        safe_message = html_mod.escape(str(issue.get('message', 'No description')))
        safe_rec     = html_mod.escape(str(issue.get('recommendation', '')))

        result = f"""
                <li class="issue-item {issue_class}">
                    <div>
                        <span class="issue-severity {severity_class}">{severity}</span>
                        <span style="color: #667eea; font-family: monospace;">{safe_file}</span>
                    </div>
                    <div style="margin: 10px 0;">{safe_message}</div>
"""
        if safe_rec:
            result += f"""
                    <div style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin-top: 10px;">
                        <strong>Recommendation:</strong> {safe_rec}
                    </div>
"""
        result += "                </li>\n"
        return result
    
    def generate_report(self, review_data: Dict[str, Any], gate_data: Dict[str, Any],
                       commit: str, author: str, output_file: str):
        """Generate comprehensive HTML report"""
        
        # Extract and log data
        scores = review_data.get('scores', {})
        thresholds = gate_data.get('thresholds', {})
        details = gate_data.get('details', {})
        self._log_report_data(scores, gate_data, thresholds)
        
        # Generate all HTML components
        template_data = self._prepare_template_data(
            review_data, gate_data, scores, thresholds, details, commit, author
        )
        
        # Fill template and write file
        html = self.template.format(**template_data)
        self._write_report_file(output_file, html, scores, gate_data.get('status', 'UNKNOWN'))
    
    def _log_report_data(self, scores: Dict[str, int], gate_data: Dict[str, Any],
                         thresholds: Dict[str, int]):
        """Log report data for debugging"""
        print("\n" + "="*60)
        print("DEBUG: Data being used for report generation")
        print("="*60)
        print(f"Review data scores: {scores}")
        print(f"Gate data scores: {gate_data.get('scores', {})}")
        print(f"Thresholds: {thresholds}")
        print("="*60 + "\n")
    
    def _prepare_template_data(self, review_data: Dict[str, Any], gate_data: Dict[str, Any],
                               scores: Dict[str, int], thresholds: Dict[str, int],
                               details: Dict[str, Any], commit: str, author: str) -> Dict[str, Any]:
        """Prepare all data for template rendering"""
        return {
            'commit': commit,
            'author': author if author and author != "ECHO is off." else "Unknown",
            'timestamp': review_data.get('timestamp', 'N/A'),
            'review_depth': review_data.get('review_depth', 'STANDARD'),
            'score_rows': self.generate_score_rows(scores),
            'bar_chart': self.generate_bar_chart(scores),
            'comparison_rows': self.generate_comparison_rows(scores, thresholds, details),
            'gate_status': gate_data.get('status', 'UNKNOWN'),
            'gate_status_class': gate_data.get('status', 'UNKNOWN').lower(),
            'gate_status_icon': self._get_status_icon(gate_data.get('status', 'UNKNOWN')),
            'gate_message': gate_data.get('message', 'No message'),
            'issues_content': self._generate_issues_section(review_data.get('issues', [])),
            'recommendations': self._generate_recommendations(review_data.get('recommendations', [])),
            'summary': review_data.get('summary', 'No summary available'),
            'generation_time': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        }
    
    def _get_status_icon(self, status: str) -> str:
        """Get icon for status"""
        icons = {'PASSED': '✅', 'WARNING': '⚠️', 'FAILED': '❌'}
        return icons.get(status, '❓')
    
    def _generate_issues_section(self, issues: List[Dict[str, Any]]) -> str:
        """Generate HTML for issues section"""
        if not issues:
            return '<p style="text-align: center; padding: 40px; color: #28a745; font-size: 1.2em;">No issues found! Excellent work!</p>'
        
        content = f"""
                <p style="margin-bottom: 20px;">Found <strong>{len(issues)}</strong> issues requiring attention:</p>
                <ul class="issue-list">
"""
        for issue in issues:
            content += self.generate_issue_html(issue)
        content += "                </ul>"
        return content
    
    def _generate_recommendations(self, recommendations_list: List[str]) -> str:
        """Generate HTML for recommendations"""
        return "\n".join([f"                        <li>{rec}</li>" for rec in recommendations_list])
    
    def _write_report_file(self, output_file: str, html: str, scores: Dict[str, int], gate_status: str):
        """Write report to file and log results"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ Report generated: {output_file}")
        print(f"📊 Scores: Code Quality={scores.get('code_quality', 0)}, Security={scores.get('security', 0)}, Maintainability={scores.get('maintainability', 0)}")
        print(f"🚦 Quality Gate: {gate_status}")


def main():
    parser = argparse.ArgumentParser(description="Generate Pipeline Report")
    parser.add_argument("--review-file", required=True, help="Review report JSON file")
    parser.add_argument("--quality-gate-file", required=True, help="Quality gate result JSON file")
    parser.add_argument("--commit", required=True, help="Git commit hash")
    parser.add_argument("--author", required=True, help="Commit author")
    parser.add_argument("--output-file", default="pipeline-report.html", help="Output HTML file")
    
    args = parser.parse_args()
    
    # Load data
    try:
        with open(args.review_file, 'r', encoding='utf-8') as f:
            review_data = json.load(f)
        print(f"✅ Loaded review data from {args.review_file}")
    except Exception as e:
        print(f"❌ Error loading review file: {e}")
        return 1
    
    try:
        with open(args.quality_gate_file, 'r', encoding='utf-8') as f:
            gate_data = json.load(f)
        print(f"✅ Loaded quality gate data from {args.quality_gate_file}")
    except Exception as e:
        print(f"❌ Error loading quality gate file: {e}")
        return 1
    
    # Generate report
    generator = ReportGenerator()
    try:
        generator.generate_report(
            review_data=review_data,
            gate_data=gate_data,
            commit=args.commit,
            author=args.author,
            output_file=args.output_file
        )
        return 0
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
