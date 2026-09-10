# Architecture — Claude AI Agent Code Review Pipeline

## Overview

This system is a Jenkins CI/CD pipeline that uses **Anthropic's Claude AI as an agentic code reviewer**. Unlike traditional single-call AI integrations, Claude is given tools and autonomously decides what to read, in what order, over multiple reasoning turns before producing a final structured review.

---

## System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        DEVELOPER                                │
│                    git push / commit                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │ triggers
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     JENKINS PIPELINE                            │
│                       (Jenkinsfile)                             │
│                                                                 │
│  Stage 1: Checkout          Stage 2: Pre-Build Analysis        │
│  Stage 3: Claude AI Review  Stage 4: Quality Gate              │
│  Stage 5: Build             Stage 6: Test                      │
│  Stage 7: Generate Report                                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │ calls
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   claude_    │  │  quality_    │  │  generate_   │
│code_review.py│  │  gate.py     │  │  report.py   │
│              │  │              │  │              │
│ AGENTIC LOOP │  │ Threshold    │  │ HTML Report  │
│ tool-use API │  │ Evaluation   │  │ Generator    │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                  │
       ▼                 ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Anthropic   │  │  quality-    │  │  pipeline-   │
│  Claude API  │  │gate-result   │  │ report.html  │
│(api.anthropic│  │   .json      │  │              │
│    .com)     │  └──────────────┘  └──────────────┘
└──────┬───────┘
       │ feeds back into
       ▼
┌──────────────┐
│  review-     │
│ report.json  │
└──────────────┘
```

---

## The Agentic Loop (Core Innovation)

The key difference from a traditional AI integration is the **multi-turn tool-use loop** inside `claude_code_review.py`:

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLAUDE AGENT LOOP                            │
│                                                                 │
│  Input: commit hash + review depth                             │
│                                                                 │
│  System prompt: "You are a code review agent. Use tools        │
│  to read files, then produce JSON."                            │
│                                                                 │
│  ┌─────────────────────────────────────────────┐               │
│  │           TURN LOOP (max 10 turns)          │               │
│  │                                             │               │
│  │  Claude API call                            │               │
│  │       │                                     │               │
│  │       ├── stop_reason = "tool_use"          │               │
│  │       │        │                            │               │
│  │       │        ▼                            │               │
│  │       │   Execute tool locally:             │               │
│  │       │   - list_changed_files()            │               │
│  │       │   - get_git_diff()                  │               │
│  │       │   - read_file()                     │               │
│  │       │   - get_file_stats()                │               │
│  │       │        │                            │               │
│  │       │        ▼                            │               │
│  │       │   Feed result back to Claude        │               │
│  │       │   (appended to message history)     │               │
│  │       │        │                            │               │
│  │       │        └──────────── loop ──────────┘               │
│  │       │                                     │               │
│  │       └── stop_reason = "end_turn"          │               │
│  │                │                            │               │
│  │                ▼                            │               │
│  │          Extract JSON from response         │               │
│  │          Return structured review           │               │
│  └─────────────────────────────────────────────┘               │
│                                                                 │
│  Fallback: if API error → static analysis (_generate_mock_     │
│  review) runs locally with no API call                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### `scripts/claude_code_review.py` — The Agent

| Element | Detail |
|---------|--------|
| Class | `ClaudeCodeReviewer` |
| SDK | `anthropic` Python SDK |
| Model | `claude-sonnet-4-5` (configurable) |
| Max turns | 10 (configurable via `self.max_turns`) |
| Tools | 4 (list_changed_files, get_git_diff, read_file, get_file_stats) |
| Output | `review-report.json` |
| Fallback | `_generate_mock_review()` — static regex-based analysis |

**Tool implementations** — all run locally, no external calls:

| Tool | Implementation |
|------|---------------|
| `list_changed_files` | `git diff --name-only {commit}~1 {commit}` |
| `get_git_diff` | `git diff {commit}~1 {commit} -- {file}` |
| `read_file` | Python `open()` with utf-8 / latin-1 fallback |
| `get_file_stats` | `os.stat()` + line count |

---

### `scripts/quality_gate.py` — The Gate

Reads `review-report.json`, compares each score against the configured threshold:

```
score < threshold            → FAILED  (deficit = threshold - score)
threshold <= score < threshold+10  → WARNING (margin = score - threshold)
score >= threshold+10        → PASSED  (margin = score - threshold)
```

If any metric is FAILED → overall status = FAILED → Jenkins build is blocked.  
Output: `quality-gate-result.json`

---

### `scripts/generate_report.py` — The Reporter

Reads both JSON files, fills an HTML template (`report_template.html`) with:
- Score bar charts per metric
- Quality gate status badge
- Issue list grouped by severity
- Recommendations list
- Summary text

Output: `pipeline-report.html`

---

### `scripts/build_history_tracker.py` — The History Tracker

Maintains `build-history.json` across pipeline runs:
- `--action add` — records each build result
- `--action check` — blocks a new build if previous builds have unresolved FAILED status
- `--action report` — generates `history-report.json`

---

### `Jenkinsfile` — The Orchestrator

7 stages, all Windows-compatible (`bat` commands):

```
Checkout
  └─ extractGitMetadata()       → GIT_COMMIT_SHORT, GIT_AUTHOR

Pre-Build Analysis
  └─ analyzeCodebase()          → console output only

Claude AI Agent Code Review
  └─ performCodeReview()        → review-report.json
     └─ parseReviewResults()    → env vars: CODE_QUALITY_SCORE etc.

Quality Gate
  └─ evaluateQualityGate()
     ├─ build_history_tracker.py --action check
     ├─ quality_gate.py         → quality-gate-result.json
     ├─ processQualityGateResults()
     └─ addBuildToHistory()     → build-history.json

Build    (skipped if QUALITY_GATE_STATUS == FAILED)
Test     (skipped if QUALITY_GATE_STATUS == FAILED)

Generate Report
  └─ generate_report.py         → pipeline-report.html

Post (always)
  └─ publishHTML → pipeline-report.html
  └─ cleanup / archiveArtifacts
```

---

## Data Flow

```
git commit
    │
    ▼
Jenkinsfile triggers
    │
    ├──► claude_code_review.py
    │         │
    │         ├──► Anthropic API (multi-turn agentic loop)
    │         │         │
    │         │         ├──► list_changed_files  (git subprocess)
    │         │         ├──► get_git_diff        (git subprocess)
    │         │         ├──► read_file           (local filesystem)
    │         │         └──► get_file_stats      (local filesystem)
    │         │
    │         └──► review-report.json
    │                   {scores, issues, summary, recommendations, metadata}
    │
    ├──► quality_gate.py
    │         │
    │         ├──► reads review-report.json
    │         └──► quality-gate-result.json
    │                   {status, thresholds, details, failed_criteria}
    │
    └──► generate_report.py
              │
              ├──► reads review-report.json
              ├──► reads quality-gate-result.json
              └──► pipeline-report.html
```

---

## JSON Schema Contracts

### `review-report.json`
```json
{
  "timestamp": "2025-01-27T12:00:00",
  "commit": "abc1234",
  "review_depth": "STANDARD",
  "scores": {
    "code_quality": 78,
    "security": 85,
    "maintainability": 72,
    "overall": 78
  },
  "issues": [
    {
      "severity": "HIGH",
      "file": "src/main/java/com/example/Calculator.java",
      "line": 42,
      "message": "Issue description",
      "recommendation": "How to fix"
    }
  ],
  "summary": "Overall assessment text",
  "recommendations": ["Recommendation 1", "Recommendation 2"],
  "metadata": {
    "total_issues": 3,
    "critical_issues": 0,
    "high_issues": 1,
    "medium_issues": 2,
    "low_issues": 0
  }
}
```

### `quality-gate-result.json`
```json
{
  "timestamp": "2025-01-27T12:00:00",
  "status": "PASSED",
  "message": "Quality Gate PASSED: All criteria met",
  "scores": { "code_quality": 78, "security": 85, "maintainability": 72 },
  "thresholds": { "code_quality": 70, "security": 80, "maintainability": 60 },
  "failed_criteria": [],
  "warning_criteria": [],
  "passed_criteria": ["code_quality: 78/100 (threshold: 70/100, margin: 8)"],
  "details": {
    "code_quality": { "status": "WARNING", "score": 78, "threshold": 70, "margin": 8 }
  }
}
```

---

## Configuration Files

| File | Purpose | Key Settings |
|------|---------|-------------|
| `config/claude-config.json` | Claude model + agent settings | `model.id`, `agent.max_turns`, `agent.tools_enabled` |
| `config/quality-thresholds.json` | Gate thresholds + profiles | `thresholds.*`, `profiles.strict/standard/lenient` |
| `config/claude-credentials-setup.md` | Jenkins credential guide | Step-by-step setup instructions |

---

## Security Boundaries

```
Jenkins Agent Machine
┌────────────────────────────────────────────┐
│  CLAUDE_API_KEY  (Jenkins Secret — never   │
│  written to disk or printed in full)       │
│                                            │
│  claude_code_review.py                     │
│  ├─ reads local git repo files             │
│  └─ sends code to api.anthropic.com  ──────┼──► Anthropic Cloud API
│                                            │
│  quality_gate.py    (no network calls)     │
│  generate_report.py (no network calls)     │
│  build_history_tracker.py (no network)     │
└────────────────────────────────────────────┘
```

Only `claude_code_review.py` makes external network calls (to `api.anthropic.com`).  
All other scripts run entirely locally.

---

*Made with Bob*
