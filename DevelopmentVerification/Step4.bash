#!/bin/bash
# SafeStream — Step 4 Verification Script
# Purpose: Run key tests to confirm Pydantic schemas, moderation stub, and unit tests are functional.
# Usage: Run this from the SafeStream project root: ./DevelopmentVerification/Step4.bash

### Before running the script:

# Activate your virtual environment if not already active
# python3 -m venv .venv
# source .venv/bin/activate

# Install all required dependencies
# pip install -e ".[dev]"

# To run entire script:
# chmod +x DevelopmentVerification/Step4.bash
# ./DevelopmentVerification/Step4.bash

set -e  # Exit immediately if a command fails

################################################################################
# 0. PREPARATION
################################################################################

# [Optional] Activate your virtual environment if not already active
# source .venv/bin/activate

# Ensure all Python dependencies are installed, including dev tools
# This assumes you've added pytest, pydantic, and other dependencies
# Run this once before executing the script:
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
# 2. SCHEMA UNIT TESTS
################################################################################

echo "▶ Running Pydantic schema unit tests..."

# Run schema-specific tests with verbose output
echo "  - Testing ChatMessageIn schema..."
python3 -m pytest tests/test_schemas.py::TestChatMessageIn -v

echo "  - Testing ChatMessageOut schema..."
python3 -m pytest tests/test_schemas.py::TestChatMessageOut -v

echo "  - Testing GiftEventOut schema..."
python3 -m pytest tests/test_schemas.py::TestGiftEventOut -v

echo "  - Testing protocol compliance..."
python3 -m pytest tests/test_schemas.py::TestSchemaProtocolCompliance -v

################################################################################
# 3. COMPREHENSIVE TEST SUITE
################################################################################

echo "▶ Running complete test suite..."

# Run all tests to ensure nothing is broken
python3 -m pytest -v

# Verify test count (should be 27 tests total for complete test suite)
TEST_COUNT=$(python3 -m pytest --collect-only | grep "tests collected" | awk '{print $1}')
echo "  - Total tests collected: $TEST_COUNT"

if [ "$TEST_COUNT" -eq 32 ]; then
    echo "  ✅ Expected test count (32) matches actual count"
else
    echo "  ❌ Unexpected test count: expected 32, got $TEST_COUNT"
    exit 1
fi

################################################################################
# 4. SCHEMA IMPORT AND USAGE TESTS
################################################################################

echo "▶ Testing schema imports and basic usage..."

# Test that schemas can be imported and used
python3 -c "
from app.schemas import ChatMessageIn, ChatMessageOut, GiftEventOut
from datetime import datetime

# Test ChatMessageIn
msg_in = ChatMessageIn(message='Hello, world!')
assert msg_in.type == 'chat'
assert msg_in.message == 'Hello, world!'
print('✅ ChatMessageIn import and usage: OK')

# Test ChatMessageOut
msg_out = ChatMessageOut(
    user='testuser',
    message='Hello, world!',
    toxic=False,
    score=0.02,
    ts=datetime.now()
)
assert msg_out.type == 'chat'
assert msg_out.user == 'testuser'
assert msg_out.toxic is False
print('✅ ChatMessageOut import and usage: OK')

# Test GiftEventOut
gift = GiftEventOut(from_user='admin', gift_id=999, amount=1)
assert gift.type == 'gift'
assert gift.from_user == 'admin'
assert gift.gift_id == 999
print('✅ GiftEventOut import and usage: OK')

print('✅ All schema imports and basic usage tests passed')
"

################################################################################
# 5. MODERATION STUB TESTS
################################################################################

echo "▶ Testing moderation stub functionality..."

# Test that moderation module can be imported and used
python3 -c "
import asyncio
from app.moderation import predict

async def test_moderation():
    # Test stub implementation
    toxic, score = await predict('Hello, world!')
    assert toxic is False
    assert score == 0.0
    
    # Test with potentially toxic content (should still return stub values)
    toxic, score = await predict('This is a test message')
    assert toxic is False
    assert score == 0.0
    
    print('✅ Moderation stub tests passed')

# Run the async test
asyncio.run(test_moderation())
"

################################################################################
# 6. PROTOCOL COMPLIANCE VERIFICATION
################################################################################

echo "▶ Verifying protocol compliance with README specifications..."

# Test that schemas produce exactly the expected JSON formats
python3 -c "
import json
from datetime import datetime
from app.schemas import ChatMessageIn, ChatMessageOut, GiftEventOut

# Test ChatMessageIn protocol: {'type':'chat','message':'hello'}
msg_in = ChatMessageIn(message='hello')
json_data = msg_in.model_dump()
expected = {'type': 'chat', 'message': 'hello'}
assert json_data == expected
print('✅ ChatMessageIn protocol compliance: OK')

# Test ChatMessageOut protocol: {'type':'chat','user':'alice','message':'hello','toxic':false,'score':0.02,'ts':'2025-06-26T12:34:56Z'}
timestamp = datetime(2025, 6, 26, 12, 34, 56)
msg_out = ChatMessageOut(
    user='alice',
    message='hello',
    toxic=False,
    score=0.02,
    ts=timestamp
)
json_data = msg_out.model_dump()
assert json_data['type'] == 'chat'
assert json_data['user'] == 'alice'
assert json_data['message'] == 'hello'
assert json_data['toxic'] is False
assert json_data['score'] == 0.02
assert 'ts' in json_data
print('✅ ChatMessageOut protocol compliance: OK')

# Test GiftEventOut protocol: {'from':'admin','gift_id':999,'amount':1}
gift = GiftEventOut(from_user='admin', gift_id=999, amount=1)
json_data = gift.model_dump(by_alias=True)
expected = {'type': 'gift', 'from': 'admin', 'gift_id': 999, 'amount': 1}
assert json_data == expected
print('✅ GiftEventOut protocol compliance: OK')

print('✅ All protocol compliance tests passed')
"

################################################################################
# 7. VALIDATION ERROR TESTING
################################################################################

echo "▶ Testing schema validation error handling..."

# Test that invalid data produces appropriate validation errors
python3 -c "
from pydantic import ValidationError
from app.schemas import ChatMessageIn, ChatMessageOut, GiftEventOut

# Test ChatMessageIn validation errors
try:
    ChatMessageIn()  # Missing required field
    assert False, 'Should have raised ValidationError'
except ValidationError:
    print('✅ ChatMessageIn missing field validation: OK')

try:
    ChatMessageIn(type='invalid', message='test')  # Invalid type
    assert False, 'Should have raised ValidationError'
except ValidationError:
    print('✅ ChatMessageIn invalid type validation: OK')

# Test GiftEventOut validation errors
try:
    GiftEventOut(from_user='admin')  # Missing required fields
    assert False, 'Should have raised ValidationError'
except ValidationError:
    print('✅ GiftEventOut missing fields validation: OK')

print('✅ All validation error tests passed')
"

################################################################################
# 8. SUCCESS CONFIRMATION
################################################################################

echo "✅ Step 4 verification complete: All checks passed."
echo ""
echo "Summary of verified components:"
echo "  - Pydantic schemas (ChatMessageIn, ChatMessageOut, GiftEventOut)"
echo "  - Moderation stub with async interface"
echo "  - Comprehensive unit tests (27 total: 13 schema + 4 smoke + 10 WebSocket/gift tests)"
echo "  - Protocol compliance with README Section 6"
echo "  - Code quality (black, ruff, pre-commit)"
echo "  - Validation error handling"
echo ""
echo "Ready for Stage 5: Detoxify integration and WebSocket implementation" 