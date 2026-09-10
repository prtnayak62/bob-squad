#!/bin/bash
# Test script for Jenkins Claude AI Agent Pipeline
# This script tests all components without requiring actual Claude credentials

set -e  # Exit on error

echo "=========================================="
echo "Jenkins Claude AI Agent Pipeline Test Suite"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print test result
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASSED${NC}: $2"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC}: $2"
        ((TESTS_FAILED++))
    fi
}

# Test 1: Check Python installation
echo "Test 1: Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_result 0 "Python is installed ($PYTHON_VERSION)"
else
    print_result 1 "Python is not installed"
fi
echo ""

# Test 2: Check required Python packages
echo "Test 2: Checking Python dependencies..."
python3 -c "import anthropic" 2>/dev/null
print_result $? "anthropic module (install: pip install anthropic>=0.40.0)"

python3 -c "import requests" 2>/dev/null
print_result $? "requests module"

python3 -c "import json" 2>/dev/null
print_result $? "json module"

python3 -c "import argparse" 2>/dev/null
print_result $? "argparse module"
echo ""

# Test 3: Check script files exist
echo "Test 3: Checking script files..."
[ -f "scripts/claude_code_review.py" ]
print_result $? "claude_code_review.py exists"

[ -f "scripts/quality_gate.py" ]
print_result $? "quality_gate.py exists"

[ -f "scripts/generate_report.py" ]
print_result $? "generate_report.py exists"

[ -f "Jenkinsfile" ]
print_result $? "Jenkinsfile exists"
echo ""

# Test 4: Check configuration files
echo "Test 4: Checking configuration files..."
[ -f "config/claude-config.json" ]
print_result $? "claude-config.json exists"

[ -f "config/quality-thresholds.json" ]
print_result $? "quality-thresholds.json exists"
echo ""

# Test 5: Validate JSON configuration files
echo "Test 5: Validating JSON configuration files..."
python3 -c "import json; json.load(open('config/claude-config.json'))" 2>/dev/null
print_result $? "claude-config.json is valid JSON"

python3 -c "import json; json.load(open('config/quality-thresholds.json'))" 2>/dev/null
print_result $? "quality-thresholds.json is valid JSON"
echo ""

# Test 6: Test quality_gate.py script
echo "Test 6: Testing quality_gate.py script..."
python3 scripts/quality_gate.py \
    --code-quality-score 75 \
    --security-score 85 \
    --maintainability-score 80 \
    --code-threshold 70 \
    --security-threshold 80 \
    --maintainability-threshold 75 \
    --output-file "test-quality-gate.json" > /dev/null 2>&1
print_result $? "quality_gate.py executes successfully"

if [ -f "test-quality-gate.json" ]; then
    python3 -c "import json; data=json.load(open('test-quality-gate.json')); exit(0 if data['status'] == 'PASSED' else 1)" 2>/dev/null
    print_result $? "quality_gate.py produces valid output"
    rm -f test-quality-gate.json
fi
echo ""

# Test 7: Test claude_code_review.py help
echo "Test 7: Testing claude_code_review.py help..."
python3 scripts/claude_code_review.py --help > /dev/null 2>&1
print_result $? "claude_code_review.py help works"
echo ""

# Test 8: Check Git repository
echo "Test 8: Checking Git repository..."
if git rev-parse --git-dir > /dev/null 2>&1; then
    print_result 0 "Git repository initialized"
    
    # Check if there are commits
    if git log -1 > /dev/null 2>&1; then
        print_result 0 "Git repository has commits"
    else
        print_result 1 "Git repository has no commits"
    fi
else
    print_result 1 "Not a Git repository"
fi
echo ""

# Test 9: Test script permissions
echo "Test 9: Checking script permissions..."
[ -x "scripts/claude_code_review.py" ] || chmod +x scripts/claude_code_review.py
print_result $? "claude_code_review.py is executable"

[ -x "scripts/quality_gate.py" ] || chmod +x scripts/quality_gate.py
print_result $? "quality_gate.py is executable"

[ -x "scripts/generate_report.py" ] || chmod +x scripts/generate_report.py
print_result $? "generate_report.py is executable"
echo ""

# Test 10: Simulate quality gate scenarios
echo "Test 10: Testing quality gate scenarios..."

# Scenario 1: All pass
python3 scripts/quality_gate.py \
    --code-quality-score 85 \
    --security-score 90 \
    --maintainability-score 88 \
    --output-file "test-pass.json" > /dev/null 2>&1
if [ -f "test-pass.json" ]; then
    python3 -c "import json; data=json.load(open('test-pass.json')); exit(0 if data['status'] == 'PASSED' else 1)" 2>/dev/null
    print_result $? "Quality gate PASSED scenario"
    rm -f test-pass.json
fi

# Scenario 2: Failure
python3 scripts/quality_gate.py \
    --code-quality-score 60 \
    --security-score 65 \
    --maintainability-score 55 \
    --output-file "test-fail.json" > /dev/null 2>&1
if [ -f "test-fail.json" ]; then
    python3 -c "import json; data=json.load(open('test-fail.json')); exit(0 if data['status'] == 'FAILED' else 1)" 2>/dev/null
    print_result $? "Quality gate FAILED scenario"
    rm -f test-fail.json
fi

# Scenario 3: Warning
python3 scripts/quality_gate.py \
    --code-quality-score 72 \
    --security-score 82 \
    --maintainability-score 77 \
    --output-file "test-warning.json" > /dev/null 2>&1
if [ -f "test-warning.json" ]; then
    python3 -c "import json; data=json.load(open('test-warning.json')); exit(0 if data['status'] == 'WARNING' else 1)" 2>/dev/null
    print_result $? "Quality gate WARNING scenario"
    rm -f test-warning.json
fi
echo ""

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "Tests Passed: ${GREEN}${TESTS_PASSED}${NC}"
echo -e "Tests Failed: ${RED}${TESTS_FAILED}${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Set up Jenkins credentials (see config/claude-credentials-setup.md)"
    echo "2. Add your Anthropic API key as a Jenkins Secret Text credential (ID: claude-api-key)"
    echo "3. Create Jenkins pipeline job"
    echo "4. Run your first build"
    exit 0
else
    echo -e "${RED}Some tests failed. Please review the errors above.${NC}"
    echo ""
    echo "Common fixes:"
    echo "1. Install Python dependencies: pip3 install -r requirements.txt"
    echo "2. Install Anthropic SDK: pip3 install anthropic>=0.40.0"
    echo "3. Initialize Git repository: git init"
    echo "4. Make scripts executable: chmod +x scripts/*.py"
    exit 1
fi

# Made with Bob
