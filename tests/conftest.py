"""Pytest configuration and fixtures for SafeStream tests.

This file sets up the testing environment and provides common fixtures
for unit tests, integration tests, and future WebSocket E2E tests.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.schemas import ChatMessageIn, ChatMessageOut, GiftEventOut


@pytest.fixture
def client():
    """Provide a test client for FastAPI application."""
    app = create_app(testing=True)
    return TestClient(app)


@pytest.fixture
def websocket_client():
    """Provide a WebSocket test client for future WebSocket tests.

    TODO(stage-2): Implement WebSocket test client using websockets library
    """
    # TODO(stage-2): from websockets.sync.client import connect
    # TODO(stage-2): return connect("ws://localhost:8000/ws/testuser")
    pass


@pytest.fixture
def sample_chat_message():
    """Provide a sample chat message for testing.

    Uses actual Pydantic model for type safety and validation.
    """
    return ChatMessageIn(message="Hello, world!")


@pytest.fixture
def sample_chat_message_out():
    """Provide a sample outgoing chat message for testing.

    Uses actual Pydantic model with moderation results.
    """
    return ChatMessageOut(
        user="testuser",
        message="Hello, world!",
        toxic=False,
        score=0.02,
        ts=datetime.now(),
    )


@pytest.fixture
def sample_gift_event():
    """Provide a sample gift event for testing.

    Uses actual Pydantic model for type safety and validation.
    """
    return GiftEventOut(from_user="admin", gift_id=999, amount=1)
