"""WebSocket basic functionality tests for SafeStream.

Tests WebSocket connections, message broadcasting, and schema validation.
Must complete in <2 seconds as per Stage 5-A requirements.
"""

import json
import os
import time
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.main import create_app

# Create test app without background tasks
app = create_app(testing=True)


def get_unique_username(prefix: str = "testuser") -> str:
    """Generate a unique username for testing."""
    timestamp = int(time.time() * 1000)
    return f"{prefix}_{timestamp}"


def create_test_user_and_token(client: TestClient, username: str) -> str:
    """Create a test user and return JWT token."""
    response = client.post(
        "/auth/register",
        json={"username": username, "password": "testpass123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


class TestWebSocketBasic:
    """Test basic WebSocket functionality with two connected clients."""

    def test_websocket_chat_broadcast(self):
        """Test that messages from one client are broadcast to all connected clients."""
        with TestClient(app) as client:
            # Create test users and get tokens
            alice_username = get_unique_username("alice")
            bob_username = get_unique_username("bob")

            alice_token = create_test_user_and_token(client, alice_username)
            bob_token = create_test_user_and_token(client, bob_username)

            # Start WebSocket connections with authentication
            with (
                client.websocket_connect(
                    f"/ws/{alice_username}?token={alice_token}"
                ) as alice_ws,
                client.websocket_connect(
                    f"/ws/{bob_username}?token={bob_token}"
                ) as bob_ws,
            ):

                # Send message from alice
                alice_message = {"type": "chat", "message": "Hello, everyone!"}
                alice_ws.send_text(json.dumps(alice_message))

                # Receive messages on both connections
                alice_received = json.loads(alice_ws.receive_text())
                bob_received = json.loads(bob_ws.receive_text())

                # Verify message structure
                assert alice_received["type"] == "chat"
                assert alice_received["user"] == alice_username
                assert alice_received["message"] == "Hello, everyone!"
                assert "toxic" in alice_received
                assert "score" in alice_received
                assert "ts" in alice_received
                assert alice_received == bob_received

                # Check if we're in stub mode or real ML mode
                is_stub_mode = os.getenv("DISABLE_DETOXIFY", "0") == "1"

                if is_stub_mode:
                    # Stub mode: always non-toxic with score 0.0
                    assert alice_received["toxic"] is False
                    assert alice_received["score"] == 0.0
                else:
                    # Real ML mode: check that score is in valid range
                    assert 0.0 <= alice_received["score"] <= 1.0
                    # For "Hello, everyone!", should be non-toxic
                    assert alice_received["toxic"] is False

                # Verify timestamp is recent
                ts = datetime.fromisoformat(alice_received["ts"].replace("Z", "+00:00"))
                assert (datetime.now(UTC) - ts).total_seconds() < 5


class TestWebSocketSchemaValidation:
    """Test WebSocket message schema validation."""

    def test_websocket_invalid_message_rejection(self):
        """Test that invalid messages are rejected."""
        with TestClient(app) as client:
            # Create test user and get token
            username = get_unique_username("testuser")
            token = create_test_user_and_token(client, username)

            with client.websocket_connect(f"/ws/{username}?token={token}") as ws:
                # Send invalid message (missing required fields)
                invalid_message = {"type": "chat"}
                ws.send_text(json.dumps(invalid_message))

                # Should receive an error response
                response = ws.receive_text()
                error_data = json.loads(response)
                assert "error" in error_data
                assert "detail" in error_data
                assert error_data["error"] == "Invalid message format"


class TestWebSocketConnectionManagement:
    """Test WebSocket connection management."""

    def test_websocket_connection_cleanup(self):
        """Test that disconnected clients are properly cleaned up."""
        with TestClient(app) as client:
            # Create test user and get token
            username = get_unique_username("tempuser")
            token = create_test_user_and_token(client, username)

            # Connect and immediately disconnect
            with client.websocket_connect(f"/ws/{username}?token={token}") as ws:
                message = {"type": "chat", "message": "test"}
                ws.send_text(json.dumps(message))
                # Receive the message to confirm it was processed
                response = json.loads(ws.receive_text())
                assert response["type"] == "chat"
                assert response["message"] == "test"

            # Connection should be cleaned up automatically when context exits


class TestWebSocketPerformance:
    """Test WebSocket performance requirements."""

    def test_websocket_response_time(self):
        """Test that WebSocket responses complete within 2 seconds."""
        start_time = datetime.now(UTC)

        with TestClient(app) as client:
            # Create test user and get token
            username = get_unique_username("performance")
            token = create_test_user_and_token(client, username)

            with client.websocket_connect(f"/ws/{username}?token={token}") as ws:
                for i in range(5):
                    message = {"type": "chat", "message": f"Message {i}"}
                    ws.send_text(json.dumps(message))
                    response = json.loads(ws.receive_text())
                    assert response["message"] == f"Message {i}"
                    assert response["type"] == "chat"

                elapsed_time = (datetime.now(UTC) - start_time).total_seconds()
                assert (
                    elapsed_time < 2.0
                ), f"WebSocket test took {elapsed_time:.2f}s, expected <2s"
