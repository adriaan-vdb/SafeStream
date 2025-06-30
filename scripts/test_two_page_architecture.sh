#!/bin/bash

# test_two_page_architecture.sh - Test the new two-page architecture
# Verifies login page, app page, and proper redirects

echo "🧪 Testing SafeStream Two-Page Architecture"
echo "==========================================="

# Check if server is running
if ! curl -s http://localhost:8000/docs > /dev/null; then
    echo "❌ SafeStream server is not running on localhost:8000"
    echo "Please start the server with: uvicorn app.main:app --reload"
    exit 1
fi

echo "✅ SafeStream server is running"

# Test 1: Root endpoint redirect
echo ""
echo "🔍 Test 1: Root endpoint redirects to login"
ROOT_RESPONSE=$(curl -s http://localhost:8000/)
if echo "$ROOT_RESPONSE" | grep -q "window.location.href = '/login'"; then
    echo "✅ Root endpoint correctly redirects to login page"
else
    echo "❌ Root endpoint redirect failed"
    echo "Response: $ROOT_RESPONSE"
fi

# Test 2: Login page accessibility
echo ""
echo "🔍 Test 2: Login page accessibility"
LOGIN_RESPONSE=$(curl -s http://localhost:8000/login)
if echo "$LOGIN_RESPONSE" | grep -q "SafeStream - Login" && echo "$LOGIN_RESPONSE" | grep -q "login.js"; then
    echo "✅ Login page loads correctly with proper scripts"
else
    echo "❌ Login page failed to load properly"
fi

# Test 3: App page accessibility
echo ""
echo "🔍 Test 3: App page accessibility"
APP_RESPONSE=$(curl -s http://localhost:8000/app)
if echo "$APP_RESPONSE" | grep -q "SafeStream - Live Chat" && echo "$APP_RESPONSE" | grep -q "app.js"; then
    echo "✅ App page loads correctly with proper scripts"
else
    echo "❌ App page failed to load properly"
fi

# Test 4: Legacy chat endpoint redirect
echo ""
echo "🔍 Test 4: Legacy chat endpoint redirects to login"
CHAT_RESPONSE=$(curl -s http://localhost:8000/chat)
if echo "$CHAT_RESPONSE" | grep -q "window.location.href = '/login'"; then
    echo "✅ Legacy chat endpoint correctly redirects to login"
else
    echo "❌ Legacy chat endpoint redirect failed"
fi

# Test 5: Static files availability
echo ""
echo "🔍 Test 5: Required static files accessibility"

# Check login.js
if curl -s http://localhost:8000/static/js/login.js | grep -q "login.js - SafeStream Login Page"; then
    echo "✅ login.js file accessible"
else
    echo "❌ login.js file not accessible"
fi

# Check app.js
if curl -s http://localhost:8000/static/js/app.js | grep -q "app.js - SafeStream Main Application"; then
    echo "✅ app.js file accessible"
else
    echo "❌ app.js file not accessible"
fi

# Test 6: Authentication endpoints still working
echo ""
echo "🔍 Test 6: Authentication endpoints functionality"

# Test authentication endpoint
AUTH_RESPONSE=$(curl -s -w "%{http_code}" -X POST http://localhost:8000/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=invalid&password=invalid" 2>/dev/null)

# Extract just the HTTP status code (last 3 characters)
AUTH_CODE=$(echo "$AUTH_RESPONSE" | tail -c 4)

if [ "$AUTH_CODE" = "401" ]; then
    echo "✅ Authentication endpoints working (correctly rejected invalid login)"
else
    echo "❌ Authentication endpoints may have issues (status: $AUTH_CODE)"
fi

# Test 7: Create a test user and verify full flow
echo ""
echo "🔍 Test 7: Complete authentication flow test"

# Create a test user
TEST_USER="test_2page_$(date +%s)"
TEST_PASS="testpass123"

REGISTER_RESPONSE=$(curl -s -X POST http://localhost:8000/auth/register \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$TEST_USER\",\"password\":\"$TEST_PASS\"}")

if echo "$REGISTER_RESPONSE" | grep -q "access_token"; then
    echo "✅ User registration successful"
    
    # Extract token
    TOKEN=$(echo "$REGISTER_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    
    # Test token validation
    ME_RESPONSE=$(curl -s -X GET http://localhost:8000/auth/me \
        -H "Authorization: Bearer $TOKEN")
    
    if echo "$ME_RESPONSE" | grep -q "$TEST_USER"; then
        echo "✅ Token validation successful"
        echo "✅ Full authentication flow working"
    else
        echo "❌ Token validation failed"
    fi
else
    echo "❌ User registration failed"
    echo "Response: $REGISTER_RESPONSE"
fi

echo ""
echo "🎯 Automated tests completed!"
echo ""
echo "📋 Manual Browser Testing:"
echo "1. Open http://localhost:8000 - should redirect to login page"
echo "2. Login with demo_user / demo_user"
echo "3. Should redirect to /app with chat interface"
echo "4. REFRESH THE PAGE - should STAY logged in!"
echo "5. Try logging out and back in"
echo ""
echo "🏆 Expected Results:"
echo "- No more session loss on page refresh"
echo "- Smooth login/logout flow"
echo "- Proper redirects between pages"
echo "- Modern UI on both login and app pages"
echo ""
echo "For detailed testing guide, see:"
echo "   SafeStream/DevelopmentVerification/TwoPageArchitectureTest.md" 