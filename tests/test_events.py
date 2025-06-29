"""Tests for SafeStream events module."""

import asyncio
import json
from unittest.mock import AsyncMock

import pytest

from app import events


class TestGiftSimulation:
    """Test gift simulation functionality."""

    @pytest.mark.asyncio
    async def test_broadcast_gift_sends_to_all_connections(self):
        """Test that broadcast_gift sends messages to all connected clients."""
        # Create mock WebSocket connections
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        connections = {mock_ws1, mock_ws2}

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

        connections = {mock_ws1, mock_ws2}

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

        # Verify mock_ws2 was removed from connections
        assert mock_ws1 in connections
        assert mock_ws2 not in connections  # Should be removed after failed send

        # Verify only mock_ws1 received the message
        mock_ws1.send_text.assert_called_once_with(json.dumps(gift_data))

    @pytest.mark.asyncio
    async def test_create_gift_task_returns_task(self):
        """Test that create_gift_task returns an asyncio task."""
        connections = set()

        task = await events.create_gift_task(connections)

        assert isinstance(task, asyncio.Task)
        assert not task.done()

        # Clean up
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
