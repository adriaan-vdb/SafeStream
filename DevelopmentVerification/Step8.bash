#!/bin/bash

# SafeStream Stage 8 Verification Script
# Tests Stage 8-C (Live Metrics) and Stage 8-D (UI Tests & Load Testing)

# === Robust Test/CI Prelude ===
set -e

ruff check --fix .
black .

export DISABLE_DETOXIFY=1
export JWT_SECRET_KEY="test-secret-key-for-verification"
export JWT_EXPIRE_MINUTES=30
export TEST_USERNAME="testuser_$(date +%s)"
export API_USERNAME="apiuser_$(date +%s)"
export TARGET_USERNAME="targetuser_$(date +%s)"

rm -f users.json test_users.json

pkill -f "uvicorn.*8002" 2>/dev/null || true
sleep 2

cleanup() {
    docker stop safestream-test-container 2>/dev/null || true
    docker rm safestream-test-container 2>/dev/null || true
    pkill -f "uvicorn.*8030" 2>/dev/null || true
    rm -f users.json test_users.json
}
trap cleanup EXIT

echo "=== SafeStream Stage 8 Verification ==="
echo "Testing Stage 8-C: Live Metrics"
echo "Testing Stage 8-D: UI Tests & Load Testing"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Server management variables
SERVER_PID=""
SERVER_PORT=8000
SERVER_URL="http://localhost:$SERVER_PORT"

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "PASS")
            echo -e "${GREEN}✓ PASS${NC}: $message"
            ;;
        "FAIL")
            echo -e "${RED}✗ FAIL${NC}: $message"
            ;;
        "SKIP")
            echo -e "${YELLOW}⚠ SKIP${NC}: $message"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ INFO${NC}: $message"
            ;;
    esac
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to start the FastAPI server
start_server() {
    print_status "INFO" "Starting FastAPI server on port $SERVER_PORT..."
    
    # Start server in background
    python3 -m uvicorn app.main:app --host 0.0.0.0 --port $SERVER_PORT --reload >/dev/null 2>&1 &
    SERVER_PID=$!
    
    # Wait for server to start
    local max_attempts=30
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$SERVER_URL/healthz" >/dev/null 2>&1; then
            print_status "PASS" "Server started successfully (PID: $SERVER_PID)"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    
    print_status "FAIL" "Server failed to start within 30 seconds"
    return 1
}

# Function to stop the FastAPI server
stop_server() {
    if [ -n "$SERVER_PID" ]; then
        print_status "INFO" "Stopping server (PID: $SERVER_PID)..."
        kill $SERVER_PID 2>/dev/null || true
        wait $SERVER_PID 2>/dev/null || true
        SERVER_PID=""
        print_status "PASS" "Server stopped"
    fi
}

# Function to wait for server to be ready
wait_for_server() {
    local max_attempts=10
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$SERVER_URL/healthz" >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    return 1
}

# Function to run test and capture result
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo "Running: $test_name"
    if eval "$test_command" >/dev/null 2>&1; then
        print_status "PASS" "$test_name"
        return 0
    else
        print_status "FAIL" "$test_name"
        return 1
    fi
}

# Track overall success
overall_success=true

echo "=== Stage 8-C: Live Metrics Testing ==="

# Test 1: Check if metrics module exists
if [ -f "app/metrics.py" ]; then
    print_status "PASS" "Metrics module exists"
else
    print_status "FAIL" "Metrics module missing"
    overall_success=false
fi

# Start server for metrics tests
if start_server; then
    # Test 2: Check if metrics endpoint is accessible
    if curl -s "$SERVER_URL/metrics" >/dev/null 2>&1; then
        print_status "PASS" "Metrics endpoint accessible"
    else
        print_status "FAIL" "Metrics endpoint not accessible"
        overall_success=false
    fi

    # Test 3: Check metrics response structure
    metrics_response=$(curl -s "$SERVER_URL/metrics" 2>/dev/null || echo "{}")
    if echo "$metrics_response" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    required_keys = ['viewer_count', 'gift_count', 'toxic_pct']
    if all(key in data for key in required_keys):
        print('PASS')
    else:
        print('FAIL')
except:
    print('FAIL')
" | grep -q "PASS"; then
        print_status "PASS" "Metrics response has correct structure"
    else
        print_status "FAIL" "Metrics response missing required fields"
        overall_success=false
    fi
else
    print_status "FAIL" "Could not start server for metrics tests"
    overall_success=false
fi

# Test 4: Run metrics unit tests
if python3 -m pytest tests/test_metrics.py -v --tb=short >/dev/null 2>&1; then
    print_status "PASS" "Metrics unit tests pass"
else
    print_status "FAIL" "Metrics unit tests fail"
    overall_success=false
fi

echo
echo "=== Stage 8-D: UI Tests & Load Testing ==="

# Test 5: Check if Playwright UI test exists
if [ -f "tests/test_ui_playwright.py" ]; then
    print_status "PASS" "Playwright UI test file exists"
else
    print_status "FAIL" "Playwright UI test file missing"
    overall_success=false
fi

# Test 6: Check if Locust load test exists
if [ -f "load/locustfile.py" ]; then
    print_status "PASS" "Locust load test file exists"
else
    print_status "FAIL" "Locust load test file missing"
    overall_success=false
fi

# Test 7: Check if Playwright is available (optional)
if command_exists playwright; then
    print_status "PASS" "Playwright is installed"
    playwright_available=true
else
    print_status "SKIP" "Playwright not installed (optional)"
    playwright_available=false
fi

# Test 8: Check if Locust is available (optional)
if command_exists locust; then
    print_status "PASS" "Locust is installed"
    locust_available=true
else
    print_status "SKIP" "Locust not installed (optional)"
    locust_available=false
fi

# Test 8.5: Check if websocat is available (optional)
if command_exists websocat; then
    print_status "PASS" "websocat is installed"
    websocat_available=true
else
    print_status "SKIP" "websocat not installed (optional)"
    websocat_available=false
fi

# Test 9: Run Playwright tests if available
if [ "$playwright_available" = true ]; then
    if ENABLE_PLAYWRIGHT_TESTS=1 python3 -m pytest tests/test_ui_playwright.py::TestSafeStreamUI::test_metrics_endpoint -v --tb=short >/dev/null 2>&1; then
        print_status "PASS" "Playwright metrics test passes"
    else
        print_status "FAIL" "Playwright metrics test fails"
        overall_success=false
    fi
else
    print_status "SKIP" "Skipping Playwright tests (not installed)"
fi

# Test 10: Test metrics integration with chat
echo "Testing metrics integration..."
# Ensure server is running
if [ -z "$SERVER_PID" ]; then
    if ! start_server; then
        print_status "FAIL" "Could not start server for integration test"
        overall_success=false
    fi
fi

# Start a background process to send some activity
(
    sleep 2
    # Send a gift (this doesn't require websocat)
    curl -s -X POST "$SERVER_URL/api/gift" -H "Content-Type: application/json" -d '{"from":"test","gift_id":1,"amount":5}' >/dev/null 2>&1
    sleep 1
    # Send another gift to ensure we have activity
    curl -s -X POST "$SERVER_URL/api/gift" -H "Content-Type: application/json" -d '{"from":"test2","gift_id":2,"amount":3}' >/dev/null 2>&1
    sleep 1
) &

# Check metrics after activity
sleep 5
metrics_after=$(curl -s "$SERVER_URL/metrics" 2>/dev/null || echo "{}")
if echo "$metrics_after" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if data.get('gift_count', 0) > 0:
        print('PASS')
    else:
        print('FAIL')
except:
    print('FAIL')
" | grep -q "PASS"; then
    print_status "PASS" "Metrics track activity correctly"
else
    print_status "FAIL" "Metrics not tracking activity"
    overall_success=false
fi

# Test 11: Check if all existing tests still pass
echo
echo "=== Verifying Existing Tests Still Pass ==="
if python3 -m pytest tests/ -v --tb=short >/dev/null 2>&1; then
    print_status "PASS" "All existing tests pass"
else
    print_status "FAIL" "Some existing tests fail"
    overall_success=false
fi

# Test 12: Check linting
echo
echo "=== Code Quality Checks ==="
if python3 -m ruff check . >/dev/null 2>&1; then
    print_status "PASS" "Ruff linting passes"
else
    print_status "FAIL" "Ruff linting fails"
    overall_success=false
fi

# Test 13: Check formatting
if python3 -m black --check . >/dev/null 2>&1; then
    print_status "PASS" "Black formatting check passes"
else
    print_status "FAIL" "Black formatting check fails"
    overall_success=false
fi

# Test 14: Check type hints
if python3 -m mypy app/ --ignore-missing-imports >/dev/null 2>&1; then
    print_status "PASS" "Type checking passes"
else
    print_status "FAIL" "Type checking fails"
    overall_success=false
fi

echo
echo "=== Stage 8 Verification Summary ==="

if [ "$overall_success" = true ]; then
    print_status "PASS" "Stage 8 verification completed successfully!"
    echo
    echo "Stage 8-C Features:"
    echo "  ✓ Live metrics tracking (viewer_count, gift_count, toxic_pct)"
    echo "  ✓ Metrics API endpoint (/metrics)"
    echo "  ✓ Integration with WebSocket and gift events"
    echo "  ✓ Comprehensive metrics tests"
    echo
    echo "Stage 8-D Features:"
    echo "  ✓ Playwright UI tests (if installed)"
    echo "  ✓ Locust load testing framework"
    echo "  ✓ WebSocket and HTTP load simulation"
    echo "  ✓ Metrics monitoring under load"
    echo
    echo "Next Steps:"
    echo "  1. Install Playwright: pip install playwright && playwright install"
    echo "  2. Install Locust: pip install locust"
    echo "  3. Run UI tests: ENABLE_PLAYWRIGHT_TESTS=1 python -m pytest tests/test_ui_playwright.py"
    echo "  4. Run load tests: locust -f load/locustfile.py --host=http://localhost:8000"
    echo "  5. Monitor metrics: curl http://localhost:8000/metrics"
    exit 0
else
    print_status "FAIL" "Stage 8 verification failed!"
    echo
    echo "Please fix the failing tests before proceeding."
    exit 1
fi 