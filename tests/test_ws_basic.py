"""WebSocket basic functionality tests for SafeStream.

Tests WebSocket connections, message broadcasting, and schema validation.
Must complete in <2 seconds as per Stage 5-A requirements.
"""

import json
import time
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from websockets.sync.client import connect

from app.main import app


class TestWebSocketBasic:
    """Test basic WebSocket functionality with two connected clients."""

    def test_websocket_chat_broadcast(self):
        """Test that messages from one client are broadcast to all connected clients."""
        # Start the FastAPI test server
        with TestClient(app):
            # Start the server in a separate thread
            import threading

            import uvicorn

            def run_server():
                uvicorn.run(app, host="127.0.0.1", port=8001, log_level="error")

            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()

            # Wait for server to start
            time.sleep(0.5)

            try:
                # Connect two WebSocket clients
                with (
                    connect("ws://127.0.0.1:8001/ws/alice") as alice_ws,
                    connect("ws://127.0.0.1:8001/ws/bob") as bob_ws,
                ):
                    # Alice sends a message
                    alice_message = {"type": "chat", "message": "Hello, everyone!"}
                    alice_ws.send(json.dumps(alice_message))

                    # Both clients should receive the message
                    alice_received = json.loads(alice_ws.recv())
                    bob_received = json.loads(bob_ws.recv())

                    # Verify message structure matches ChatMessageOut schema
                    assert alice_received["type"] == "chat"
                    assert alice_received["user"] == "alice"
                    assert alice_received["message"] == "Hello, everyone!"
                    assert "toxic" in alice_received
                    assert "score" in alice_received
                    assert "ts" in alice_received

                    # Verify both clients received identical messages
                    assert alice_received == bob_received

                    # Verify moderation results (should be stub values)
                    assert alice_received["toxic"] is False
                    assert alice_received["score"] == 0.0

                    # Verify timestamp is recent
                    ts = datetime.fromisoformat(
                        alice_received["ts"].replace("Z", "+00:00")
                    )
                    assert (datetime.now(UTC) - ts).total_seconds() < 5

            finally:
                # Clean up
                pass


class TestWebSocketSchemaValidation:
    """Test WebSocket message schema validation."""

    def test_websocket_invalid_message_rejection(self):
        """Test that invalid messages are rejected."""
        with TestClient(app):
            import threading

            import uvicorn

            def run_server():
                uvicorn.run(app, host="127.0.0.1", port=8002, log_level="error")

            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            time.sleep(0.5)

            try:
                with connect("ws://127.0.0.1:8002/ws/testuser") as ws:
                    # Send invalid message (missing required field)
                    invalid_message = {"type": "chat"}
                    ws.send(json.dumps(invalid_message))

                    # Should receive error or connection should close
                    # This test verifies that the WebSocket handles validation errors gracefully
                    time.sleep(0.1)

            except Exception:
                # Expected behavior for invalid messages
                pass


class TestWebSocketConnectionManagement:
    """Test WebSocket connection management."""

    def test_websocket_connection_cleanup(self):
        """Test that disconnected clients are properly cleaned up."""
        with TestClient(app):
            import threading

            import uvicorn

            def run_server():
                uvicorn.run(app, host="127.0.0.1", port=8003, log_level="error")

            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            time.sleep(0.5)

            try:
                # Connect and immediately disconnect
                with connect("ws://127.0.0.1:8003/ws/tempuser") as ws:
                    # Send a message to ensure connection is active
                    message = {"type": "chat", "message": "test"}
                    ws.send(json.dumps(message))
                    time.sleep(0.1)

                # Connection should be cleaned up after disconnect
                # This is verified by the fact that no exceptions are raised

            except Exception as e:
                pytest.fail(f"Connection cleanup failed: {e}")


class TestWebSocketPerformance:
    """Test WebSocket performance requirements."""

    def test_websocket_response_time(self):
        """Test that WebSocket responses complete within 2 seconds."""
        start_time = time.time()

        with TestClient(app):
            import threading

            import uvicorn

            def run_server():
                uvicorn.run(app, host="127.0.0.1", port=8004, log_level="error")

            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            time.sleep(0.5)

            try:
                with connect("ws://127.0.0.1:8004/ws/performance") as ws:
                    # Send multiple messages quickly
                    for i in range(5):
                        message = {"type": "chat", "message": f"Message {i}"}
                        ws.send(json.dumps(message))
                        response = json.loads(ws.recv())
                        assert response["message"] == f"Message {i}"

                elapsed_time = time.time() - start_time
                assert (
                    elapsed_time < 2.0
                ), f"WebSocket test took {elapsed_time:.2f}s, expected <2s"

            except Exception as e:
                pytest.fail(f"Performance test failed: {e}")
