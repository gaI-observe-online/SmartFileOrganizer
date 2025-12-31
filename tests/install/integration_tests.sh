#!/bin/bash
# Integration tests for install/uninstall scripts
# Run manually: ./tests/install/integration_tests.sh

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║      SmartFileOrganizer - Integration Tests                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Repository: $REPO_ROOT"
echo ""

# Test helper functions
test_start() {
    echo -n "  Testing: $1... "
    TESTS_RUN=$((TESTS_RUN + 1))
}

test_pass() {
    echo -e "${GREEN}✓${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

test_fail() {
    echo -e "${RED}✗${NC}"
    if [ $# -gt 0 ]; then
        echo "    Error: $1"
    fi
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

section() {
    echo ""
    echo "─────────────────────────────────────────────────────────"
    echo "  $1"
    echo "─────────────────────────────────────────────────────────"
    echo ""
}

# Test 1: Script syntax
section "SYNTAX CHECKS"

test_start "install.sh syntax"
bash -n "$REPO_ROOT/install.sh" < /dev/null > /dev/null 2>&1 && test_pass || test_fail "Syntax error in install.sh"

test_start "uninstall.sh syntax"
bash -n "$REPO_ROOT/uninstall.sh" < /dev/null > /dev/null 2>&1 && test_pass || test_fail "Syntax error in uninstall.sh"

test_start "diagnose.sh syntax"
bash -n "$REPO_ROOT/diagnose.sh" < /dev/null > /dev/null 2>&1 && test_pass || test_fail "Syntax error in diagnose.sh"

# Test 2: File permissions
section "FILE PERMISSIONS"

test_start "install.sh is executable"
if [ -x "$REPO_ROOT/install.sh" ]; then
    test_pass
else
    test_fail "install.sh is not executable"
fi

test_start "uninstall.sh is executable"
if [ -x "$REPO_ROOT/uninstall.sh" ]; then
    test_pass
else
    test_fail "uninstall.sh is not executable"
fi

test_start "diagnose.sh is executable"
if [ -x "$REPO_ROOT/diagnose.sh" ]; then
    test_pass
else
    test_fail "diagnose.sh is not executable"
fi

# Test 3: Required files
section "REQUIRED FILES"

test_start "requirements.txt exists"
if [ -f "$REPO_ROOT/requirements.txt" ]; then
    test_pass
else
    test_fail "requirements.txt not found"
fi

test_start "config.example.json exists"
if [ -f "$REPO_ROOT/config.example.json" ]; then
    test_pass
else
    test_fail "config.example.json not found"
fi

test_start "organize.py exists"
if [ -f "$REPO_ROOT/organize.py" ]; then
    test_pass
else
    test_fail "organize.py not found"
fi

# Test 4: JSON validity
section "JSON VALIDATION"

test_start "config.example.json is valid JSON"
if python3 -c "import json; json.load(open('$REPO_ROOT/config.example.json'))" 2>/dev/null; then
    test_pass
else
    test_fail "config.example.json is invalid JSON"
fi

# Test 5: Dependencies
section "SYSTEM DEPENDENCIES"

test_start "Python 3.8+ available"
if command -v python3 &> /dev/null; then
    PY_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if [ "$(printf '%s\n' "3.8" "$PY_VERSION" | sort -V | head -n1)" == "3.8" ]; then
        test_pass
    else
        test_fail "Python version $PY_VERSION < 3.8"
    fi
else
    test_fail "Python 3 not found"
fi

test_start "pip available"
if command -v pip3 &> /dev/null || python3 -m pip --version &> /dev/null; then
    test_pass
else
    test_fail "pip not found"
fi

test_start "venv module available"
if python3 -m venv --help &> /dev/null; then
    test_pass
else
    test_fail "venv module not available"
fi

test_start "curl available"
if command -v curl &> /dev/null; then
    test_pass
else
    test_fail "curl not found"
fi

# Test 6: Script contents
section "SCRIPT CONTENTS"

test_start "install.sh has logging functions"
if grep -q "log_info\|log_error\|log_warn" "$REPO_ROOT/install.sh"; then
    test_pass
else
    test_fail "Missing logging functions"
fi

test_start "install.sh has state management"
if grep -q "save_state\|load_state" "$REPO_ROOT/install.sh"; then
    test_pass
else
    test_fail "Missing state management"
fi

test_start "install.sh has rollback"
if grep -q "cleanup_on_failure" "$REPO_ROOT/install.sh"; then
    test_pass
else
    test_fail "Missing rollback function"
fi

test_start "install.sh has health checks"
if grep -q "health_check" "$REPO_ROOT/install.sh"; then
    test_pass
else
    test_fail "Missing health checks"
fi

test_start "install.sh uses error trap"
if grep -q "trap.*ERR" "$REPO_ROOT/install.sh"; then
    test_pass
else
    test_fail "Missing error trap"
fi

# Test 7: Requirements
section "REQUIREMENTS FILE"

test_start "requirements.txt has content"
if [ -s "$REPO_ROOT/requirements.txt" ]; then
    LINE_COUNT=$(grep -v '^#' "$REPO_ROOT/requirements.txt" | grep -v '^$' | wc -l)
    if [ "$LINE_COUNT" -gt 0 ]; then
        test_pass
    else
        test_fail "requirements.txt has no dependencies"
    fi
else
    test_fail "requirements.txt is empty"
fi

test_start "requirements.txt has version pins"
if grep -q "==" "$REPO_ROOT/requirements.txt"; then
    test_pass
else
    test_fail "requirements.txt should have version pins (==)"
fi

# Test 8: Test runner (if pytest available)
section "UNIT TESTS"

if command -v pytest &> /dev/null; then
    test_start "Python unit tests for installation"
    if pytest "$SCRIPT_DIR/test_installation.py" -v --tb=short 2>/dev/null; then
        test_pass
    else
        test_fail "Some unit tests failed (run pytest for details)"
    fi
else
    echo "  Skipping: pytest not available"
fi

# Summary
section "TEST SUMMARY"

echo "  Tests run:    $TESTS_RUN"
echo -e "  Tests passed: ${GREEN}$TESTS_PASSED${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "  Tests failed: ${RED}$TESTS_FAILED${NC}"
else
    echo -e "  Tests failed: $TESTS_FAILED"
fi
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║          All Tests Passed! ✓                                ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║          Some Tests Failed ✗                                ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
    exit 1
fi
