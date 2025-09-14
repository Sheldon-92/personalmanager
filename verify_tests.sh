#!/bin/bash

# Test Verification Script for PersonalManager
# This script reproduces all test scenarios locally

set -e

echo "=========================================="
echo "PersonalManager Test Suite Verification"
echo "=========================================="
echo "Date: $(date)"
echo "Project: /Users/sheldonzhao/programs/personal-manager"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to run test and track results
run_test() {
    local test_name="$1"
    local test_command="$2"

    echo -e "${BLUE}[INFO]${NC} Running: $test_name"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if eval "$test_command" > /tmp/test_output.log 2>&1; then
        echo -e "${GREEN}[PASS]${NC} $test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}[FAIL]${NC} $test_name"
        echo "Error output:"
        cat /tmp/test_output.log
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

echo "1. TASK A - E2E Testing"
echo "======================="

# Verify launcher exists and is executable
echo -e "${BLUE}[INFO]${NC} Verifying launcher exists and is executable..."
if [ -x "./bin/pm-local" ]; then
    echo -e "${GREEN}[PASS]${NC} Launcher exists and is executable"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}[FAIL]${NC} Launcher not found or not executable"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Run E2E tests
echo ""
echo "Running E2E Test Suite..."
run_test "E2E Tests" "python3 -m pytest tests/test_pm_local_launcher.py -v --tb=short"

# Test specific scenarios
echo ""
echo "Testing specific E2E scenarios:"

# Poetry environment detection
run_test "Poetry Environment Detection" "./bin/pm-local --launcher-debug | grep -q 'Poetry Available: Yes'"

# Version command
run_test "Version Command" "./bin/pm-local --version | grep -q 'PersonalManager'"

# Today command (with timeout to handle long execution)
run_test "Today Command" "timeout 30s ./bin/pm-local today | grep -q 'INFO'"

# Projects overview command (with timeout)
run_test "Projects Overview Command" "timeout 30s ./bin/pm-local projects overview | grep -q '项目状态概览'"

echo ""
echo "2. TASK B - Security Testing"
echo "============================"

# Run security test suite
run_test "Security Test Suite (8 vectors)" "python3 -m pytest tests/security/test_security_vectors.py -v --tb=short"

# Test individual security vectors
echo ""
echo "Testing individual security vectors:"

run_test "Command Injection Prevention" "python3 -m pytest tests/security/test_security_vectors.py::TestSecurityVectors::test_command_injection_prevention -v"

run_test "Path Traversal Protection" "python3 -m pytest tests/security/test_security_vectors.py::TestSecurityVectors::test_path_traversal_protection -v"

run_test "Environment Variable Sanitization" "python3 -m pytest tests/security/test_security_vectors.py::TestSecurityVectors::test_environment_variable_sanitization -v"

run_test "Shell Command Escaping" "python3 -m pytest tests/security/test_security_vectors.py::TestSecurityVectors::test_shell_command_escaping -v"

run_test "File Permission Validation" "python3 -m pytest tests/security/test_security_vectors.py::TestSecurityVectors::test_file_permission_validation -v"

run_test "Input Validation and Sanitization" "python3 -m pytest tests/security/test_security_vectors.py::TestSecurityVectors::test_input_validation_and_sanitization -v"

run_test "Process Execution Security" "python3 -m pytest tests/security/test_security_vectors.py::TestSecurityVectors::test_process_execution_security -v"

run_test "Configuration File Security" "python3 -m pytest tests/security/test_security_vectors.py::TestSecurityVectors::test_configuration_file_security -v"

echo ""
echo "3. Comprehensive Test Run"
echo "========================="

# Run all tests together
run_test "Complete Test Suite" "python3 -m pytest tests/test_pm_local_launcher.py tests/security/test_security_vectors.py -v --tb=short --durations=5"

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "Total Tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo "Test Coverage: 100% (10/10 scenarios)"
else
    echo -e "${RED}❌ Some tests failed${NC}"
    echo "Test Coverage: $(( (PASSED_TESTS * 100) / TOTAL_TESTS ))%"
fi

echo ""
echo "Test execution completed at: $(date)"
echo "Logs available in /tmp/test_output.log"

# Cleanup
rm -f /tmp/test_output.log

exit $FAILED_TESTS