#!/bin/bash
# SafeStream Stage 6 Verification Script
# Validates random gift generator, config, and service health

### Before running the script:
# Activate your virtual environment if not already active
# python3 -m venv .venv
# source .venv/bin/activate
# Install all required dependencies
# pip install -e ".[dev]"
# To run entire script:
# chmod +x DevelopmentVerification/Step6.bash
# ./DevelopmentVerification/Step6.bash

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper for success/failure
function success() { echo -e "${GREEN}✔ $1${NC}"; }
function fail() { echo -e "${RED}✖ $1${NC}"; exit 1; }
function warn() { echo -e "${YELLOW}⚠ $1${NC}"; }

# 1. Check required environment variables
if [ -f .env ]; then
    source .env
fi

if [ -z "$GIFT_INTERVAL_SECS" ]; then
    warn "GIFT_INTERVAL_SECS not set, using default (15)"
else
    success "GIFT_INTERVAL_SECS is set to $GIFT_INTERVAL_SECS"
fi

# 2. Run Stage 6-specific tests
if pytest tests/test_random_gift.py -q; then
    success "Random gift producer tests passed"
else
    fail "Random gift producer tests failed"
fi

# 3. Validate WebSocket gift event behavior (basic check)
python3 - <<EOF
import os
import sys
import time
from fastapi.testclient import TestClient
from app.main import create_app
import json

# Use test app (no background tasks)
app = create_app(testing=True)
client = TestClient(app)

# Test that WebSocket endpoint exists and can be reached
try:
    # Test basic WebSocket connectivity (without waiting for gifts)
    with client.websocket_connect("/ws/step6test") as ws:
        # Send a test message
        ws.send_text(json.dumps({"type": "chat", "message": "test"}))
        
        # Receive the response
        msg = ws.receive_text()
        data = json.loads(msg)
        
        if data.get("type") == "chat" and data.get("user") == "step6test":
            print("WEBSOCKET_OK")
            sys.exit(0)
        else:
            print(f"Unexpected message format: {data}", file=sys.stderr)
            sys.exit(1)
except Exception as e:
    print(f"WebSocket test failed: {e}", file=sys.stderr)
    sys.exit(1)
EOF
if [ $? -eq 0 ]; then
    success "WebSocket endpoint is working correctly"
else
    fail "WebSocket endpoint test failed"
fi

# 4. Confirm API health using test client
python3 - <<EOF
import sys
from fastapi.testclient import TestClient
from app.main import create_app

# Use test app
app = create_app(testing=True)
client = TestClient(app)

# Test health endpoint
response = client.get("/healthz")
if response.status_code == 200 and response.json() == {"status": "healthy"}:
    print("API_HEALTH_OK")
    sys.exit(0)
else:
    print(f"Health check failed: {response.status_code} - {response.json()}", file=sys.stderr)
    sys.exit(1)
EOF
if [ $? -eq 0 ]; then
    success "API health check passed"
else
    fail "API health check failed"
fi

echo -e "\n${GREEN}Stage 6 verification complete!${NC}" 