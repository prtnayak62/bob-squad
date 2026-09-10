@echo off
echo ========================================
echo Local Report Generation Test
echo ========================================
echo.
echo This script will generate reports locally
echo using the same process as Jenkins.
echo.
echo Prerequisites:
echo - Python installed
echo - CLAUDE_API_KEY environment variable set (set CLAUDE_API_KEY=sk-ant-...)
echo - All Python dependencies installed (pip install -r requirements.txt)
echo.
pause

echo.
echo Step 1: Running Claude AI Agent Code Review...
echo ----------------------------------------
python scripts\claude_code_review.py --api-key "%CLAUDE_API_KEY%" --base-url "https://api.nextgen-beta.ica.ibm.com/ica" --model "claude-sonnet-4-6" --commit HEAD --output-file review-report.json
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Code review failed!
    echo Check your Anthropic API key and network connection.
    pause
    exit /b 1
)
echo [SUCCESS] Code review completed
echo.

echo Step 2: Running Quality Gate Check...
echo ----------------------------------------
python scripts\quality_gate.py --review-file review-report.json --output-file quality-gate-result.json
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Quality gate check failed!
    pause
    exit /b 1
)
echo [SUCCESS] Quality gate check completed
echo.

echo Step 3: Generating HTML Report...
echo ----------------------------------------
for /f "tokens=*" %%a in ('git rev-parse --short HEAD 2^>nul') do set GIT_COMMIT=%%a
if "%GIT_COMMIT%"=="" set GIT_COMMIT=local-test

for /f "tokens=*" %%a in ('git config user.name 2^>nul') do set GIT_AUTHOR=%%a
if "%GIT_AUTHOR%"=="" set GIT_AUTHOR=Local User

python scripts\generate_report.py ^
    --review-file review-report.json ^
    --quality-gate-file quality-gate-result.json ^
    --commit %GIT_COMMIT% ^
    --author "%GIT_AUTHOR%" ^
    --output-file pipeline-report.html

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Report generation failed!
    pause
    exit /b 1
)
echo [SUCCESS] Report generated
echo.

echo ========================================
echo Generation Complete!
echo ========================================
echo.
echo Generated files:
echo   1. review-report.json
echo   2. quality-gate-result.json
echo   3. pipeline-report.html
echo.

echo Displaying review scores:
echo ----------------------------------------
type review-report.json | findstr /C:"code_quality" /C:"security" /C:"maintainability" /C:"overall"
echo.

echo Would you like to open the HTML report? (Y/N)
set /p OPEN_REPORT=
if /i "%OPEN_REPORT%"=="Y" (
    start pipeline-report.html
    echo Report opened in browser.
)

echo.
echo Note: This is the same report Jenkins would generate.
echo If scores look correct here, Jenkins should show the same.
echo.
pause

@REM Made with Bob
