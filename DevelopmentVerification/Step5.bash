#!/bin/bash
# SafeStream — Step 5 Verification Script
# Purpose: Run key tests to confirm WebSocket chat, gift API, logging, and E2E tests are functional.
# Usage: Run this from the SafeStream project root: ./DevelopmentVerification/Step5.bash

### Before running the script:
# Activate your virtual environment if not already active
# python3 -m venv .venv
# source .venv/bin/activate
# Install all required dependencies
# pip install -e ".[dev]"
# To run entire script:
# chmod +x DevelopmentVerification/Step5.bash
# ./DevelopmentVerification/Step5.bash

set -e  # Exit immediately if a command fails

################################################################################
# 0. PREPARATION
################################################################################

# [Optional] Activate your virtual environment if not already active
# source .venv/bin/activate
# Ensure all Python dependencies are installed, including dev tools
# pip install -e ".[dev]"

################################################################################
# 1. CODE QUALITY CHECKS
################################################################################

echo "▶ Running code quality checks..."

# Check code formatting with black (the only formatter)
echo "  - Checking code formatting..."
black --check .

# Check linting with ruff (linting only, not formatting)
echo "  - Checking code linting..."
ruff check .

# Run pre-commit hooks if available
if command -v pre-commit &> /dev/null; then
    echo "  - Running pre-commit hooks..."
    pre-commit run --all-files
else
    echo "  - Pre-commit not available, skipping..."
fi

################################################################################
# 2. WEBSOCKET CHAT TESTS
################################################################################

echo "▶ Running WebSocket chat E2E tests..."
python3 -m pytest tests/test_ws_basic.py -v

################################################################################
# 3. GIFT API TESTS
################################################################################

echo "▶ Running Gift API E2E tests..."
python3 -m pytest tests/test_gift.py -v

################################################################################
# 4. FULL TEST SUITE
################################################################################

echo "▶ Running complete test suite..."
python3 -m pytest -v

# Verify test count (should be 42 tests total for complete test suite)
TEST_COUNT=$(python3 -m pytest --collect-only | grep "tests collected" | awk '{print $1}')
echo "  - Total tests collected: $TEST_COUNT"

if [ "$TEST_COUNT" -eq 42 ]; then
    echo "  ✅ Expected test count (42) matches actual count"
else
    echo "  ❌ Unexpected test count: expected 42, got $TEST_COUNT"
    exit 1
fi

################################################################################
# 5. API & PROTOCOL EXAMPLES
################################################################################

echo "▶ Testing API and protocol compliance..."

# Test WebSocket chat via Python
python3 -c "
from app.schemas import ChatMessageIn, ChatMessageOut
from datetime import datetime, UTC
msg = ChatMessageIn(message='Hello!')
out = ChatMessageOut(user='alice', message='Hello!', toxic=False, score=0.0, ts=datetime.now(UTC))
assert msg.type == 'chat'
assert out.type == 'chat'
assert hasattr(out, 'toxic') and hasattr(out, 'score')
print('✅ ChatMessageIn/Out protocol: OK')
"

# Test GiftEventOut protocol
python3 -c "
from app.schemas import GiftEventOut
gift = GiftEventOut(from_user='admin', gift_id=1, amount=5)
json_data = gift.model_dump(by_alias=True)
assert json_data['type'] == 'gift'
assert json_data['from'] == 'admin'
assert json_data['gift_id'] == 1
assert json_data['amount'] == 5
print('✅ GiftEventOut protocol: OK')
"

################################################################################
# 6. LOGGING VERIFICATION
################################################################################

echo "▶ Verifying chat and gift event logging..."

LOGFILE="logs/chat_$(date -u +%Y-%m-%d).jsonl"
if [ -f "$LOGFILE" ]; then
    echo "  - Log file exists: $LOGFILE"
    tail -n 5 "$LOGFILE"
else
    echo "  ❌ Log file not found: $LOGFILE"
    exit 1
fi

################################################################################
# 7. SUCCESS CONFIRMATION
################################################################################

echo "✅ Step 5 verification complete: All checks passed."
echo ""
echo "Summary of verified components:"
echo "  - WebSocket chat broadcast and moderation"
echo "  - Gift API endpoint and broadcast"
echo "  - Unified JSONL logging for chat and gifts"
echo "  - E2E tests for chat, gift, and integration"
echo "  - Protocol compliance with README Section 6"
echo "  - Code quality (black, ruff, pre-commit)"
echo "  - Validation and error handling"
echo ""
echo "Ready for Stage 6: Random gift generator and further enhancements" 