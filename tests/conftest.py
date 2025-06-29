"""Pytest configuration and fixtures for SafeStream tests.

This file sets up the testing environment and provides common fixtures
for unit tests, integration tests, and future WebSocket E2E tests.
"""

from datetime import datetime

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.main import create_app
from app.schemas import ChatMessageIn, ChatMessageOut, GiftEventOut


@pytest_asyncio.fixture
async def async_engine_e2e():
    """Provide a fresh in-memory SQLite async engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", echo=False, future=True
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(async_engine_e2e):
    """Provide an AsyncSession scoped per-function with transaction rollback."""
    async_session = sessionmaker(
        async_engine_e2e, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Begin a transaction
        transaction = await session.begin()

        yield session

        # Rollback the transaction to clean up
        await transaction.rollback()


@pytest_asyncio.fixture
async def sample_user():
    """Provide a pre-created user object for testing."""
    import os
    import random
    import string
    from unittest.mock import patch

    from app.auth import get_password_hash
    from app.db import async_session, init_db
    from app.services import database as db_service

    # Generate unique username for each test
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    username = f"testuser_sample_{suffix}"
    password = "testpass123"
    email = f"testuser_{suffix}@example.com"

    # Use in-memory database
    test_db_url = "sqlite+aiosqlite:///:memory:"

    with patch.dict(os.environ, {"DATABASE_URL": test_db_url}):
        # Re-import settings to pick up new environment variable
        from app.config import Settings

        test_settings = Settings()

        with patch("app.db.settings", test_settings):
            # Initialize database
            await init_db()

            # Create sample user with proper database session
            async with async_session() as session:
                hashed_password = get_password_hash(password)
                user = await db_service.create_user(
                    session, username, email, hashed_password
                )
                yield user


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
