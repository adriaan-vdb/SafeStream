"""Tests for SafeStream metrics functionality.

Tests live metrics including viewer count, gift count, and toxic percentage.
"""

import json
import time

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.metrics import MetricsTracker, metrics


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


@pytest.fixture(autouse=True)
def reset_metrics():
    metrics.reset()
    yield


class TestMetricsTracker:
    """Test the MetricsTracker class functionality."""

    def test_initial_state(self):
        """Test that metrics tracker starts with zero values."""
        tracker = MetricsTracker()
        assert tracker.gift_count == 0
        assert tracker.chat_message_total == 0
        assert tracker.toxic_message_total == 0

    def test_viewer_count(self):
        """Test viewer count calculation."""
        tracker = MetricsTracker()
        connected = {"user1": "ws1", "user2": "ws2", "user3": "ws3"}
        assert tracker.get_viewer_count(connected) == 3

    def test_viewer_count_empty(self):
        """Test viewer count with no connections."""
        tracker = MetricsTracker()
        connected = {}
        assert tracker.get_viewer_count(connected) == 0

    def test_increment_gift_count(self):
        """Test gift count increment."""
        tracker = MetricsTracker()
        assert tracker.gift_count == 0
        tracker.increment_gift_count()
        assert tracker.gift_count == 1
        tracker.increment_gift_count()
        assert tracker.gift_count == 2

    def test_increment_chat_message_non_toxic(self):
        """Test chat message increment for non-toxic message."""
        tracker = MetricsTracker()
        tracker.increment_chat_message(is_toxic=False)
        assert tracker.chat_message_total == 1
        assert tracker.toxic_message_total == 0

    def test_increment_chat_message_toxic(self):
        """Test chat message increment for toxic message."""
        tracker = MetricsTracker()
        tracker.increment_chat_message(is_toxic=True)
        assert tracker.chat_message_total == 1
        assert tracker.toxic_message_total == 1

    def test_toxic_percentage_no_messages(self):
        """Test toxic percentage with no messages."""
        tracker = MetricsTracker()
        assert tracker.get_toxic_percentage() == 0.0

    def test_toxic_percentage_all_non_toxic(self):
        """Test toxic percentage with all non-toxic messages."""
        tracker = MetricsTracker()
        tracker.increment_chat_message(is_toxic=False)
        tracker.increment_chat_message(is_toxic=False)
        tracker.increment_chat_message(is_toxic=False)
        assert tracker.get_toxic_percentage() == 0.0

    def test_toxic_percentage_all_toxic(self):
        """Test toxic percentage with all toxic messages."""
        tracker = MetricsTracker()
        tracker.increment_chat_message(is_toxic=True)
        tracker.increment_chat_message(is_toxic=True)
        assert tracker.get_toxic_percentage() == 100.0

    def test_toxic_percentage_mixed(self):
        """Test toxic percentage with mixed toxic/non-toxic messages."""
        tracker = MetricsTracker()
        tracker.increment_chat_message(is_toxic=False)
        tracker.increment_chat_message(is_toxic=True)
        tracker.increment_chat_message(is_toxic=False)
        tracker.increment_chat_message(is_toxic=True)
        assert tracker.get_toxic_percentage() == 50.0

    def test_get_metrics(self):
        """Test getting all metrics together."""
        tracker = MetricsTracker()
        connected = {"user1": "ws1", "user2": "ws2"}

        # Add some activity
        tracker.increment_gift_count()
        tracker.increment_chat_message(is_toxic=False)
        tracker.increment_chat_message(is_toxic=True)

        metrics = tracker.get_metrics(connected)
        assert metrics["viewer_count"] == 2
        assert metrics["gift_count"] == 1
        assert metrics["toxic_pct"] == 50.0


class TestMetricsAPI:
    """Test the metrics API endpoint."""

    def test_metrics_endpoint_empty(self):
        """Test metrics endpoint with no activity."""
        app = create_app(testing=True)
        with TestClient(app) as client:
            response = client.get("/metrics")
            assert response.status_code == 200
            data = response.json()
            assert "viewer_count" in data
            assert "gift_count" in data
            assert "toxic_pct" in data
            assert data["viewer_count"] == 0
            assert data["gift_count"] == 0
            assert data["toxic_pct"] == 0.0

    def test_metrics_endpoint_with_activity(self):
        """Test metrics endpoint after some activity."""
        app = create_app(testing=True)
        with TestClient(app) as client:
            # Create test user and get token
            username = get_unique_username("testuser")
            token = create_test_user_and_token(client, username)

            with client.websocket_connect(f"/ws/{username}?token={token}") as ws:
                message = {"type": "chat", "message": "Hello!"}
                ws.send_text(json.dumps(message))
                response = json.loads(ws.receive_text())
                assert response["type"] == "chat"
            gift_data = {"from": "admin", "gift_id": 1, "amount": 5}
            response = client.post("/api/gift", json=gift_data)
            assert response.status_code == 200
            metrics_response = client.get("/metrics")
            assert metrics_response.status_code == 200
            data = metrics_response.json()
            assert data["viewer_count"] == 0
            assert data["gift_count"] == 1
            assert data["toxic_pct"] == 0.0


class TestMetricsIntegration:
    """Test metrics integration with WebSocket and gift API."""

    def test_metrics_track_chat_messages(self):
        """Test that chat messages are tracked in metrics."""
        app = create_app(testing=True)
        with TestClient(app) as client:
            # Create test user and get token
            username = get_unique_username("user1")
            token = create_test_user_and_token(client, username)

            with client.websocket_connect(f"/ws/{username}?token={token}") as ws:
                message1 = {"type": "chat", "message": "Hello everyone!"}
                ws.send_text(json.dumps(message1))
                response1 = json.loads(ws.receive_text())
                assert response1["toxic"] is False
                message2 = {"type": "chat", "message": "You are stupid and worthless"}
                ws.send_text(json.dumps(message2))
                json.loads(ws.receive_text())
            metrics_response = client.get("/metrics")
            data = metrics_response.json()
            assert data["viewer_count"] == 0
            assert "toxic_pct" in data

    def test_metrics_track_gift_events(self):
        """Test that gift events are tracked in metrics."""
        app = create_app(testing=True)
        with TestClient(app) as client:
            for i in range(3):
                gift_data = {"from": f"user{i}", "gift_id": i, "amount": 1}
                response = client.post("/api/gift", json=gift_data)
                assert response.status_code == 200
            metrics_response = client.get("/metrics")
            data = metrics_response.json()
            assert data["gift_count"] == 3

    def test_metrics_viewer_count(self):
        """Test that viewer count reflects active connections."""
        app = create_app(testing=True)
        with TestClient(app) as client:
            # Create test users and get tokens
            user1_username = get_unique_username("user1")
            user2_username = get_unique_username("user2")

            user1_token = create_test_user_and_token(client, user1_username)
            user2_token = create_test_user_and_token(client, user2_username)

            metrics_response = client.get("/metrics")
            data = metrics_response.json()
            assert data["viewer_count"] == 0
            with client.websocket_connect(f"/ws/{user1_username}?token={user1_token}"):
                metrics_response = client.get("/metrics")
                data = metrics_response.json()
                assert data["viewer_count"] == 1
                with client.websocket_connect(
                    f"/ws/{user2_username}?token={user2_token}"
                ):
                    metrics_response = client.get("/metrics")
                    data = metrics_response.json()
                    assert data["viewer_count"] == 2
                metrics_response = client.get("/metrics")
                data = metrics_response.json()
                assert data["viewer_count"] == 1
            metrics_response = client.get("/metrics")
            data = metrics_response.json()
            assert data["viewer_count"] == 0
