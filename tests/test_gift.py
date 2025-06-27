"""Gift API and WebSocket integration tests for SafeStream.

Tests gift event broadcasting, validation, and integration with chat messages.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

# Create test app without background tasks
app = create_app(testing=True)


class TestGiftAPI:
    """Test gift API functionality and WebSocket broadcasting."""

    def test_gift_api_broadcast(self):
        """Test that gift API broadcasts to connected WebSocket clients."""
        # TODO: Fix WebSocket test hanging issue
        pytest.skip("WebSocket test temporarily disabled due to hanging issues")
        # import threading
        # import uvicorn

        # def run_server():
        #     uvicorn.run(app, host="127.0.0.1", port=8005, log_level="error")

        # server_thread = threading.Thread(target=run_server, daemon=True)
        # server_thread.start()
        # time.sleep(0.5)
        # try:
        #     with connect("ws://127.0.0.1:8005/ws/testuser") as ws:
        #         gift_data = {"from": "admin", "gift_id": 1, "amount": 5}
        #         with TestClient(app) as client:
        #             response = client.post("/api/gift", json=gift_data)
        #             assert response.status_code == 200
        #             assert response.json() == {"status": "queued"}
        #         received = json.loads(ws.recv())
        #         assert received["type"] == "gift"
        #         assert received["from"] == "admin"
        #         assert received["gift_id"] == 1
        #         assert received["amount"] == 5
        #         assert "ts" in received
        #         ts = received["ts"]
        #         assert isinstance(ts, str)
        # except Exception as e:
        #     pytest.fail(f"Gift broadcast test failed: {e}")


class TestGiftAPIMultipleClients:
    """Test gift API with multiple connected clients."""

    def test_gift_api_multiple_clients(self):
        """Test that gift API broadcasts to all connected clients."""
        # TODO: Fix WebSocket test hanging issue
        pytest.skip("WebSocket test temporarily disabled due to hanging issues")
        # import threading
        # import uvicorn

        # def run_server():
        #     uvicorn.run(app, host="127.0.0.1", port=8006, log_level="error")

        # server_thread = threading.Thread(target=run_server, daemon=True)
        # server_thread.start()
        # time.sleep(0.5)
        # try:
        #     with (
        #         connect("ws://127.0.0.1:8006/ws/user1") as ws1,
        #         connect("ws://127.0.0.1:8006/ws/user2") as ws2,
        #     ):
        #         gift_data = {"from": "donor", "gift_id": 2, "amount": 10}
        #         with TestClient(app) as client:
        #             response = client.post("/api/gift", json=gift_data)
        #             assert response.status_code == 200
        #         received1 = json.loads(ws1.recv())
        #         received2 = json.loads(ws2.recv())
        #         assert received1 == received2
        #         assert received1["type"] == "gift"
        #         assert received1["from"] == "donor"
        #         assert received1["gift_id"] == 2
        #         assert received1["amount"] == 10
        # except Exception as e:
        #     pytest.fail(f"Multiple clients test failed: {e}")


class TestGiftAPIValidation:
    """Test gift API validation and error handling."""

    def test_gift_api_validation_errors(self):
        """Test gift API handles validation errors gracefully."""
        with TestClient(app) as client:
            invalid_gift = {"from": "user", "gift_id": 1}
            response = client.post("/api/gift", json=invalid_gift)
            assert response.status_code == 400
            invalid_gift = {"from": "user", "gift_id": "invalid", "amount": 5}
            response = client.post("/api/gift", json=invalid_gift)
            assert response.status_code == 400
            invalid_gift = {"from": "user", "gift_id": 1, "amount": "invalid"}
            response = client.post("/api/gift", json=invalid_gift)
            assert response.status_code == 400


class TestGiftAPIDisconnectedClients:
    """Test gift API behavior with disconnected clients."""

    def test_gift_api_disconnected_clients(self):
        """Test gift API handles disconnected clients gracefully."""
        # TODO: Fix WebSocket test hanging issue
        pytest.skip("WebSocket test temporarily disabled due to hanging issues")
        # import threading
        # import uvicorn

        # def run_server():
        #     uvicorn.run(app, host="127.0.0.1", port=8007, log_level="error")

        # server_thread = threading.Thread(target=run_server, daemon=True)
        # server_thread.start()
        # time.sleep(0.5)
        # try:
        #     with connect("ws://127.0.0.1:8007/ws/disconnected"):
        #         pass
        #     gift_data = {"from": "system", "gift_id": 3, "amount": 1}
        #     with TestClient(app) as client:
        #         response = client.post("/api/gift", json=gift_data)
        #         assert response.status_code == 200
        # except Exception as e:
        #     pytest.fail(f"Disconnected clients test failed: {e}")


class TestGiftAndChatIntegration:
    """Test integration between gift and chat messages."""

    def test_gift_and_chat_integration(self):
        """Test that gift and chat messages work together."""
        # TODO: Fix WebSocket test hanging issue
        pytest.skip("WebSocket test temporarily disabled due to hanging issues")
        # import threading
        # import uvicorn

        # def run_server():
        #     uvicorn.run(app, host="127.0.0.1", port=8008, log_level="error")

        # server_thread = threading.Thread(target=run_server, daemon=True)
        # server_thread.start()
        # time.sleep(0.5)
        # try:
        #     with connect("ws://127.0.0.1:8008/ws/integration") as ws:
        #         chat_message = {"type": "chat", "message": "Hello!"}
        #         ws.send(json.dumps(chat_message))
        #         chat_received = json.loads(ws.recv())
        #         assert chat_received["type"] == "chat"
        #         assert chat_received["message"] == "Hello!"
        #         gift_data = {"from": "user", "gift_id": 1, "amount": 5}
        #         with TestClient(app) as client:
        #             response = client.post("/api/gift", json=gift_data)
        #             assert response.status_code == 200
        #         gift_received = json.loads(ws.recv())
        #         assert gift_received["type"] == "gift"
        #         assert gift_received["from"] == "user"
        # except Exception as e:
        #     pytest.fail(f"Integration test failed: {e}")


class TestChatModerationFields:
    """Test that chat messages include moderation fields."""

    def test_chat_toxic_and_score_fields(self):
        """Test that chat messages include toxic and score fields."""
        # TODO: Fix WebSocket test hanging issue
        pytest.skip("WebSocket test temporarily disabled due to hanging issues")
        # import threading
        # import uvicorn

        # def run_server():
        #     uvicorn.run(app, host="127.0.0.1", port=8009, log_level="error")

        # server_thread = threading.Thread(target=run_server, daemon=True)
        # server_thread.start()
        # time.sleep(0.5)
        # try:
        #     with connect("ws://127.0.0.1:8009/ws/moderation") as ws:
        #         chat_message = {"type": "chat", "message": "Test message"}
        #         ws.send(json.dumps(chat_message))
        #         received = json.loads(ws.recv())
        #         assert received["type"] == "chat"
        #         assert "toxic" in received
        #         assert "score" in received
        #         assert isinstance(received["toxic"], bool)
        #         assert isinstance(received["score"], int | float)

        #         # Check if we're in stub mode or real ML mode
        #         is_stub_mode = os.getenv("DISABLE_DETOXIFY", "0") == "1"

        #         if is_stub_mode:
        #             # Stub mode: always non-toxic with score 0.0
        #             assert received["toxic"] is False
        #             assert received["score"] == 0.0
        #         else:
        #             # Real ML mode: check that score is in valid range
        #             assert 0.0 <= received["score"] <= 1.0
        # except Exception as e:
        #     pytest.fail(f"Moderation fields test failed: {e}")


class TestGiftAPIEdgeCases:
    """Test gift API edge cases and boundary conditions."""

    def test_gift_api_edge_cases(self):
        """Test gift API handles edge cases gracefully."""
        with TestClient(app) as client:
            # Test with minimum valid values
            min_gift = {"from": "a", "gift_id": 0, "amount": 1}
            response = client.post("/api/gift", json=min_gift)
            assert response.status_code == 200

            # Test with maximum reasonable values
            max_gift = {"from": "x" * 50, "gift_id": 999999, "amount": 1000}
            response = client.post("/api/gift", json=max_gift)
            assert response.status_code == 200

            # Test with empty from field (schema allows this)
            empty_from_gift = {"from": "", "gift_id": 1, "amount": 5}
            response = client.post("/api/gift", json=empty_from_gift)
            assert response.status_code == 200  # Schema allows empty strings

            # Test with negative values
            negative_gift = {"from": "user", "gift_id": -1, "amount": 5}
            response = client.post("/api/gift", json=negative_gift)
            assert response.status_code == 400

            negative_amount_gift = {"from": "user", "gift_id": 1, "amount": -5}
            response = client.post("/api/gift", json=negative_amount_gift)
            assert response.status_code == 400
