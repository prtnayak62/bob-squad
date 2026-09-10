#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude AI Agentic Code Review Script
Uses Anthropic's Claude with tool-use to autonomously read files,
analyse diffs, and produce a structured code review report.

Agentic loop:
  1. Claude receives the commit hash and review depth.
  2. Claude CALLS tools (list_changed_files, get_git_diff, read_file, get_file_stats)
     to gather the information it needs — in whatever order it decides.
  3. Each tool result is fed back into Claude's context.
  4. When Claude is satisfied it calls no more tools and returns the final JSON review.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict, List

import anthropic

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


# ---------------------------------------------------------------------------
# Tool definitions exposed to the Claude agent
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS = [
    {
        "name": "list_changed_files",
        "description": (
            "Returns a newline-separated list of file paths that were changed in the "
            "given commit compared to its parent. Use this first to discover which "
            "files need review."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "commit": {
                    "type": "string",
                    "description": "The git commit hash to inspect."
                }
            },
            "required": ["commit"]
        }
    },
    {
        "name": "list_source_files",
        "description": (
            "Returns all source code files (*.java, *.py, *.js, *.ts) tracked in the "
            "repository, regardless of what changed in this commit. Use this when the "
            "changed files contain no reviewable source code (e.g. only config or "
            "pipeline files changed) so you can still review the application code."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_git_diff",
        "description": (
            "Returns the unified diff for a specific file in the given commit. "
            "Use this to see exactly what lines were added or removed."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "commit": {
                    "type": "string",
                    "description": "The git commit hash."
                },
                "file_path": {
                    "type": "string",
                    "description": "Path to the file whose diff you want."
                }
            },
            "required": ["commit", "file_path"]
        }
    },
    {
        "name": "read_file",
        "description": (
            "Reads and returns the full content of a file from the repository. "
            "Use this when you need to understand context beyond the diff, e.g. "
            "to check how a function is implemented or how a class is structured."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Relative path to the file."
                }
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "get_file_stats",
        "description": (
            "Returns metadata about a file: number of lines, file extension, "
            "and size in bytes. Useful for a quick complexity assessment before "
            "deciding whether to read the full content."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Relative path to the file."
                }
            },
            "required": ["file_path"]
        }
    }
]


# ---------------------------------------------------------------------------
# Main reviewer class
# ---------------------------------------------------------------------------

class ClaudeCodeReviewer:
    """Agentic code reviewer powered by Claude with tool-use."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5",
                 base_url: str = None):
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        self.client = anthropic.Anthropic(**client_kwargs)
        self.model = model
        self.review_depth = "STANDARD"
        self.max_turns = 15   # safety cap on the agentic loop

    # ------------------------------------------------------------------
    # Tool executor — called whenever Claude requests a tool
    # ------------------------------------------------------------------

    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """Execute the requested tool and return the result as a string."""
        try:
            if tool_name == "list_changed_files":
                return self._tool_list_changed_files(tool_input["commit"])
            elif tool_name == "list_source_files":
                return self._tool_list_source_files()
            elif tool_name == "get_git_diff":
                return self._tool_get_git_diff(tool_input["commit"], tool_input["file_path"])
            elif tool_name == "read_file":
                return self._tool_read_file(tool_input["file_path"])
            elif tool_name == "get_file_stats":
                return self._tool_get_file_stats(tool_input["file_path"])
            else:
                return f"ERROR: Unknown tool '{tool_name}'"
        except Exception as e:
            return f"ERROR executing {tool_name}: {str(e)}"

    def _tool_list_changed_files(self, commit: str) -> str:
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", f"{commit}~1", commit],
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", check=True
            )
            files = [f for f in result.stdout.strip().split("\n") if f]
            if files:
                return "\n".join(files)
            # Fall through to root diff if no files found
        except subprocess.CalledProcessError:
            pass  # likely only 1 commit — try --root diff below

        # Repo has only one commit — diff against empty tree
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=A",
                 "4b825dc642cb6eb9a060e54bf8d69288fbee4904", commit],
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", check=True
            )
            files = [f for f in result.stdout.strip().split("\n") if f]
            if files:
                return "\n".join(files)
        except subprocess.CalledProcessError:
            pass

        # Last resort: list all tracked files
        try:
            result = subprocess.run(
                ["git", "ls-files"],
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", check=True
            )
            files = [f for f in result.stdout.strip().split("\n") if f]
            return "\n".join(files) if files else "No files found."
        except subprocess.CalledProcessError as e:
            return f"git error: {e.stderr}"

    def _tool_list_source_files(self) -> str:
        """List all tracked source code files (.java .py .js .ts) in the repo."""
        SOURCE_EXTS = {".java", ".py", ".js", ".ts"}
        try:
            result = subprocess.run(
                ["git", "ls-files"],
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", check=True
            )
            files = [
                f for f in result.stdout.strip().split("\n")
                if f and os.path.splitext(f)[1] in SOURCE_EXTS
                and not f.startswith("scripts/")  # skip the pipeline scripts themselves
            ]
            return "\n".join(files) if files else "No source files found."
        except subprocess.CalledProcessError as e:
            return f"git error: {e.stderr}"

    def _tool_get_git_diff(self, commit: str, file_path: str) -> str:
        try:
            result = subprocess.run(
                ["git", "diff", f"{commit}~1", commit, "--", file_path],
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", check=True
            )
            return result.stdout or "No diff available."
        except subprocess.CalledProcessError as e:
            return f"git error: {e.stderr}"

    def _tool_read_file(self, file_path: str) -> str:
        for encoding in ["utf-8", "latin-1"]:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except FileNotFoundError:
                return f"File not found: {file_path}"
            except Exception as e:
                return f"Error reading file: {str(e)}"
        try:
            with open(file_path, "rb") as f:
                return f.read().decode("utf-8", errors="replace")
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def _tool_get_file_stats(self, file_path: str) -> str:
        try:
            stat = os.stat(file_path)
            with open(file_path, "rb") as f:
                line_count = sum(1 for _ in f)
            ext = os.path.splitext(file_path)[1]
            return json.dumps({
                "file_path": file_path,
                "extension": ext,
                "size_bytes": stat.st_size,
                "line_count": line_count
            })
        except FileNotFoundError:
            return json.dumps({"error": f"File not found: {file_path}"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    # ------------------------------------------------------------------
    # Agentic review loop
    # ------------------------------------------------------------------

    def analyze_code_agentically(self, commit: str, review_depth: str) -> Dict[str, Any]:
        """
        Run the agentic Claude loop.

        Claude is given 4 tools and autonomously decides which files to read,
        which diffs to inspect, and when it has enough context to produce
        the final JSON review.
        """
        depth_instructions = {
            "QUICK": (
                "Focus only on CRITICAL and HIGH severity issues: security vulnerabilities, "
                "hardcoded secrets, and obvious bugs. Be concise."
            ),
            "STANDARD": (
                "Perform a thorough review covering code quality, security, best practices, "
                "naming conventions, and maintainability."
            ),
            "COMPREHENSIVE": (
                "Perform a deep review covering code quality, security, performance, "
                "maintainability, architectural concerns, test coverage, and SOLID principles. "
                "Read related test files if they exist."
            ),
        }

        system_prompt = (
            "You are an expert code review agent with deep knowledge of software engineering "
            "best practices, security, and clean code principles.\n\n"
            "Your workflow:\n"
            "1. Call list_changed_files to see what changed in this commit.\n"
            "2. Filter that list to source code files only (*.java, *.py, *.js, *.ts).\n"
            "   - SKIP: Jenkinsfile, *.groovy, *.json, *.xml, *.md, *.bat, *.sh, *.txt, "
            "*.properties, *.yaml, *.yml — these are pipeline/config files, NOT application code.\n"
            "3. If NO source files were changed in this commit, call list_source_files to get "
            "all application source files in the repo, then read those instead.\n"
            "4. Read at most 5 source files, then stop and produce the JSON review.\n\n"
            "Score the APPLICATION SOURCE CODE quality (Java/Python/JS/TS files), not pipeline files.\n\n"
            "Output your final answer as VALID JSON ONLY — no preamble, no markdown fences, no extra text.\n\n"
            "The JSON MUST have exactly these top-level keys:\n"
            "  scores        → object with code_quality, security, maintainability, overall (0-100)\n"
            "  issues        → array of {severity, file, line, message, recommendation}\n"
            "  summary       → string\n"
            "  recommendations → array of strings\n\n"
            "severity values: CRITICAL, HIGH, MEDIUM, LOW"
        )

        user_message = (
            f"Review commit: {commit}\n"
            f"Review depth: {review_depth}\n"
            f"Instructions: {depth_instructions.get(review_depth, depth_instructions['STANDARD'])}\n\n"
            "Step 1: Call list_changed_files to see what changed.\n"
            "Step 2: If the changed files are only pipeline/config files (Jenkinsfile, *.json, "
            "*.xml, *.md, *.bat etc.), call list_source_files to get the application source code.\n"
            "Step 3: Read the source code files (*.java, *.py, *.js, *.ts) and review them.\n"
            "Step 4: Output the JSON review of the APPLICATION CODE quality."
        )

        messages: List[Dict[str, Any]] = [{"role": "user", "content": user_message}]

        print(f"\n🤖 Claude Agent starting agentic loop (max {self.max_turns} turns)...")

        for turn in range(1, self.max_turns + 1):
            print(f"   Turn {turn}: calling Claude...")

            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                tools=TOOL_DEFINITIONS,
                messages=messages
            )

            print(f"   stop_reason={response.stop_reason}  "
                  f"blocks={[b.type for b in response.content]}")

            # ---- Claude finished — extract the JSON review ----
            if response.stop_reason == "end_turn":
                print("   ✅ Claude finished reasoning. Extracting review JSON...")
                return self._extract_json_from_response(response)

            # ---- Claude wants to call tools ----
            if response.stop_reason == "tool_use":
                # Append Claude's response to the conversation history
                messages.append({"role": "assistant", "content": response.content})

                # Execute every tool Claude requested and collect results
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        print(f"   🔧 Tool call: {block.name}({json.dumps(block.input)})")
                        result = self._execute_tool(block.name, block.input)
                        preview = result[:120].replace("\n", " ")
                        print(f"      → result preview: {preview}...")
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result
                        })

                # Feed all tool results back to Claude
                messages.append({"role": "user", "content": tool_results})
                continue

            # Unexpected stop reason — treat as done
            print(f"   ⚠️ Unexpected stop_reason: {response.stop_reason}. Attempting JSON extraction.")
            return self._extract_json_from_response(response)

        # Reached max turns without a clean end_turn
        print(f"⚠️ Agent reached max turns ({self.max_turns}). Falling back to static analysis.")
        raise RuntimeError("Agent loop exceeded max turns without producing a review.")

    # ------------------------------------------------------------------
    # JSON extraction from Claude's final response
    # ------------------------------------------------------------------

    def _extract_json_from_response(self, response) -> Dict[str, Any]:
        """Extract the JSON object from Claude's final text block."""
        full_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                full_text += block.text

        print(f"\n🔍 Extracting JSON from response ({len(full_text)} chars)...")

        # Find opening brace
        json_start = full_text.find("{")
        if json_start == -1:
            raise ValueError(f"No JSON object found in Claude response:\n{full_text[:500]}")

        # Match closing brace
        brace_count = 0
        json_end = json_start
        for i in range(json_start, len(full_text)):
            if full_text[i] == "{":
                brace_count += 1
            elif full_text[i] == "}":
                brace_count -= 1
                if brace_count == 0:
                    json_end = i + 1
                    break

        json_str = full_text[json_start:json_end]
        parsed = json.loads(json_str)

        # Validate required keys
        required = {"scores", "issues", "summary", "recommendations"}
        missing = required - set(parsed.keys())
        if missing:
            raise ValueError(f"JSON missing required keys: {missing}")

        print("✅ JSON extracted successfully.")
        return parsed

    # ------------------------------------------------------------------
    # Static fallback (used when Claude API is unreachable)
    # ------------------------------------------------------------------

    def _get_files_for_fallback(self, commit: str) -> List[Dict[str, Any]]:
        """Gather file data for the static fallback analysis."""
        try:
            raw = self._tool_list_changed_files(commit)
            paths = [p for p in raw.strip().split("\n") if p and "error" not in p.lower()]
        except Exception:
            paths = []

        files = []
        for path in paths:
            content = self._tool_read_file(path)
            files.append({
                "path": path,
                "content": content,
                "extension": os.path.splitext(path)[1]
            })
        return files

    def _generate_mock_review(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Static code analysis fallback when Claude API is unavailable."""
        print("⚠️ Using static fallback analysis (Claude API unavailable)")

        issues = []
        total_complexity = 0

        for file_info in files:
            content = file_info.get("content", "")
            path = file_info["path"]
            lines = content.split("\n")

            if "TODO" in content or "FIXME" in content or "HACK" in content:
                issues.append({"severity": "MEDIUM", "file": path, "line": 0,
                                "message": "Found TODO/FIXME/HACK comments indicating incomplete code",
                                "recommendation": "Address pending tasks before merging"})

            if any(w in content.lower() for w in ["password", "secret", "api_key", "apikey", "token"]):
                if "=" in content and "credentials(" not in content:
                    issues.append({"severity": "CRITICAL", "file": path, "line": 0,
                                   "message": "Potential hardcoded credentials or secrets detected",
                                   "recommendation": "Use environment variables or secure credential management"})

            if len(lines) > 500:
                issues.append({"severity": "HIGH", "file": path, "line": 0,
                                "message": f"Large file detected ({len(lines)} lines) - difficult to maintain",
                                "recommendation": "Break into smaller, focused modules"})
            elif len(lines) > 300:
                issues.append({"severity": "MEDIUM", "file": path, "line": 0,
                                "message": f"File is getting large ({len(lines)} lines)",
                                "recommendation": "Consider refactoring into smaller components"})

            if file_info["extension"] in [".py", ".js", ".java", ".ts"]:
                for i, line in enumerate(lines):
                    if any(kw in line for kw in ["def ", "function ", "public ", "private ", "protected "]):
                        func_lines = 0
                        for j in range(i + 1, min(i + 100, len(lines))):
                            if any(kw in lines[j] for kw in ["def ", "function ", "public ", "private "]):
                                break
                            func_lines += 1
                        if func_lines > 50:
                            issues.append({"severity": "HIGH", "file": path, "line": i + 1,
                                           "message": f"Function too long ({func_lines} lines) — high complexity",
                                           "recommendation": "Break into smaller, single-purpose functions"})
                            total_complexity += 20
                        elif func_lines > 30:
                            issues.append({"severity": "MEDIUM", "file": path, "line": i + 1,
                                           "message": f"Function is getting long ({func_lines} lines)",
                                           "recommendation": "Consider refactoring for better readability"})
                            total_complexity += 10

            if file_info["extension"] in [".py", ".js", ".java", ".ts"]:
                has_docs = '"""' in content or "'''" in content or "/**" in content or "//" in content
                if not has_docs and len(lines) > 50:
                    issues.append({"severity": "MEDIUM", "file": path, "line": 0,
                                   "message": "Missing documentation/comments in significant code file",
                                   "recommendation": "Add docstrings and comments to explain complex logic"})

            duplicate_lines: List[str] = []
            for line in lines:
                if line.strip() and len(line.strip()) > 20:
                    if lines.count(line) > 3 and line not in duplicate_lines:
                        duplicate_lines.append(line)
            if len(duplicate_lines) > 5:
                issues.append({"severity": "HIGH", "file": path, "line": 0,
                                "message": f"Significant code duplication ({len(duplicate_lines)} repeated patterns)",
                                "recommendation": "Extract common code into reusable functions"})

            if file_info["extension"] in [".py", ".js", ".java", ".ts"]:
                poor_names = 0
                for line in lines:
                    if "=" in line and "for " not in line:
                        matches = re.findall(r"\b([a-z])\s*=", line)
                        poor_names += len([m for m in matches if m not in list("ijkxyz")])
                if poor_names > 5:
                    issues.append({"severity": "MEDIUM", "file": path, "line": 0,
                                   "message": f"Poor variable naming ({poor_names} single-letter names)",
                                   "recommendation": "Use descriptive variable names"})

        critical_count = sum(1 for i in issues if i["severity"] == "CRITICAL")
        high_count = sum(1 for i in issues if i["severity"] == "HIGH")
        medium_count = sum(1 for i in issues if i["severity"] == "MEDIUM")
        low_count = sum(1 for i in issues if i["severity"] == "LOW")

        security_score = max(30, 100 - critical_count * 40 - high_count * 20)
        code_quality_score = max(30, 100 - critical_count * 30 - high_count * 15
                                 - medium_count * 8 - low_count * 3)
        maintainability_score = max(30, 100 - high_count * 20 - medium_count * 10
                                    - total_complexity // 10)
        overall_score = (security_score + code_quality_score + maintainability_score) // 3
        quality_level = ("excellent" if overall_score >= 85 else
                         "good" if overall_score >= 70 else
                         "fair" if overall_score >= 50 else "poor")

        return {
            "scores": {
                "code_quality": max(0, min(100, code_quality_score)),
                "security": max(0, min(100, security_score)),
                "maintainability": max(0, min(100, maintainability_score)),
                "overall": max(0, min(100, overall_score))
            },
            "issues": issues,
            "summary": (
                f"Static fallback analysis: {len(issues)} issues found "
                f"({critical_count} critical, {high_count} high, {medium_count} medium, {low_count} low). "
                f"Overall quality is {quality_level}."
            ),
            "recommendations": [
                "Follow consistent coding standards and style guides",
                "Add comprehensive unit tests for all functions",
                "Document complex logic with clear comments",
                "Use meaningful, descriptive variable and function names",
                "Keep functions small and focused (< 30 lines)",
                "Avoid code duplication — extract common patterns",
                "Never hardcode credentials or secrets",
                "Break large files into smaller, cohesive modules"
            ]
        }

    # ------------------------------------------------------------------
    # Report writer
    # ------------------------------------------------------------------

    def generate_report(self, review_data: Dict[str, Any], commit: str, output_file: str) -> Dict[str, Any]:
        """Write review-report.json consumed by quality_gate.py and generate_report.py."""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "commit": commit,
            "review_depth": self.review_depth,
            "scores": review_data["scores"],
            "issues": review_data["issues"],
            "summary": review_data["summary"],
            "recommendations": review_data["recommendations"],
            "metadata": {
                "total_issues": len(review_data["issues"]),
                "critical_issues": sum(1 for i in review_data["issues"] if i["severity"] == "CRITICAL"),
                "high_issues": sum(1 for i in review_data["issues"] if i["severity"] == "HIGH"),
                "medium_issues": sum(1 for i in review_data["issues"] if i["severity"] == "MEDIUM"),
                "low_issues": sum(1 for i in review_data["issues"] if i["severity"] == "LOW")
            }
        }
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"✅ Review report generated: {output_file}")
        return report


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Claude AI Agentic Code Review")
    parser.add_argument("--api-key", required=True, help="Anthropic API key or IBM gateway token")
    parser.add_argument("--base-url", default=None, help="Custom API base URL (e.g. IBM gateway)")
    parser.add_argument("--model", default="claude-sonnet-4-6", help="Claude model ID")
    parser.add_argument("--review-depth", choices=["QUICK", "STANDARD", "COMPREHENSIVE"],
                        default="STANDARD", help="Review depth level")
    parser.add_argument("--commit", required=True, help="Git commit hash to review")
    parser.add_argument("--output-file", default="review-report.json", help="Output JSON file path")
    args = parser.parse_args()

    print("🤖 Claude AI Agentic Code Review")
    print(f"   Commit:       {args.commit}")
    print(f"   Review Depth: {args.review_depth}")
    print(f"   Model:        {args.model}")
    api_key_masked = (args.api_key[:8] + "..." + args.api_key[-4:]
                      if len(args.api_key) > 12 else "***")
    print(f"   API Key:      {api_key_masked} ({len(args.api_key)} chars)")

    if args.base_url:
        print(f"   Base URL:     {args.base_url}")
    reviewer = ClaudeCodeReviewer(api_key=args.api_key, model=args.model,
                                  base_url=args.base_url)
    reviewer.review_depth = args.review_depth

    # Run agentic loop; fall back to static analysis on any API error
    try:
        print("\n🔍 Starting agentic code analysis with Claude...")
        review_data = reviewer.analyze_code_agentically(args.commit, args.review_depth)
    except Exception as e:
        print(f"\n⚠️ Claude API error: {e}")
        print("   Falling back to static code analysis...")
        files = reviewer._get_files_for_fallback(args.commit)
        if not files:
            print("⚠️  No files to review")
            minimal = {
                "timestamp": datetime.utcnow().isoformat(),
                "commit": args.commit,
                "scores": {"code_quality": 100, "security": 100,
                            "maintainability": 100, "overall": 100},
                "issues": [],
                "summary": "No files changed",
                "recommendations": [],
                "metadata": {"total_issues": 0, "critical_issues": 0,
                              "high_issues": 0, "medium_issues": 0, "low_issues": 0}
            }
            with open(args.output_file, "w", encoding="utf-8") as f:
                json.dump(minimal, f, indent=2)
            return 0
        review_data = reviewer._generate_mock_review(files)

    # Write report
    print("\n📊 Generating report...")
    report = reviewer.generate_report(review_data, args.commit, args.output_file)

    print("\n" + "=" * 60)
    print("📈 REVIEW SUMMARY")
    print("=" * 60)
    print(f"Code Quality:     {report['scores']['code_quality']}/100")
    print(f"Security:         {report['scores']['security']}/100")
    print(f"Maintainability:  {report['scores']['maintainability']}/100")
    print(f"Overall Score:    {report['scores']['overall']}/100")
    print(f"\nTotal Issues:     {report['metadata']['total_issues']}")
    print(f"  Critical:       {report['metadata']['critical_issues']}")
    print(f"  High:           {report['metadata']['high_issues']}")
    print(f"  Medium:         {report['metadata']['medium_issues']}")
    print(f"  Low:            {report['metadata']['low_issues']}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
