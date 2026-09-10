# Local Setup Guide — Claude AI Agent Code Review Pipeline

Step-by-step instructions to run the full pipeline locally on Windows, without Jenkins.

---

## Prerequisites

Before you start, ensure all of the following are installed:

| Requirement | Version | Check Command |
|-------------|---------|--------------|
| Python | 3.7+ | `python --version` |
| Git | Any | `git --version` |
| Java (JDK) | 11+ | `java -version` |
| Maven | 3.6+ | `mvn -version` |

---

## Step 1 — Clone or Navigate to the Project

```cmd
cd C:\Users\PritiNayak\python\Bob-Squad-main\Bob-Squad-main
```

Verify you can see the key files:
```cmd
dir Jenkinsfile
dir scripts\claude_code_review.py
dir config\claude-config.json
```

---

## Step 2 — Install Python Dependencies

```cmd
pip install -r requirements.txt
```

This installs:
- `anthropic>=0.40.0` — Anthropic Python SDK (required for the agent)
- `requests>=2.31.0` — HTTP library
- All other dependencies listed in `requirements.txt`

Verify the Anthropic SDK installed correctly:
```cmd
python -c "import anthropic; print('anthropic version:', anthropic.__version__)"
```

---

## Step 3 — Get Your Anthropic API Key

You already have Claude Code CLI installed. Your API key is the same one used by the CLI.

**Option A — From Anthropic Console (easiest)**
1. Go to: https://console.anthropic.com/settings/keys
2. Copy your existing key (starts with `sk-ant-api03-...`)

**Option B — From Claude Code CLI config**
```cmd
type C:\Users\PritiNayak\.claude\config.json
```
Look for the `api_key` field.

---

## Step 4 — Set Your API Key

```cmd
set CLAUDE_API_KEY=sk-ant-api03-your-key-here
```

Verify it is set:
```cmd
echo %CLAUDE_API_KEY%
```
You should see your key printed (not empty).

> **Tip**: To avoid setting this every time, add it to your Windows environment variables permanently:  
> `System Properties → Advanced → Environment Variables → New User Variable`  
> Name: `CLAUDE_API_KEY`, Value: `sk-ant-api03-your-key-here`

---

## Step 5 — Initialise Git (if not already done)

The agent uses `git diff` to find changed files. The repo must have at least one commit:

```cmd
git init
git add .
git commit -m "Initial commit"
```

If already a git repo with commits, skip this step.

---

## Step 6 — Run the Validation Test

Before running the full pipeline, verify all components are working:

```cmd
test_scripts.bat
```

All tests should show `[PASS]`. The most important ones:
- `[PASS] anthropic module` — SDK is installed
- `[PASS] claude_code_review.py exists` — agent script is present
- `[PASS] claude_code_review.py help works` — script is executable
- `[PASS] quality_gate.py executes successfully` — gate evaluator works
- `[PASS] claude-config.json exists` — config file is present

---

## Step 7 — Run the Full Pipeline Locally

### Option A — Automated (recommended)

```cmd
set CLAUDE_API_KEY=sk-ant-api03-your-key-here
run_pipeline_locally.bat
```

This runs all stages in sequence:
1. Gets Git commit hash and author
2. Runs Claude AI Agent code review → `review-report.json`
3. Evaluates quality gate → `quality-gate-result.json`
4. Generates HTML report → `pipeline-report.html`
5. Opens the report in your browser

---

### Option B — Step by Step (for debugging)

Run each script individually to see exactly what each one does.

#### Step 7a — Run the Claude AI Agent

```cmd
python scripts\claude_code_review.py ^
    --api-key "%CLAUDE_API_KEY%" ^
    --model "claude-sonnet-4-5" ^
    --review-depth "STANDARD" ^
    --commit "HEAD" ^
    --output-file "review-report.json"
```

**What you will see in the console:**
```
🤖 Claude AI Agentic Code Review
   Commit:       abc1234
   Review Depth: STANDARD
   Model:        claude-sonnet-4-5
   API Key:      sk-ant-... (108 chars)

🔍 Starting agentic code analysis with Claude...

🤖 Claude Agent starting agentic loop (max 10 turns)...
   Turn 1: calling Claude...
   stop_reason=tool_use  blocks=[text, tool_use]
   🔧 Tool call: list_changed_files({"commit": "HEAD"})
      → result preview: src/main/java/com/example/Calculator.java...
   Turn 2: calling Claude...
   🔧 Tool call: get_git_diff({"commit": "HEAD", "file_path": "src/..."})
      → result preview: @@ -1,10 +1,15 @@...
   Turn 3: calling Claude...
   ✅ Claude finished reasoning. Extracting review JSON...

📊 Generating report...
✅ Review report generated: review-report.json

============================================================
📈 REVIEW SUMMARY
============================================================
Code Quality:     78/100
Security:         85/100
Maintainability:  72/100
Overall Score:    78/100

Total Issues:     3
  Critical:       0
  High:           1
  Medium:         2
  Low:            0
============================================================
```

Check the output file:
```cmd
type review-report.json
```

---

#### Step 7b — Evaluate the Quality Gate

```cmd
python scripts\quality_gate.py ^
    --review-file "review-report.json" ^
    --code-threshold 70 ^
    --security-threshold 80 ^
    --maintainability-threshold 60 ^
    --output-file "quality-gate-result.json"
```

**What you will see:**
```
🚦 QUALITY GATE EVALUATION
======================================================================
Status: ✅ PASSED
Message: Quality Gate PASSED: All criteria met
```

---

#### Step 7c — Generate the HTML Report

```cmd
for /f "tokens=*" %a in ('git rev-parse --short HEAD') do set GIT_COMMIT=%a
for /f "tokens=*" %a in ('git config user.name') do set GIT_AUTHOR=%a

python scripts\generate_report.py ^
    --review-file "review-report.json" ^
    --quality-gate-file "quality-gate-result.json" ^
    --commit "%GIT_COMMIT%" ^
    --author "%GIT_AUTHOR%" ^
    --output-file "pipeline-report.html"
```

---

#### Step 7d — Open the Report

```cmd
start pipeline-report.html
```

The HTML report opens in your default browser and shows:
- Score cards with progress bars (Code Quality, Security, Maintainability, Overall)
- Quality gate status (PASSED / WARNING / FAILED)
- Issue list with severity badges
- AI-generated recommendations
- Summary text from Claude

---

## Step 8 — Quick Test (generate report only)

To quickly regenerate the report from existing JSON files without calling the Claude API again:

```cmd
test_local_generation.bat
```

---

## Review Depth Options

Change `--review-depth` to control how thorough Claude's analysis is:

| Value | What Claude Does | Speed | Cost |
|-------|-----------------|-------|------|
| `QUICK` | Checks critical/high issues only | Fastest | Lowest |
| `STANDARD` | Quality, security, best practices | Medium | Medium |
| `COMPREHENSIVE` | Everything + architecture, SOLID, tests | Slowest | Highest |

---

## Model Options

Change `--model` to use a different Claude model:

| Model | Speed | Cost | Best For |
|-------|-------|------|---------|
| `claude-3-5-haiku-20241022` | Fastest | Lowest | Quick daily checks |
| `claude-sonnet-4-5` | Medium | Medium | Default — best balance |
| `claude-opus-4-5` | Slowest | Highest | Deep comprehensive review |

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'anthropic'`
```cmd
pip install anthropic>=0.40.0
```

### `anthropic.AuthenticationError: Invalid API key`
- Check your key starts with `sk-ant-`
- Verify: `echo %CLAUDE_API_KEY%` shows the full key
- Get a new key at: https://console.anthropic.com/settings/keys

### `anthropic.RateLimitError`
You have hit the API rate limit. Wait 60 seconds and retry.

### `git error: unknown revision or path`
The commit `HEAD~1` does not exist (likely a fresh repo with only 1 commit).  
Make a second commit first:
```cmd
git add .
git commit -m "Second commit"
```
Or pass a specific commit hash instead of `HEAD`.

### `Agent reached max turns (10)`
Claude needed more than 10 turns. The script falls back to static analysis automatically.  
To increase the limit, edit [`scripts/claude_code_review.py`](scripts/claude_code_review.py) line 128:
```python
self.max_turns = 15  # increase from 10
```

### Quality Gate always FAILED
Lower the thresholds temporarily while you address issues:
```cmd
python scripts\quality_gate.py ^
    --review-file "review-report.json" ^
    --code-threshold 50 ^
    --security-threshold 60 ^
    --maintainability-threshold 50 ^
    --output-file "quality-gate-result.json"
```

---

## Running on Jenkins

Once local testing passes, see [`config/claude-credentials-setup.md`](config/claude-credentials-setup.md) to set up Jenkins and run the full automated pipeline.

---

*Made with Bob*
