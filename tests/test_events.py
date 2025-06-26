"""Tests for SafeStream events module."""

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

from app import events, schemas


class TestGiftSimulation:
    """Test gift simulation functionality."""

    @pytest.mark.asyncio
    async def test_broadcast_gift_sends_to_all_connections(self):
        """Test that broadcast_gift sends messages to all connected clients."""
        # Create mock WebSocket connections
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        connections = {"user1": mock_ws1, "user2": mock_ws2}

        # Test gift data
        gift_data = {
            "type": "gift",
            "from": "admin",
            "gift_id": 999,
            "amount": 1,
            "ts": "2025-01-01T12:00:00Z",
        }

        # Call broadcast function
        await events.broadcast_gift(connections, gift_data)

        # Verify messages were sent to both clients
        mock_ws1.send_text.assert_called_once_with(json.dumps(gift_data))
        mock_ws2.send_text.assert_called_once_with(json.dumps(gift_data))

    @pytest.mark.asyncio
    async def test_broadcast_gift_removes_disconnected_clients(self):
        """Test that broadcast_gift removes disconnected clients."""
        # Create mock WebSocket connections
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        mock_ws2.send_text.side_effect = Exception("Connection lost")

        connections = {"user1": mock_ws1, "user2": mock_ws2}

        # Test gift data
        gift_data = {
            "type": "gift",
            "from": "admin",
            "gift_id": 999,
            "amount": 1,
            "ts": "2025-01-01T12:00:00Z",
        }

        # Call broadcast function
        await events.broadcast_gift(connections, gift_data)

        # Verify user2 was removed from connections
        assert "user1" in connections
        assert "user2" not in connections

        # Verify only user1 received the message
        mock_ws1.send_text.assert_called_once_with(json.dumps(gift_data))

    @pytest.mark.asyncio
    async def test_create_gift_task_returns_task(self):
        """Test that create_gift_task returns an asyncio task."""
        connections = {}

        task = await events.create_gift_task(connections)

        assert isinstance(task, asyncio.Task)
        assert not task.done()

        # Clean up
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    def test_sample_gifts_are_valid(self):
        """Test that all sample gifts conform to the GiftEventOut schema."""
        for gift_data in events.SAMPLE_GIFTS:
            # This should not raise any validation errors
            gift_event = schemas.GiftEventOut(**gift_data)
            assert gift_event.from_user in [
                "admin",
                "moderator",
                "viewer",
                "fan",
                "supporter",
            ]
            assert isinstance(gift_event.gift_id, int)
            assert isinstance(gift_event.amount, int)
            assert gift_event.amount > 0

    @pytest.mark.asyncio
    async def test_gift_simulation_uses_environment_variables(self):
        """Test that gift simulation respects environment variables."""
        with patch.dict("os.environ", {"GIFT_RATE_SEC": "30"}):
            # Reload the module to pick up new env var
            import importlib

            import app.events

            importlib.reload(app.events)

            assert app.events.GIFT_RATE_SEC == 30

            # Reset to default
            importlib.reload(app.events)
