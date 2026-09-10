# Bob Squad — Claude AI Agent Code Review Pipeline

A Jenkins CI/CD pipeline that uses **Anthropic's Claude AI as an agentic code reviewer**.  
Claude autonomously reads files, inspects diffs, cross-references code, and reasons step-by-step before producing a structured quality report — all inside a Jenkins pipeline.

---

## What This Does

Every time code is committed, the pipeline:

1. **Checks out** the code and extracts Git metadata
2. **Runs a pre-build analysis** — lists changed files and line counts
3. **Starts the Claude AI Agent** — Claude uses tools to read files, get diffs, and reason about the code
4. **Evaluates a Quality Gate** — scores are compared against configurable thresholds
5. **Builds and Tests** — only if the quality gate passes
6. **Generates an HTML Report** — visual report with scores, issues, and recommendations

---

## Why Agentic AI?

Traditional code review tools send a truncated snippet to an AI and get one response back.  
This pipeline uses Claude as a **true agent**:

| Traditional (single-call) | Claude Agent (this project) |
|---------------------------|----------------------------|
| Max 5 files, 1500 chars each — truncated | Claude decides which files to read, reads them fully |
| One prompt → one response | Multi-turn loop: read → think → read more → conclude |
| Cannot follow imports or check related files | Can cross-reference test files, callers, and related modules |
| Stateless | Maintains full conversation history across tool calls |

---

## Project Structure

```
Bob-Squad-main/
│
├── Jenkinsfile                          # 7-stage CI/CD pipeline definition
├── pom.xml                              # Maven build configuration
├── requirements.txt                     # Python dependencies
├── README.md                            # This file
│
├── config/
│   ├── claude-config.json               # Claude model and agent settings
│   ├── claude-credentials-setup.md      # How to set up Jenkins credentials
│   └── quality-thresholds.json          # Quality gate pass/fail thresholds
│
├── scripts/
│   ├── claude_code_review.py            # Claude AI Agent — agentic code reviewer
│   ├── quality_gate.py                  # Evaluates scores against thresholds
│   ├── generate_report.py               # Generates the HTML pipeline report
│   ├── build_history_tracker.py         # Tracks build history and trends
│   └── report_template.html             # HTML report template
│
├── src/
│   ├── main/java/com/example/
│   │   ├── Calculator.java              # Sample Java source (under review)
│   │   └── Main.java
│   └── test/java/com/example/
│       └── UserServiceTest.java         # Sample Java tests
│
├── run_pipeline_locally.bat             # Simulate full pipeline locally (Windows)
├── test_scripts.bat                     # Validate all components (Windows)
├── test_scripts.sh                      # Validate all components (Linux/macOS)
└── test_local_generation.bat            # Quick local report test (Windows)
```

---

## Pipeline Stages

```
Checkout → Pre-Build Analysis → Claude AI Agent Review → Quality Gate → Build → Test → Generate Report
```

| Stage | What Happens |
|-------|-------------|
| **Checkout** | Pulls code from SCM, extracts commit hash and author |
| **Pre-Build Analysis** | Lists changed files, counts lines of code |
| **Claude AI Agent Code Review** | Claude runs agentic loop with 4 tools (see below) |
| **Quality Gate** | Checks scores against thresholds; blocks build if failed |
| **Build** | Runs `mvn clean package` (skipped if quality gate failed) |
| **Test** | Runs `mvn test` (skipped if quality gate failed) |
| **Generate Report** | Produces `pipeline-report.html` with scores, issues, recommendations |

---

## Claude Agent Tools

The Claude agent is given 4 tools it can call in any order, as many times as needed:

| Tool | What It Does |
|------|-------------|
| `list_changed_files(commit)` | Lists all files changed in the commit |
| `get_git_diff(commit, file_path)` | Returns the unified diff for a specific file |
| `read_file(file_path)` | Reads the full content of any file in the repo |
| `get_file_stats(file_path)` | Returns line count, extension, and file size |

The agent runs for up to **10 turns**. If the API is unreachable, it falls back to static analysis automatically.

---

## Quality Gate Thresholds

Scores are 0–100. Default thresholds (configurable in `config/quality-thresholds.json`):

| Metric | Default Threshold | Severity |
|--------|------------------|---------|
| Code Quality | 70 | HIGH |
| Security | 80 | CRITICAL |
| Maintainability | 60 | MEDIUM |

**Gate outcomes:**
- **PASSED** — all scores exceed thresholds by more than 10 points
- **WARNING** — scores pass but are within 10 points of threshold
- **FAILED** — one or more scores are below threshold → build is blocked

---

## Review Depth Options

Set via the `REVIEW_DEPTH` Jenkins build parameter:

| Depth | Focus |
|-------|-------|
| `QUICK` | Critical and HIGH issues only — security vulnerabilities and obvious bugs |
| `STANDARD` | Code quality, security, best practices, naming, maintainability *(default)* |
| `COMPREHENSIVE` | All of STANDARD + performance, architecture, SOLID principles, test coverage |

---

## Output Files

After a pipeline run, these files are produced and archived as Jenkins artifacts:

| File | Description |
|------|-------------|
| `review-report.json` | Full Claude AI review with scores, issues, summary |
| `quality-gate-result.json` | Pass/fail result with threshold details |
| `pipeline-report.html` | Visual HTML report — open in browser |
| `build-history.json` | Cumulative build history |

---

## Configuration

### Claude Model (`config/claude-config.json`)
```json
{
  "model": { "id": "claude-sonnet-4-5" },
  "agent": { "max_turns": 10, "tools_enabled": true }
}
```
Change `model.id` to `claude-3-5-haiku-20241022` for faster/cheaper reviews, or `claude-opus-4-5` for the deepest analysis.

### Quality Thresholds (`config/quality-thresholds.json`)
Three built-in profiles:
- `strict` — 85 / 90 / 85
- `standard` — 70 / 80 / 75 *(default)*
- `lenient` — 60 / 70 / 65

### Jenkins Parameters
| Parameter | Default | Description |
|-----------|---------|-------------|
| `REVIEW_DEPTH` | `STANDARD` | Review thoroughness |
| `SKIP_QUALITY_GATE` | `false` | Bypass gate (not for production) |
| `CUSTOM_THRESHOLD` | *(empty)* | Override code quality threshold |

---

## Prerequisites

- **Jenkins 2.x+** with Pipeline and HTML Publisher plugins
- **Python 3.7+** on the Jenkins agent
- **Anthropic API key** (reuse the same key as Claude Code CLI)
- **Git** available on PATH
- **Java + Maven** (for the sample Java project build)

---

## Quick Start

See [`LOCAL_SETUP.md`](LOCAL_SETUP.md) for a full step-by-step local run guide.  
See [`config/claude-credentials-setup.md`](config/claude-credentials-setup.md) for Jenkins credential setup.

```cmd
REM 1. Install Python dependency
pip install anthropic>=0.40.0

REM 2. Set your Anthropic API key
set CLAUDE_API_KEY=sk-ant-your-key-here

REM 3. Run the agent directly
python scripts\claude_code_review.py --api-key "%CLAUDE_API_KEY%" --model "claude-sonnet-4-5" --review-depth STANDARD --commit HEAD --output-file review-report.json
```

---

## Security Notes

- API key is stored as a Jenkins Secret Text credential — never hardcoded
- Code is sent to Anthropic's API for analysis — do not use with confidential/proprietary code unless your Anthropic plan covers it
- The `SKIP_QUALITY_GATE` parameter should never be enabled in production pipelines

---

*Made with Bob*
