"""Gift API and WebSocket integration tests for SafeStream.

Tests gift event broadcasting, validation, and integration with chat messages.
"""

import json
import os
import time

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


class TestGiftAPI:
    """Test gift API functionality and WebSocket broadcasting."""

    def test_gift_api_broadcast(self):
        """Test that gift API broadcasts to connected WebSocket clients."""
        with TestClient(app) as client:
            # Create test user and get token
            username = get_unique_username("testuser")
            token = create_test_user_and_token(client, username)

            # Connect WebSocket client with authentication
            with client.websocket_connect(f"/ws/{username}?token={token}") as ws:
                # Send gift via API
                gift_data = {"from": "admin", "gift_id": 1, "amount": 5}
                response = client.post("/api/gift", json=gift_data)
                if response.status_code != 200:
                    print(f"Error response: {response.status_code} - {response.text}")
                assert response.status_code == 200
                assert response.json() == {"status": "queued"}

                # Receive gift event on WebSocket
                received = json.loads(ws.receive_text())
                assert received["type"] == "gift"
                assert received["from"] == "admin"
                assert received["gift_id"] == 1
                assert received["amount"] == 5
                assert "ts" in received
                ts = received["ts"]
                assert isinstance(ts, str)


class TestGiftAPIMultipleClients:
    """Test gift API with multiple connected clients."""

    def test_gift_api_multiple_clients(self):
        """Test that gift API broadcasts to all connected clients."""
        with TestClient(app) as client:
            # Create test users and get tokens
            user1_username = get_unique_username("user1")
            user2_username = get_unique_username("user2")

            user1_token = create_test_user_and_token(client, user1_username)
            user2_token = create_test_user_and_token(client, user2_username)

            # Connect multiple WebSocket clients with authentication
            with (
                client.websocket_connect(
                    f"/ws/{user1_username}?token={user1_token}"
                ) as ws1,
                client.websocket_connect(
                    f"/ws/{user2_username}?token={user2_token}"
                ) as ws2,
            ):

                # Send gift via API
                gift_data = {"from": "donor", "gift_id": 2, "amount": 10}
                response = client.post("/api/gift", json=gift_data)
                assert response.status_code == 200

                # Both clients should receive the same gift event
                received1 = json.loads(ws1.receive_text())
                received2 = json.loads(ws2.receive_text())
                assert received1 == received2
                assert received1["type"] == "gift"
                assert received1["from"] == "donor"
                assert received1["gift_id"] == 2
                assert received1["amount"] == 10


class TestGiftAPIValidation:
    """Test gift API validation and error handling."""

    def test_gift_api_validation_errors(self):
        """Test gift API handles validation errors gracefully."""
        with TestClient(app) as client:
            # Test missing required field
            invalid_gift = {"from": "user", "gift_id": 1}
            response = client.post("/api/gift", json=invalid_gift)
            assert response.status_code == 400

            # Test invalid gift_id type
            invalid_gift = {"from": "user", "gift_id": "invalid", "amount": 5}
            response = client.post("/api/gift", json=invalid_gift)
            assert response.status_code == 400

            # Test invalid amount type
            invalid_gift = {"from": "user", "gift_id": 1, "amount": "invalid"}
            response = client.post("/api/gift", json=invalid_gift)
            assert response.status_code == 400


class TestGiftAPIDisconnectedClients:
    """Test gift API behavior with disconnected clients."""

    def test_gift_api_disconnected_clients(self):
        """Test gift API handles disconnected clients gracefully."""
        with TestClient(app) as client:
            # Create test user and get token
            username = get_unique_username("disconnected")
            token = create_test_user_and_token(client, username)

            # Connect and immediately disconnect
            with client.websocket_connect(f"/ws/{username}?token={token}"):
                pass

            # Send gift after client disconnected
            gift_data = {"from": "system", "gift_id": 3, "amount": 1}
            response = client.post("/api/gift", json=gift_data)
            assert response.status_code == 200


class TestGiftAndChatIntegration:
    """Test integration between gift and chat messages."""

    def test_gift_and_chat_integration(self):
        """Test that gift and chat messages work together."""
        with TestClient(app) as client:
            # Create test user and get token
            username = get_unique_username("integration")
            token = create_test_user_and_token(client, username)

            with client.websocket_connect(f"/ws/{username}?token={token}") as ws:
                # Send chat message
                chat_message = {"type": "chat", "message": "Hello!"}
                ws.send_text(json.dumps(chat_message))
                chat_received = json.loads(ws.receive_text())
                assert chat_received["type"] == "chat"
                assert chat_received["message"] == "Hello!"

                # Send gift via API
                gift_data = {"from": "user", "gift_id": 1, "amount": 5}
                response = client.post("/api/gift", json=gift_data)
                assert response.status_code == 200

                # Receive gift event
                gift_received = json.loads(ws.receive_text())
                assert gift_received["type"] == "gift"
                assert gift_received["from"] == "user"


class TestChatModerationFields:
    """Test that chat messages include moderation fields."""

    def test_chat_toxic_and_score_fields(self):
        """Test that chat messages include toxic and score fields."""
        with TestClient(app) as client:
            # Create test user and get token
            username = get_unique_username("moderation")
            token = create_test_user_and_token(client, username)

            with client.websocket_connect(f"/ws/{username}?token={token}") as ws:
                # Send chat message
                chat_message = {"type": "chat", "message": "Test message"}
                ws.send_text(json.dumps(chat_message))

                # Receive response with moderation fields
                received = json.loads(ws.receive_text())
                assert received["type"] == "chat"
                assert "toxic" in received
                assert "score" in received
                assert isinstance(received["toxic"], bool)
                assert isinstance(received["score"], int | float)

                # Check if we're in stub mode or real ML mode
                is_stub_mode = os.getenv("DISABLE_DETOXIFY", "0") == "1"

                if is_stub_mode:
                    # Stub mode: always non-toxic with score 0.0
                    assert received["toxic"] is False
                    assert received["score"] == 0.0
                else:
                    # Real ML mode: check that score is in valid range
                    assert 0.0 <= received["score"] <= 1.0


class TestGiftAPIEdgeCases:
    """Test gift API edge cases and boundary conditions."""

    def test_gift_api_edge_cases(self):
        """Test gift API with edge case values."""
        with TestClient(app) as client:
            # Test minimum valid values (amount must be >= 1)
            gift_data = {"from": "min", "gift_id": 0, "amount": 1}
            response = client.post("/api/gift", json=gift_data)
            assert response.status_code == 200

            # Test maximum reasonable values
            gift_data = {"from": "max", "gift_id": 999999, "amount": 999999}
            response = client.post("/api/gift", json=gift_data)
            assert response.status_code == 200

            # Test empty string username (should be valid)
            gift_data = {"from": "", "gift_id": 1, "amount": 1}
            response = client.post("/api/gift", json=gift_data)
            assert response.status_code == 200

            # Test that amount=0 is rejected (validation error)
            gift_data = {"from": "test", "gift_id": 1, "amount": 0}
            response = client.post("/api/gift", json=gift_data)
            assert response.status_code == 400
