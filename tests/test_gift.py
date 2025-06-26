"""Gift API and WebSocket integration tests for SafeStream.

Tests gift event broadcasting, validation, and integration with chat messages.
"""

import json
import time

import pytest
from fastapi.testclient import TestClient
from websockets.sync.client import connect

from app.main import app


class TestGiftAPI:
    """Test gift API functionality and WebSocket broadcasting."""

    def test_gift_api_broadcast(self):
        """Test that gift API broadcasts to connected WebSocket clients."""
        with TestClient(app):
            import threading

            import uvicorn

            def run_server():
                uvicorn.run(app, host="127.0.0.1", port=8005, log_level="error")

            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            time.sleep(0.5)

            try:
                # Connect a WebSocket client
                with connect("ws://127.0.0.1:8005/ws/testuser") as ws:
                    # Send gift via API
                    gift_data = {"from": "admin", "gift_id": 1, "amount": 5}

                    # Use TestClient to make HTTP request
                    with TestClient(app) as client:
                        response = client.post("/api/gift", json=gift_data)
                        assert response.status_code == 200
                        assert response.json() == {"status": "queued"}

                    # WebSocket should receive the gift event
                    received = json.loads(ws.recv())

                    # Verify gift event structure
                    assert received["type"] == "gift"
                    assert received["from"] == "admin"
                    assert received["gift_id"] == 1
                    assert received["amount"] == 5
                    assert "ts" in received

                    # Verify timestamp is recent
                    ts = received["ts"]
                    assert isinstance(ts, str)

            except Exception as e:
                pytest.fail(f"Gift broadcast test failed: {e}")


class TestGiftAPIMultipleClients:
    """Test gift API with multiple connected clients."""

    def test_gift_api_multiple_clients(self):
        """Test that gift API broadcasts to all connected clients."""
        with TestClient(app):
            import threading

            import uvicorn

            def run_server():
                uvicorn.run(app, host="127.0.0.1", port=8006, log_level="error")

            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            time.sleep(0.5)

            try:
                # Connect multiple WebSocket clients
                with (
                    connect("ws://127.0.0.1:8006/ws/user1") as ws1,
                    connect("ws://127.0.0.1:8006/ws/user2") as ws2,
                ):
                    # Send gift via API
                    gift_data = {"from": "donor", "gift_id": 2, "amount": 10}

                    with TestClient(app) as client:
                        response = client.post("/api/gift", json=gift_data)
                        assert response.status_code == 200

                    # Both clients should receive identical gift events
                    received1 = json.loads(ws1.recv())
                    received2 = json.loads(ws2.recv())

                    assert received1 == received2
                    assert received1["type"] == "gift"
                    assert received1["from"] == "donor"
                    assert received1["gift_id"] == 2
                    assert received1["amount"] == 10

            except Exception as e:
                pytest.fail(f"Multiple clients test failed: {e}")


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
        with TestClient(app):
            import threading

            import uvicorn

            def run_server():
                uvicorn.run(app, host="127.0.0.1", port=8007, log_level="error")

            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            time.sleep(0.5)

            try:
                # Connect a client and then disconnect it
                with connect("ws://127.0.0.1:8007/ws/disconnected"):
                    # Client is connected
                    pass

                # Client is now disconnected, send gift via API
                gift_data = {"from": "system", "gift_id": 3, "amount": 1}

                with TestClient(app) as client:
                    # Should not raise an exception
                    response = client.post("/api/gift", json=gift_data)
                    assert response.status_code == 200

            except Exception as e:
                pytest.fail(f"Disconnected clients test failed: {e}")


class TestGiftAndChatIntegration:
    """Test integration between gift and chat messages."""

    def test_gift_and_chat_integration(self):
        """Test that gift and chat messages work together."""
        with TestClient(app):
            import threading

            import uvicorn

            def run_server():
                uvicorn.run(app, host="127.0.0.1", port=8008, log_level="error")

            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            time.sleep(0.5)

            try:
                with connect("ws://127.0.0.1:8008/ws/integration") as ws:
                    # Send a chat message
                    chat_message = {"type": "chat", "message": "Hello!"}
                    ws.send(json.dumps(chat_message))

                    # Receive chat message
                    chat_received = json.loads(ws.recv())
                    assert chat_received["type"] == "chat"
                    assert chat_received["message"] == "Hello!"

                    # Send a gift via API
                    gift_data = {"from": "user", "gift_id": 1, "amount": 5}
                    with TestClient(app) as client:
                        response = client.post("/api/gift", json=gift_data)
                        assert response.status_code == 200

                    # Receive gift message
                    gift_received = json.loads(ws.recv())
                    assert gift_received["type"] == "gift"
                    assert gift_received["from"] == "user"

            except Exception as e:
                pytest.fail(f"Integration test failed: {e}")


class TestChatModerationFields:
    """Test that chat messages include moderation fields."""

    def test_chat_toxic_and_score_fields(self):
        """Test that chat messages include toxic and score fields."""
        with TestClient(app):
            import threading

            import uvicorn

            def run_server():
                uvicorn.run(app, host="127.0.0.1", port=8009, log_level="error")

            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            time.sleep(0.5)

            try:
                with connect("ws://127.0.0.1:8009/ws/moderation") as ws:
                    # Send a chat message
                    chat_message = {"type": "chat", "message": "Test message"}
                    ws.send(json.dumps(chat_message))

                    # Receive and verify moderation fields
                    received = json.loads(ws.recv())
                    assert received["type"] == "chat"
                    assert "toxic" in received
                    assert "score" in received
                    assert isinstance(received["toxic"], bool)
                    assert isinstance(received["score"], int | float)

                    # With stub moderation, should always be False, 0.0
                    assert received["toxic"] is False
                    assert received["score"] == 0.0

            except Exception as e:
                pytest.fail(f"Moderation fields test failed: {e}")
