# Claude AI Agent — Jenkins Credentials Setup Guide

This guide explains how to configure Jenkins to use your existing Anthropic API key
(the same one used by Claude Code CLI v2.1.229) to run the Claude AI Agent code review pipeline.

---

## Section 1 — Prerequisites

Before running the pipeline, ensure the following are in place on the Jenkins agent machine:

1. **Python 3.7 or higher**
   ```
   python --version
   ```

2. **Install the Anthropic Python SDK**
   ```
   pip install anthropic>=0.40.0
   ```
   Verify the install:
   ```
   python -c "import anthropic; print(anthropic.__version__)"
   ```

3. **Git available on PATH** (required for the agent's tools)
   ```
   git --version
   ```

---

## Section 2 — Find Your Anthropic API Key

You already have Claude Code CLI v2.1.229 installed and authenticated at `C:\Users\PritiNayak`.
Your Anthropic API key is stored in one of these locations:

### Option A — Claude Code CLI config file
Open a command prompt and run:
```
type C:\Users\PritiNayak\.claude\config.json
```
Look for the `api_key` field.

### Option B — Anthropic Console (recommended)
1. Go to: https://console.anthropic.com/settings/keys
2. Sign in with your Anthropic account
3. Copy your existing API key (starts with `sk-ant-`)
4. If you need a new one, click **Create Key**

> **Note**: Your API key starts with `sk-ant-api03-...` and is approximately 100+ characters long.

---

## Section 3 — Create the Jenkins Credential

1. Open Jenkins in your browser → `http://localhost:8080`
2. Go to: **Manage Jenkins** → **Credentials** → **System** → **Global credentials (unrestricted)**
3. Click **Add Credentials**
4. Fill in the form:

   | Field | Value |
   |-------|-------|
   | **Kind** | Secret text |
   | **Scope** | Global |
   | **Secret** | Your Anthropic API key (`sk-ant-...`) |
   | **ID** | `claude-api-key` ← must be exactly this |
   | **Description** | Anthropic API Key for Claude AI Agent |

5. Click **Create**

> The `ID` field **must** be `claude-api-key` — the Jenkinsfile references it by this exact ID:
> ```groovy
> CLAUDE_API_KEY = credentials('claude-api-key')
> ```

---

## Section 4 — Environment Variables Reference

| Variable | Value | Where Set |
|----------|-------|-----------|
| `CLAUDE_API_KEY` | Your Anthropic API key (`sk-ant-...`) | Jenkins credential `claude-api-key` |
| `CLAUDE_MODEL` | `claude-sonnet-4-5` | Jenkinsfile `environment` block |

### Changing the Model (optional)

To use a cheaper/faster model for routine builds, edit the `Jenkinsfile` environment block:
```groovy
CLAUDE_MODEL = 'claude-3-5-haiku-20241022'   // ~10x cheaper, slightly less thorough
```

To use the most capable model for comprehensive reviews:
```groovy
CLAUDE_MODEL = 'claude-opus-4-5'              // most powerful, higher cost
```

---

## Section 5 — Standalone Verification

Before running the full Jenkins pipeline, verify the script works from your command prompt:

### Step 1 — Install dependencies
```cmd
cd C:\Users\PritiNayak\python\Bob-Squad-main\Bob-Squad-main
pip install -r requirements.txt
```

### Step 2 — Set your API key in the shell
```cmd
set CLAUDE_API_KEY=sk-ant-your-key-here
```

### Step 3 — Run the script directly
```cmd
python scripts\claude_code_review.py ^
    --api-key "%CLAUDE_API_KEY%" ^
    --model "claude-sonnet-4-5" ^
    --review-depth "STANDARD" ^
    --commit "HEAD" ^
    --output-file "test-review-report.json"
```

### Step 4 — Check the output
```cmd
type test-review-report.json
```

You should see a JSON file with `scores`, `issues`, `summary`, and `recommendations` keys.

### What to expect in the console:
```
🤖 Claude AI Agentic Code Review
   Commit:       HEAD
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
   ...
   ✅ Claude finished reasoning. Extracting review JSON...

📊 Generating report...
✅ Review report generated: test-review-report.json

============================================================
📈 REVIEW SUMMARY
============================================================
Code Quality:     78/100
Security:         85/100
Maintainability:  72/100
Overall Score:    78/100
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `anthropic.AuthenticationError` | API key is wrong or expired — check https://console.anthropic.com/settings/keys |
| `anthropic.RateLimitError` | Too many requests — wait 60 seconds and retry |
| `ModuleNotFoundError: anthropic` | Run `pip install anthropic>=0.40.0` |
| Agent exceeds max turns | Claude needed more info than the limit allowed — increase `max_turns` in the script |
| Jenkins shows `claude-api-key not found` | Credential ID in Jenkins must be exactly `claude-api-key` |

---

## Cost Estimate

| Model | Cost per code review (approx.) |
|-------|-------------------------------|
| `claude-3-5-haiku-20241022` | ~$0.01–0.05 |
| `claude-sonnet-4-5` *(default)* | ~$0.05–0.25 |
| `claude-opus-4-5` | ~$0.25–1.00 |

Costs depend on the number of files changed and review depth selected.
