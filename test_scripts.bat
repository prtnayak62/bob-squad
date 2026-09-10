@echo off
REM Test script for Jenkins Claude AI Agent Pipeline (Windows)
REM This script tests all components without requiring actual Claude credentials

echo ==========================================
echo Jenkins Claude AI Agent Pipeline Test Suite
echo ==========================================
echo.

set TESTS_PASSED=0
set TESTS_FAILED=0

REM Test 1: Check Python installation
echo Test 1: Checking Python installation...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [PASS] Python is installed
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] Python is not installed
    set /a TESTS_FAILED+=1
)
echo.

REM Test 2: Check required Python packages
echo Test 2: Checking Python dependencies...
python -c "import anthropic" >nul 2>&1
if %errorlevel% equ 0 (
    echo [PASS] anthropic module
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] anthropic module (run: pip install anthropic>=0.40.0)
    set /a TESTS_FAILED+=1
)

python -c "import requests" >nul 2>&1
if %errorlevel% equ 0 (
    echo [PASS] requests module
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] requests module
    set /a TESTS_FAILED+=1
)

python -c "import json" >nul 2>&1
if %errorlevel% equ 0 (
    echo [PASS] json module
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] json module
    set /a TESTS_FAILED+=1
)
echo.

REM Test 3: Check script files exist
echo Test 3: Checking script files...
if exist "scripts\claude_code_review.py" (
    echo [PASS] claude_code_review.py exists
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] claude_code_review.py exists
    set /a TESTS_FAILED+=1
)

if exist "scripts\quality_gate.py" (
    echo [PASS] quality_gate.py exists
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] quality_gate.py exists
    set /a TESTS_FAILED+=1
)

if exist "Jenkinsfile" (
    echo [PASS] Jenkinsfile exists
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] Jenkinsfile exists
    set /a TESTS_FAILED+=1
)
echo.

REM Test 4: Check configuration files
echo Test 4: Checking configuration files...
if exist "config\claude-config.json" (
    echo [PASS] claude-config.json exists
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] claude-config.json exists
    set /a TESTS_FAILED+=1
)

if exist "config\quality-thresholds.json" (
    echo [PASS] quality-thresholds.json exists
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] quality-thresholds.json exists
    set /a TESTS_FAILED+=1
)
echo.

REM Test 5: Test quality_gate.py script
echo Test 5: Testing quality_gate.py script...
python scripts\quality_gate.py --code-quality-score 75 --security-score 85 --maintainability-score 80 --code-threshold 70 --security-threshold 80 --maintainability-threshold 75 --output-file "test-quality-gate.json" >nul 2>&1
if %errorlevel% equ 0 (
    echo [PASS] quality_gate.py executes successfully
    set /a TESTS_PASSED+=1
    if exist "test-quality-gate.json" (
        del test-quality-gate.json
    )
) else (
    echo [FAIL] quality_gate.py executes successfully
    set /a TESTS_FAILED+=1
)
echo.

REM Test 6: Test claude_code_review.py help
echo Test 6: Testing claude_code_review.py help...
python scripts\claude_code_review.py --help >nul 2>&1
if %errorlevel% equ 0 (
    echo [PASS] claude_code_review.py help works
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] claude_code_review.py help works
    set /a TESTS_FAILED+=1
)
echo.

REM Summary
echo ==========================================
echo Test Summary
echo ==========================================
echo Tests Passed: %TESTS_PASSED%
echo Tests Failed: %TESTS_FAILED%
echo.

if %TESTS_FAILED% equ 0 (
    echo All tests passed!
    echo.
    echo Next steps:
    echo 1. Set up Jenkins credentials (see config\claude-credentials-setup.md)
    echo 2. Add your Anthropic API key as a Jenkins Secret Text credential (ID: claude-api-key)
    echo 3. Create Jenkins pipeline job
    echo 4. Run your first build
    exit /b 0
) else (
    echo Some tests failed. Please review the errors above.
    echo.
    echo Common fixes:
    echo 1. Install Python dependencies: pip install -r requirements.txt
    echo 2. Install Anthropic SDK: pip install anthropic>=0.40.0
    echo 3. Initialize Git repository: git init
    exit /b 1
)

@REM Made with Bob
