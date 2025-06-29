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

# === Robust Test/CI Prelude ===
set -e

ruff check --fix .
black .

export DISABLE_DETOXIFY=1
export JWT_SECRET_KEY="test-secret-key-for-verification"
export JWT_EXPIRE_MINUTES=30
export DATABASE_URL="sqlite+aiosqlite:///:memory:"
export TEST_USERNAME="testuser_$(date +%s)"
export API_USERNAME="apiuser_$(date +%s)"
export TARGET_USERNAME="targetuser_$(date +%s)"

pkill -f "uvicorn.*8002" 2>/dev/null || true
sleep 2

cleanup() {
    docker stop safestream-test-container 2>/dev/null || true
    docker rm safestream-test-container 2>/dev/null || true
    pkill -f "uvicorn.*8002" 2>/dev/null || true
}
trap cleanup EXIT

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
from app.auth import create_user, create_access_token
import json

# Use test app (no background tasks)
app = create_app(testing=True)
client = TestClient(app)

# Create a test user and generate a valid JWT token
try:
    # Create test user
    test_username = "step6test"
    test_password = "testpass123"
    
    # Register user
    response = client.post(
        "/auth/register",
        json={"username": test_username, "password": test_password}
    )
    
    if response.status_code != 200:
        print(f"Failed to create test user: {response.status_code} - {response.json()}", file=sys.stderr)
        sys.exit(1)
    
    # Get the JWT token from the response
    token_data = response.json()
    jwt_token = token_data["access_token"]
    
    # Test that WebSocket endpoint exists and can be reached with valid token
    with client.websocket_connect(f"/ws/{test_username}?token={jwt_token}") as ws:
        # Send a test message
        ws.send_text(json.dumps({"type": "chat", "message": "test"}))
        
        # Receive the response
        msg = ws.receive_text()
        data = json.loads(msg)
        
        if data.get("type") == "chat" and data.get("user") == test_username:
            print("WEBSOCKET_OK")
            sys.exit(0)
        else:
            print(f"Unexpected message format: {data}", file=sys.stderr)
            sys.exit(1)
except Exception as e:
    import traceback
    print(f"WebSocket test failed: {e}", file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)
EOF
if [ $? -eq 0 ]; then
    success "WebSocket endpoint is working correctly"
else
    fail "WebSocket endpoint test failed (see error above)"
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