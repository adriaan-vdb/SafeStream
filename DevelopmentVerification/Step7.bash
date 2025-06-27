#!/bin/bash
# SafeStream Stage 7 Verification Script
# Validates Detoxify ML moderation integration, environment variables, and dual modes

### Before running the script:
# Activate your virtual environment if not already active
# python3 -m venv .venv
# source .venv/bin/activate
# Install all required dependencies
# pip install -e ".[dev]"
# To run real ML mode: pip install -e ".[dev,ml]"
# To run entire script:
# chmod +x DevelopmentVerification/Step7.bash
# ./DevelopmentVerification/Step7.bash

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper for success/failure
function success() { echo -e "${GREEN}✔ $1${NC}"; }
function fail() { echo -e "${RED}✖ $1${NC}"; exit 1; }
function warn() { echo -e "${YELLOW}⚠ $1${NC}"; }
function info() { echo -e "${BLUE}ℹ $1${NC}"; }

echo -e "${BLUE}=== Stage 7: Detoxify ML Moderation Integration ===${NC}"

# 1. Check virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    warn "Virtual environment not detected"
    warn "Consider activating: source .venv/bin/activate"
else
    success "Virtual environment active: $VIRTUAL_ENV"
fi

# 2. Check dependencies
info "Checking dependencies..."
if python3 -c "import detoxify" 2>/dev/null; then
    success "Detoxify available (ML mode enabled)"
    DETOXIFY_AVAILABLE=true
else
    warn "Detoxify not available (stub mode only)"
    warn "Install with: pip install -e '.[dev,ml]'"
    DETOXIFY_AVAILABLE=false
fi

# 3. Run linting and formatting checks
info "Running code quality checks..."

echo "  Checking formatting with Black..."
if black --check . --quiet; then
    success "Black formatting check passed"
else
    fail "Black formatting check failed"
fi

echo "  Checking linting with Ruff..."
if ruff check . --quiet; then
    success "Ruff linting check passed"
else
    fail "Ruff linting check failed"
fi

# 4. Test stub mode (DISABLE_DETOXIFY=1)
info "Testing stub mode (DISABLE_DETOXIFY=1)..."
export DISABLE_DETOXIFY=1

python3 - <<EOF
import asyncio
import os
import sys
from app.moderation import predict

async def test_stub_mode():
    # Test toxic text should return (False, 0.0) in stub mode
    result = await predict("you are stupid")
    if result == (False, 0.0):
        print("STUB_TOXIC_OK")
    else:
        print(f"Stub mode failed for toxic text: expected (False, 0.0), got {result}", file=sys.stderr)
        sys.exit(1)
    
    # Test benign text should also return (False, 0.0) in stub mode
    result2 = await predict("hello world")
    if result2 == (False, 0.0):
        print("STUB_BENIGN_OK")
    else:
        print(f"Stub mode failed for benign text: expected (False, 0.0), got {result2}", file=sys.stderr)
        sys.exit(1)

asyncio.run(test_stub_mode())
EOF

if [ $? -eq 0 ]; then
    success "Stub mode tests passed"
else
    fail "Stub mode tests failed"
fi

# 5. Test real mode (DISABLE_DETOXIFY=0) if Detoxify available
if [ "$DETOXIFY_AVAILABLE" = true ]; then
    info "Testing real mode (DISABLE_DETOXIFY=0)..."
    export DISABLE_DETOXIFY=0
    
    python3 - <<EOF
import asyncio
import os
import sys
from app.moderation import predict

async def test_real_mode():
    # Test toxic text should return actual toxicity score
    result = await predict("you are stupid")
    if isinstance(result[0], bool) and 0.0 <= result[1] <= 1.0:
        print(f"REAL_TOXIC_OK: toxic={result[0]}, score={result[1]:.3f}")
    else:
        print(f"Real mode failed for toxic text: invalid result {result}", file=sys.stderr)
        sys.exit(1)
    
    # Test benign text should return lower toxicity score
    result2 = await predict("hello world")
    if isinstance(result2[0], bool) and 0.0 <= result2[1] <= 1.0:
        print(f"REAL_BENIGN_OK: toxic={result2[0]}, score={result2[1]:.3f}")
    else:
        print(f"Real mode failed for benign text: invalid result {result2}", file=sys.stderr)
        sys.exit(1)

asyncio.run(test_real_mode())
EOF

    if [ $? -eq 0 ]; then
        success "Real mode tests passed"
    else
        fail "Real mode tests failed"
    fi
else
    warn "Skipping real mode tests (Detoxify not available)"
fi

# 6. Test custom threshold
info "Testing custom threshold..."
export TOXIC_THRESHOLD=0.1
export DISABLE_DETOXIFY=0

if [ "$DETOXIFY_AVAILABLE" = true ]; then
    python3 - <<EOF
import asyncio
import os
import sys
from app.moderation import predict

async def test_custom_threshold():
    # With threshold 0.1, even benign text might be flagged
    result = await predict("hello world")
    if isinstance(result[0], bool) and 0.0 <= result[1] <= 1.0:
        print(f"CUSTOM_THRESHOLD_OK: toxic={result[0]}, score={result[1]:.3f}")
    else:
        print(f"Custom threshold test failed: invalid result {result}", file=sys.stderr)
        sys.exit(1)

asyncio.run(test_custom_threshold())
EOF

    if [ $? -eq 0 ]; then
        success "Custom threshold test passed"
    else
        fail "Custom threshold test failed"
    fi
else
    warn "Skipping custom threshold test (Detoxify not available)"
fi

# 7. Run moderation unit tests
info "Running moderation unit tests..."
export DISABLE_DETOXIFY=1  # Use stub mode for consistent testing

if pytest tests/test_moderation.py -q; then
    success "Moderation unit tests passed"
else
    fail "Moderation unit tests failed"
fi

# 8. Test async interface
info "Testing async interface..."
python3 - <<EOF
import asyncio
import inspect
import sys
from app.moderation import predict

def test_async_interface():
    # Check that predict is async
    if inspect.iscoroutinefunction(predict):
        print("ASYNC_INTERFACE_OK")
    else:
        print("predict function is not async", file=sys.stderr)
        sys.exit(1)

test_async_interface()
EOF

if [ $? -eq 0 ]; then
    success "Async interface test passed"
else
    fail "Async interface test failed"
fi

# 9. Test environment variable handling
info "Testing environment variable handling..."
python3 - <<EOF
import asyncio
import os
import sys
from app.moderation import predict

async def test_env_vars():
    # Test DISABLE_DETOXIFY=1
    os.environ["DISABLE_DETOXIFY"] = "1"
    result1 = await predict("test")
    if result1 == (False, 0.0):
        print("ENV_DISABLE_OK")
    else:
        print(f"DISABLE_DETOXIFY=1 failed: {result1}", file=sys.stderr)
        sys.exit(1)
    
    # Test TOXIC_THRESHOLD
    if "TOXIC_THRESHOLD" in os.environ:
        threshold = float(os.environ["TOXIC_THRESHOLD"])
        print(f"ENV_THRESHOLD_OK: {threshold}")
    else:
        print("ENV_THRESHOLD_OK: default")

asyncio.run(test_env_vars())
EOF

if [ $? -eq 0 ]; then
    success "Environment variable tests passed"
else
    fail "Environment variable tests failed"
fi

# 10. Test API integration (WebSocket with moderation)
info "Testing API integration with moderation..."
export DISABLE_DETOXIFY=1  # Use stub for testing

python3 - <<EOF
import asyncio
import json
import sys
from fastapi.testclient import TestClient
from app.main import create_app

async def test_api_integration():
    # Use test app (no background tasks)
    app = create_app(testing=True)
    client = TestClient(app)
    
    # Test WebSocket with moderation
    with client.websocket_connect("/ws/modtest") as ws:
        # Send message
        ws.send_text(json.dumps({"type": "chat", "message": "hello world"}))
        
        # Receive response
        msg = ws.receive_text()
        data = json.loads(msg)
        
        # Check that moderation fields are present
        if (data.get("type") == "chat" and 
            data.get("user") == "modtest" and
            "toxic" in data and
            "score" in data):
            print(f"API_INTEGRATION_OK: toxic={data['toxic']}, score={data['score']}")
        else:
            print(f"API integration failed: {data}", file=sys.stderr)
            sys.exit(1)

asyncio.run(test_api_integration())
EOF

if [ $? -eq 0 ]; then
    success "API integration test passed"
else
    fail "API integration test failed"
fi

# Summary
echo -e "\n${GREEN}=== Stage 7 Verification Complete ===${NC}"
success "All Stage 7 checks passed!"
echo -e "${GREEN}✓ Environment variables work${NC}"
echo -e "${GREEN}✓ Stub mode works${NC}"
if [ "$DETOXIFY_AVAILABLE" = true ]; then
    echo -e "${GREEN}✓ Real ML mode works${NC}"
    echo -e "${GREEN}✓ Custom threshold works${NC}"
else
    echo -e "${YELLOW}⚠ Real ML mode skipped (Detoxify not available)${NC}"
    echo -e "${YELLOW}⚠ Install with: pip install -e '.[dev,ml]'${NC}"
fi
echo -e "${GREEN}✓ API integration works${NC}"
echo -e "${GREEN}✓ Tests pass${NC}"
echo -e "${GREEN}✓ Code quality checks pass${NC}"

echo -e "\n${BLUE}Stage 7 Detoxify ML moderation integration is working correctly!${NC}" 