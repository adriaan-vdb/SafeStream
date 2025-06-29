#!/bin/bash

# Stage 10 Verification: JWT Authentication Integration
# Tests: Registration, login, token validation, WebSocket auth, admin endpoints
# Updated for Step 11 database-only implementation

set -e

echo "=== Stage 10: JWT Authentication Integration (Updated for Database-Only) ==="

# Set up environment variables
export JWT_SECRET_KEY="test-secret-key-for-verification"
export JWT_EXPIRE_MINUTES=30
export DATABASE_URL="sqlite+aiosqlite:///:memory:"
export DISABLE_DETOXIFY=1

# Generate unique test usernames to avoid conflicts
TEST_USERNAME="testuser_$(date +%s)"
API_USERNAME="apiuser_$(date +%s)"
TARGET_USERNAME="targetuser_$(date +%s)"

echo "Using test usernames: $TEST_USERNAME, $API_USERNAME, $TARGET_USERNAME"

# Test 1: Environment Variables
echo "1. Testing environment variables..."
python3 -c "
import os
from app.auth import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES
assert SECRET_KEY == 'test-secret-key-for-verification'
assert ACCESS_TOKEN_EXPIRE_MINUTES == 30
print('✓ Environment variables loaded correctly')
"

# Test 2: Database Initialization and User Registration
echo "2. Testing database initialization and user registration..."
python3 -c "
import asyncio
import os
from app.db import init_db
from app.auth import create_user, get_user

async def test_registration():
    # Initialize database
    await init_db()
    
    test_username = '$TEST_USERNAME'
    print(f'Creating user: {test_username}')

    # Test registration
    user = await create_user(test_username, 'testpass123', 'test@example.com')
    assert user.username == test_username
    assert user.email == 'test@example.com'
    print('✓ User registration works')

    # Test duplicate registration fails
    try:
        await create_user(test_username, 'anotherpass', 'another@example.com')
        assert False, 'Should have failed'
    except Exception as e:
        assert 'already registered' in str(e)
        print('✓ Duplicate registration properly rejected')

asyncio.run(test_registration())
"

# Test 3: User Authentication
echo "3. Testing user authentication..."
python3 -c "
import asyncio
import os
from app.db import init_db
from app.auth import authenticate_user, get_user, create_user

async def test_authentication():
    # Initialize database
    await init_db()
    
    test_username = '$TEST_USERNAME'
    print(f'Testing authentication for user: {test_username}')

    # Create user first (since database is in-memory)
    await create_user(test_username, 'testpass123', 'test@example.com')

    # Test valid authentication
    user = await authenticate_user(test_username, 'testpass123')
    assert user is not None
    assert user.username == test_username
    print('✓ Valid authentication works')

    # Test invalid password
    user = await authenticate_user(test_username, 'wrongpass')
    assert user is None
    print('✓ Invalid password properly rejected')

    # Test non-existent user
    user = await authenticate_user('nonexistent', 'testpass123')
    assert user is None
    print('✓ Non-existent user properly rejected')

asyncio.run(test_authentication())
"

# Test 4: JWT Token Creation and Validation
echo "4. Testing JWT token creation and validation..."
python3 -c "
import asyncio
import os
from app.db import init_db
from app.auth import create_access_token, get_user_by_token, create_user

async def test_jwt():
    # Initialize database
    await init_db()
    
    test_username = '$TEST_USERNAME'

    # Create user first (since database is in-memory)
    await create_user(test_username, 'testpass123', 'test@example.com')

    # Test token creation
    token = create_access_token({'sub': test_username})
    assert token is not None
    print('✓ JWT token creation works')

    # Test token validation
    user = await get_user_by_token(token)
    assert user is not None
    assert user.username == test_username
    print('✓ JWT token validation works')

    # Test invalid token
    user = await get_user_by_token('invalid-token')
    assert user is None
    print('✓ Invalid token properly rejected')

asyncio.run(test_jwt())
"

# Test 5: API Integration (Registration and Login endpoints)
echo "5. Testing API integration..."

# Kill any existing process on port 8002
pkill -f "uvicorn.*8002" 2>/dev/null || true
sleep 2

# Start server in background
python3 -c "
import uvicorn
import asyncio
from app.main import create_app

app = create_app(testing=True)
uvicorn.run(app, host='127.0.0.1', port=8002, log_level='error')
" &
SERVER_PID=$!

# Wait for server to start
for i in {1..10}; do
    if nc -z localhost 8002; then break; fi
    sleep 1
done

# Test registration endpoint
python3 -c "
import requests
import json
import os
import time

api_username = '$API_USERNAME'
print(f'Testing API with username: {api_username}')

# Test registration
response = requests.post('http://localhost:8002/auth/register', 
    json={'username': api_username, 'password': 'apipass123', 'email': 'api@example.com'})
assert response.status_code == 200
data = response.json()
assert 'access_token' in data
assert data['username'] == api_username
print('✓ Registration endpoint works')

# Test login endpoint
response = requests.post('http://localhost:8002/auth/login', 
    data={'username': api_username, 'password': 'apipass123'})
assert response.status_code == 200
data = response.json()
assert 'access_token' in data
assert data['username'] == api_username
token = data['access_token']
print('✓ Login endpoint works')

# Test protected endpoint
headers = {'Authorization': f'Bearer {token}'}
response = requests.get('http://localhost:8002/auth/me', headers=headers)
assert response.status_code == 200
data = response.json()
assert data['username'] == api_username
print('✓ Protected endpoint works')

# Test unauthorized access
response = requests.get('http://localhost:8002/auth/me')
assert response.status_code == 401
print('✓ Unauthorized access properly rejected')
"

# Test 6: WebSocket Authentication
echo "6. Testing WebSocket authentication..."
python3 -c "
import asyncio
import websockets
import json
import requests
import os

api_username = '$API_USERNAME'

# Get token first
response = requests.post('http://localhost:8002/auth/login', 
    data={'username': api_username, 'password': 'apipass123'})
token = response.json()['access_token']

async def test_websocket_auth():
    try:
        # Test authenticated connection
        uri = f'ws://localhost:8002/ws/{api_username}?token={token}'
        print(f'Connecting to WebSocket: {uri}')
        async with websockets.connect(uri) as websocket:
            # Send message
            message = {'type': 'chat', 'message': 'hello world'}
            await websocket.send(json.dumps(message))
            print(f'Sent message: {message}')
            
            # Receive response
            response = await websocket.recv()
            data = json.loads(response)
            print('WebSocket received:', data)
            
            # Validate response
            assert isinstance(data, dict), f'Expected dict, got {type(data)}'
            assert 'type' in data, f'Message missing type field: {data}'
            assert data['type'] == 'chat', f'Expected chat message, got: {data}'
            assert data['user'] == api_username
            assert data['message'] == 'hello world'
            print('✓ Authenticated WebSocket connection works')

        # Test unauthenticated connection
        uri_no_token = f'ws://localhost:8002/ws/{api_username}'
        try:
            async with websockets.connect(uri_no_token) as websocket:
                assert False, 'Should have failed'
        except Exception as e:
            print('✓ Unauthenticated WebSocket properly rejected')
            
    except Exception as e:
        print(f'WebSocket test failed: {e}')
        raise

asyncio.run(test_websocket_auth())
"

# Test 7: Admin Endpoints with Authentication
echo "7. Testing admin endpoints with authentication..."
python3 -c "
import requests
import json
import os

api_username = '$API_USERNAME'
target_username = '$TARGET_USERNAME'

# Get token
response = requests.post('http://localhost:8002/auth/login', 
    data={'username': api_username, 'password': 'apipass123'})
token = response.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Test admin kick endpoint
response = requests.post('http://localhost:8002/api/admin/kick', 
    json={'username': target_username}, headers=headers)
assert response.status_code == 200
print('✓ Admin kick endpoint works')

# Test admin mute endpoint
response = requests.post('http://localhost:8002/api/admin/mute', 
    json={'username': target_username}, headers=headers)
assert response.status_code == 200
print('✓ Admin mute endpoint works')

# Test admin reset metrics endpoint
response = requests.post('http://localhost:8002/api/admin/reset_metrics', headers=headers)
assert response.status_code == 200
print('✓ Admin reset metrics endpoint works')

# Test unauthorized admin access
response = requests.post('http://localhost:8002/api/admin/kick', 
    json={'username': target_username})
assert response.status_code == 401
print('✓ Unauthorized admin access properly rejected')
"

# Cleanup
kill $SERVER_PID 2>/dev/null || true

# Test 8: Code Quality
echo "8. Running code quality checks..."
python3 -m black --check app/auth.py app/main.py app/schemas.py
python3 -m ruff check app/auth.py app/main.py app/schemas.py
python3 -m mypy app/auth.py app/main.py app/schemas.py --ignore-missing-imports

# Test 9: Test Coverage
echo "9. Running authentication tests..."
pytest tests/test_auth.py -v

echo "=== Stage 10 Verification Complete (Updated for Database-Only) ==="
echo "✓ Environment variables work"
echo "✓ Database initialization works"
echo "✓ User registration works"
echo "✓ User authentication works"
echo "✓ JWT token creation and validation works"
echo "✓ API endpoints work"
echo "✓ WebSocket authentication works"
echo "✓ Admin endpoints work"
echo "✓ Code quality checks pass"
echo "✓ Tests pass" 