#!/bin/bash

# test_session_persistence.sh - Test session persistence functionality
# Tests the JWT token persistence and automatic session restoration

echo "🧪 Testing SafeStream Session Persistence"
echo "========================================="

# Check if server is running
if ! curl -s http://localhost:8000/docs > /dev/null; then
    echo "❌ SafeStream server is not running on localhost:8000"
    echo "Please start the server with: uvicorn app.main:app --reload"
    exit 1
fi

echo "✅ SafeStream server is running"

# Test 1: Check if authentication endpoints are accessible
echo ""
echo "🔍 Test 1: Authentication endpoints accessibility"
if curl -s -X POST http://localhost:8000/auth/login -H "Content-Type: application/x-www-form-urlencoded" -d "username=invalid&password=invalid" | grep -q "detail"; then
    echo "✅ Authentication endpoints are working"
else
    echo "❌ Authentication endpoints are not responding correctly"
    exit 1
fi

# Test 2: Test user creation and token validation
echo ""
echo "🔍 Test 2: User creation and token validation"

# Create a test user
TEST_USER="test_session_$(date +%s)"
TEST_PASS="testpass123"

echo "Creating test user: $TEST_USER"
REGISTER_RESPONSE=$(curl -s -X POST http://localhost:8000/auth/register \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$TEST_USER\",\"password\":\"$TEST_PASS\"}")

if echo "$REGISTER_RESPONSE" | grep -q "access_token"; then
    echo "✅ User registration successful"
    TOKEN=$(echo "$REGISTER_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    echo "✅ JWT token received: ${TOKEN:0:20}..."
else
    echo "❌ User registration failed"
    echo "Response: $REGISTER_RESPONSE"
    exit 1
fi

# Test 3: Validate token with /auth/me endpoint
echo ""
echo "🔍 Test 3: Token validation with /auth/me"
ME_RESPONSE=$(curl -s -X GET http://localhost:8000/auth/me \
    -H "Authorization: Bearer $TOKEN")

if echo "$ME_RESPONSE" | grep -q "$TEST_USER"; then
    echo "✅ Token validation successful"
    echo "✅ User info retrieved: $(echo "$ME_RESPONSE" | grep -o '"username":"[^"]*"')"
else
    echo "❌ Token validation failed"
    echo "Response: $ME_RESPONSE"
fi

# Test 4: Test invalid token handling
echo ""
echo "🔍 Test 4: Invalid token handling"
INVALID_RESPONSE=$(curl -s -w "%{http_code}" -X GET http://localhost:8000/auth/me \
    -H "Authorization: Bearer invalid_token_here")

if echo "$INVALID_RESPONSE" | grep -q "401"; then
    echo "✅ Invalid token correctly rejected with 401"
else
    echo "❌ Invalid token handling failed"
    echo "Response: $INVALID_RESPONSE"
fi

# Test 5: Test WebSocket endpoint accessibility
echo ""
echo "🔍 Test 5: WebSocket endpoint connectivity"
echo "Note: This tests WebSocket endpoint availability, but browser testing is needed for full session persistence verification"

# Try to connect to WebSocket (will fail but should not return 404)
WS_TEST=$(curl -s -w "%{http_code}" -H "Connection: Upgrade" -H "Upgrade: websocket" \
    "http://localhost:8000/ws/$TEST_USER?token=$TOKEN" 2>/dev/null | tail -n1)

if [ "$WS_TEST" != "404" ]; then
    echo "✅ WebSocket endpoint is accessible (status: $WS_TEST)"
else
    echo "❌ WebSocket endpoint returned 404"
fi

echo ""
echo "🎯 Automated tests completed!"
echo ""
echo "📋 Manual Testing Required:"
echo "1. Open browser to http://localhost:8000/chat"
echo "2. Login with: $TEST_USER / $TEST_PASS"
echo "3. Refresh the page - you should stay logged in"
echo "4. Check browser console for session restoration messages"
echo ""
echo "For detailed testing instructions, see:"
echo "   SafeStream/DevelopmentVerification/SessionPersistenceTest.md" 