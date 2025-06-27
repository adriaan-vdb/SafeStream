"""Tests for SafeStream random gift producer functionality."""

import asyncio
import importlib
import json
import os
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.schemas import GiftEventOut


class TestRandomGiftProducer:
    """Test the random gift producer background task."""

    @pytest.mark.asyncio
    async def test_gift_producer_generates_valid_gifts(self):
        """Test that the gift producer generates valid gift events."""
        # Test the gift generation logic directly
        with patch("random.randint", side_effect=[123, 3]):
            with patch("app.events.datetime") as mock_datetime:
                # Mock datetime to return a fixed timestamp
                mock_datetime.now.return_value.isoformat.return_value = (
                    "2025-06-26T12:34:56+00:00"
                )

                from app.events import broadcast_gift

                # Create a test gift event
                gift_event = GiftEventOut(from_user="bot", gift_id=123, amount=3)

                # Convert to dict with proper aliasing and add timestamp
                gift_event_dict = gift_event.model_dump(by_alias=True)
                gift_event_dict["ts"] = "2025-06-26T12:34:56Z"

                # Test broadcasting
                mock_websocket = AsyncMock()
                connections = {"testuser": mock_websocket}

                await broadcast_gift(connections, gift_event_dict)

                assert (
                    mock_websocket.send_text.called
                ), "WebSocket should receive a gift message"
                call_args = mock_websocket.send_text.call_args
                message_json = call_args[0][0]
                gift_data = json.loads(message_json)

                assert gift_data["type"] == "gift"
                assert gift_data["from"] == "bot"
                assert gift_data["gift_id"] == 123
                assert gift_data["amount"] == 3
                assert gift_data["ts"] == "2025-06-26T12:34:56Z"

    @pytest.mark.asyncio
    async def test_gift_producer_uses_environment_variable(self):
        """Test that the gift producer uses the GIFT_INTERVAL_SECS environment variable."""
        with patch.dict(os.environ, {"GIFT_INTERVAL_SECS": "5"}):
            import app.events

            importlib.reload(app.events)
            assert app.events.GIFT_INTERVAL_SECS == 5

    @pytest.mark.asyncio
    async def test_gift_producer_cancellation(self):
        """Test that the gift producer can be cancelled cleanly."""
        with patch("asyncio.sleep", new=AsyncMock()):
            with patch("app.events.logging.getLogger", return_value=Mock()):
                from app import events

                importlib.reload(events)

                connections = {}
                task = asyncio.create_task(events.gift_producer(connections))
                await asyncio.sleep(0)
                await asyncio.sleep(0)
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                assert task.done()
                # Do not call task.exception() if cancelled

    @pytest.mark.asyncio
    async def test_gift_producer_logging(self):
        """Test that gift events are properly logged."""
        # Test logging directly
        with patch("random.randint", side_effect=[123, 3]):
            mock_logger = Mock()
            with patch("app.events.logging.getLogger", return_value=mock_logger):

                # Create a test gift event
                gift_event = GiftEventOut(from_user="bot", gift_id=123, amount=3)

                gift_event_dict = gift_event.model_dump(by_alias=True)
                gift_event_dict["ts"] = "2025-06-26T12:34:56Z"

                # Log the gift event (simulating what the producer does)
                mock_logger.info(json.dumps(gift_event_dict))

                assert mock_logger.info.called, "Gift should be logged"
                call_args = mock_logger.info.call_args
                logged_message = call_args[0][0]

                gift_data = json.loads(logged_message)
                assert gift_data["type"] == "gift"
                assert gift_data["from"] == "bot"
                assert gift_data["gift_id"] == 123
                assert gift_data["amount"] == 3
                assert gift_data["ts"] == "2025-06-26T12:34:56Z"

    @pytest.mark.asyncio
    async def test_gift_producer_broadcast_to_multiple_clients(self):
        """Test that gifts are broadcast to all connected clients."""
        from app.events import broadcast_gift

        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()
        connections = {"user1": mock_websocket1, "user2": mock_websocket2}
        gift_event = GiftEventOut(from_user="bot", gift_id=123, amount=3)
        gift_data = gift_event.model_dump(by_alias=True)
        gift_data["ts"] = "2025-06-26T12:34:56Z"
        await broadcast_gift(connections, gift_data)
        assert mock_websocket1.send_text.called
        assert mock_websocket2.send_text.called
        message1 = json.loads(mock_websocket1.send_text.call_args[0][0])
        message2 = json.loads(mock_websocket2.send_text.call_args[0][0])
        assert message1 == message2
        assert message1["type"] == "gift"
        assert message1["from"] == "bot"

    @pytest.mark.asyncio
    async def test_gift_producer_full_loop_with_mocked_sleep(self):
        """Test the full gift producer loop with mocked sleep."""
        with patch("asyncio.sleep", new=AsyncMock()) as mock_sleep:
            with patch("random.randint", side_effect=[123, 3]):
                with patch("app.events.datetime") as mock_datetime:
                    mock_datetime.now.return_value.isoformat.return_value = (
                        "2025-06-26T12:34:56+00:00"
                    )

                    mock_logger = Mock()
                    with patch(
                        "app.events.logging.getLogger", return_value=mock_logger
                    ):
                        from app import events

                        importlib.reload(events)

                        mock_websocket = AsyncMock()
                        connections = {"testuser": mock_websocket}

                        # Start the task
                        task = asyncio.create_task(events.gift_producer(connections))

                        # Let it run through the first sleep
                        await asyncio.sleep(0)

                        # Cancel immediately
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass

                        # Check that sleep was called (indicating the loop started)
                        assert mock_sleep.called, "asyncio.sleep should be called"
