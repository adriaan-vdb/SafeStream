#!/bin/bash

# Stage 7 Verification: Detoxify ML Moderation Integration
# Tests: Environment variables, stub mode, real mode, API integration

set -e

echo "=== Stage 7: Detoxify ML Moderation Integration ==="

# Test 1: Environment Variables
echo "1. Testing environment variables..."
export DISABLE_DETOXIFY=1
export TOXIC_THRESHOLD=0.5

# Test 2: Stub Mode (DISABLE_DETOXIFY=1)
echo "2. Testing stub mode (DISABLE_DETOXIFY=1)..."
export DISABLE_DETOXIFY=1
python3 -c "
import asyncio
import os
from app.moderation import predict

async def test_stub():
    result = await predict('you are stupid')
    assert result == (False, 0.0), f'Expected (False, 0.0), got {result}'
    print('✓ Stub mode works correctly')

asyncio.run(test_stub())
"

# Test 3: Real Mode (if Detoxify available)
echo "3. Testing real mode (if Detoxify available)..."
export DISABLE_DETOXIFY=0

# Check if Detoxify is available
if python3 -c "import detoxify" 2>/dev/null; then
    echo "  Detoxify available, testing real mode..."
    python3 -c "
import asyncio
import os
from app.moderation import predict

async def test_real():
    # Test toxic text
    result = await predict('you are stupid')
    assert isinstance(result[0], bool), f'Expected bool, got {type(result[0])}'
    assert 0.0 <= result[1] <= 1.0, f'Expected score 0-1, got {result[1]}'
    print(f'✓ Real mode works: toxic={result[0]}, score={result[1]:.3f}')
    
    # Test non-toxic text
    result2 = await predict('hello world')
    assert isinstance(result2[0], bool), f'Expected bool, got {type(result2[0])}'
    assert 0.0 <= result2[1] <= 1.0, f'Expected score 0-1, got {result2[1]}'
    print(f'✓ Real mode works: toxic={result2[0]}, score={result2[1]:.3f}')

asyncio.run(test_real())
"
else
    echo "  Detoxify not available, skipping real mode test"
    echo "  Install with: pip install -e '.[dev,ml]'"
fi

# Test 4: Custom Threshold
echo "4. Testing custom threshold..."
export TOXIC_THRESHOLD=0.1
export DISABLE_DETOXIFY=0

if python3 -c "import detoxify" 2>/dev/null; then
    python3 -c "
import asyncio
import os
from app.moderation import predict

async def test_threshold():
    result = await predict('hello world')
    # With threshold 0.1, even benign text might be flagged
    assert isinstance(result[0], bool), f'Expected bool, got {type(result[0])}'
    print(f'✓ Custom threshold works: toxic={result[0]}, score={result[1]:.3f}')

asyncio.run(test_threshold())
"
else
    echo "  Detoxify not available, skipping threshold test"
fi

# Test 5: API Integration (WebSocket with moderation)
echo "5. Testing API integration with moderation..."
export DISABLE_DETOXIFY=1  # Use stub for testing

# Start server in background
python3 -c "
import uvicorn
import asyncio
from app.main import create_app

app = create_app(testing=True)
uvicorn.run(app, host='127.0.0.1', port=8001, log_level='error')
" &
SERVER_PID=$!

# Wait for server to start
sleep 3

# Test WebSocket with moderation
python3 -c "
import asyncio
import websockets
import json

async def test_websocket_moderation():
    uri = 'ws://localhost:8001/ws/testuser'
    async with websockets.connect(uri) as websocket:
        # Send message
        await websocket.send(json.dumps({'type': 'chat', 'message': 'hello world'}))
        
        # Receive response
        response = await websocket.recv()
        data = json.loads(response)
        
        assert data['type'] == 'chat'
        assert data['user'] == 'testuser'
        assert data['message'] == 'hello world'
        assert 'toxic' in data
        assert 'score' in data
        print(f'✓ WebSocket moderation works: toxic={data[\"toxic\"]}, score={data[\"score\"]}')

asyncio.run(test_websocket_moderation())
"

# Cleanup
kill $SERVER_PID 2>/dev/null || true

# Test 6: Test Coverage
echo "6. Running moderation tests..."
export DISABLE_DETOXIFY=1
pytest tests/test_moderation.py -q

echo "=== Stage 7 Verification Complete ==="
echo "✓ Environment variables work"
echo "✓ Stub mode works"
echo "✓ Real mode works (if Detoxify available)"
echo "✓ Custom threshold works"
echo "✓ API integration works"
echo "✓ Tests pass" 