@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Jenkins Claude AI Agent Pipeline - Local Execution
echo ========================================
echo.
echo This script simulates the Jenkins pipeline locally
echo.

REM Check if credentials are set
if "%CLAUDE_API_KEY%"=="" (
    echo ERROR: CLAUDE_API_KEY environment variable not set
    echo.
    echo Please set it first:
    echo   set CLAUDE_API_KEY=sk-ant-your-key-here
    echo.
    pause
    exit /b 1
)

REM Configuration
set CLAUDE_MODEL=claude-sonnet-4-6
set CLAUDE_BASE_URL=https://api.nextgen-beta.ica.ibm.com/ica
set CODE_QUALITY_THRESHOLD=70
set SECURITY_THRESHOLD=80
set MAINTAINABILITY_THRESHOLD=60
set REVIEW_DEPTH=STANDARD

echo Configuration:
echo   Model: %CLAUDE_MODEL%
echo   Review Depth: %REVIEW_DEPTH%
echo   Thresholds: Code=%CODE_QUALITY_THRESHOLD%, Security=%SECURITY_THRESHOLD%, Maintainability=%MAINTAINABILITY_THRESHOLD%
echo.
pause

REM Get Git information
echo ========================================
echo Stage 1: Checkout
echo ========================================
for /f "tokens=*" %%a in ('git rev-parse --short HEAD') do set GIT_COMMIT=%%a
for /f "tokens=*" %%a in ('git config user.name') do set GIT_AUTHOR=%%a
for /f "tokens=*" %%a in ('git log -1 --pretty^=%%B') do set GIT_MESSAGE=%%a

echo Commit: %GIT_COMMIT%
echo Author: %GIT_AUTHOR%
echo Message: %GIT_MESSAGE%
echo.
pause

REM Pre-Build Analysis
echo ========================================
echo Stage 2: Pre-Build Analysis
echo ========================================
echo Analyzing codebase...
git diff --name-only HEAD~1 HEAD
echo.
pause

REM Code Review
echo ========================================
echo Stage 3: Claude AI Agent Code Review
echo ========================================
echo Running agentic AI code review...
echo.

python scripts\claude_code_review.py ^
    --api-key %CLAUDE_API_KEY% ^
    --base-url %CLAUDE_BASE_URL% ^
    --model %CLAUDE_MODEL% ^
    --review-depth %REVIEW_DEPTH% ^
    --commit %GIT_COMMIT% ^
    --output-file review-report.json

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Code review failed!
    pause
    exit /b 1
)

echo.
echo Review completed successfully!
echo.
pause

REM Quality Gate
echo ========================================
echo Stage 4: Quality Gate Evaluation
echo ========================================
echo Evaluating quality thresholds...
echo.

python scripts\quality_gate.py ^
    --review-file review-report.json ^
    --code-threshold %CODE_QUALITY_THRESHOLD% ^
    --security-threshold %SECURITY_THRESHOLD% ^
    --maintainability-threshold %MAINTAINABILITY_THRESHOLD% ^
    --output-file quality-gate-result.json

set QUALITY_GATE_STATUS=%ERRORLEVEL%

if %QUALITY_GATE_STATUS% NEQ 0 (
    echo.
    echo WARNING: Quality Gate FAILED
    echo Continuing to generate report...
    echo.
) else (
    echo.
    echo Quality Gate PASSED!
    echo.
)

pause

REM Generate Report
echo ========================================
echo Stage 5: Generate Report
echo ========================================
echo Creating comprehensive HTML report...
echo.

python scripts\generate_report.py ^
    --review-file review-report.json ^
    --quality-gate-file quality-gate-result.json ^
    --commit %GIT_COMMIT% ^
    --author "%GIT_AUTHOR%" ^
    --output-file pipeline-report.html

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Report generation failed!
    pause
    exit /b 1
)

echo.
echo Report generated successfully!
echo.

REM Display Results
echo ========================================
echo Pipeline Results
echo ========================================
echo.
echo Generated Files:
echo   - review-report.json
echo   - quality-gate-result.json
echo   - pipeline-report.html
echo.

echo Extracting scores from review-report.json:
type review-report.json | findstr /C:"code_quality" /C:"security" /C:"maintainability" /C:"overall"
echo.

echo Quality Gate Status:
if %QUALITY_GATE_STATUS% EQU 0 (
    echo   [PASSED] All quality thresholds met
) else (
    echo   [FAILED] Some quality thresholds not met
)
echo.

echo ========================================
echo Opening HTML Report
echo ========================================
echo.
start pipeline-report.html
echo Report opened in browser
echo.

REM Final Status
echo ========================================
echo Pipeline Complete
echo ========================================
echo.

if %QUALITY_GATE_STATUS% NEQ 0 (
    echo Status: FAILED
    echo Reason: Quality Gate thresholds not met
    echo.
    echo Review the HTML report for details and fix the issues.
    echo.
    pause
    exit /b 1
) else (
    echo Status: SUCCESS
    echo All stages completed successfully!
    echo.
    pause
    exit /b 0
)

@REM Made with Bob
