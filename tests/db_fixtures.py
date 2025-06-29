"""Database test fixtures for SafeStream.

Provides in-memory SQLite database for testing with proper session management
and configuration patching.
"""

import asyncio
import os
import tempfile
from unittest.mock import patch

import pytest

from app.config import Settings
from app.db import async_session, init_db


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def temp_db():
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
        temp_db_path = temp_file.name

    # Clean up the file so SQLite can create it fresh
    os.unlink(temp_db_path)

    yield temp_db_path

    # Clean up after test
    if os.path.exists(temp_db_path):
        os.unlink(temp_db_path)


@pytest.fixture(scope="function")
async def test_db_session(temp_db):
    """Create a test database session with temporary database."""
    # Create test database URL
    test_db_url = f"sqlite+aiosqlite:///{temp_db}"

    # Patch the settings to use test database
    with patch.object(Settings, "DATABASE_URL", test_db_url):
        # Patch the database configuration
        with patch("app.db.settings.DATABASE_URL", test_db_url):
            # Initialize test database
            await init_db()

            # Create a test session
            async with async_session() as session:
                yield session
                # Rollback any changes after test
                await session.rollback()


@pytest.fixture(scope="function")
async def memory_db_session():
    """Create an in-memory SQLite database session for testing."""
    # Use in-memory SQLite database
    test_db_url = "sqlite+aiosqlite:///:memory:"

    # Patch the settings to use in-memory database
    with patch.object(Settings, "DATABASE_URL", test_db_url):
        # Patch the database configuration
        with patch("app.db.settings.DATABASE_URL", test_db_url):
            # Initialize in-memory database
            await init_db()

            # Create a test session
            async with async_session() as session:
                yield session
                # No cleanup needed for in-memory database


@pytest.fixture(scope="function")
def patch_database_url():
    """Patch DATABASE_URL environment variable for testing."""
    test_db_url = "sqlite+aiosqlite:///:memory:"

    with patch.dict(os.environ, {"DATABASE_URL": test_db_url}):
        yield test_db_url


@pytest.fixture(scope="function")
async def clean_db_session():
    """Create a clean database session that gets reset after each test."""
    # Use in-memory database for speed
    test_db_url = "sqlite+aiosqlite:///:memory:"

    # Patch configuration
    with patch.object(Settings, "DATABASE_URL", test_db_url):
        with patch("app.db.settings.DATABASE_URL", test_db_url):
            # Initialize database
            await init_db()

            # Provide session
            async with async_session() as session:
                try:
                    yield session
                finally:
                    # Clean up by rolling back any uncommitted changes
                    await session.rollback()


@pytest.fixture(scope="function")
def mock_db_failure():
    """Mock database failures for testing fallback behavior."""

    def _mock_session_failure(*args, **kwargs):
        raise Exception("Mocked database connection failure")

    with patch("app.db.async_session", side_effect=_mock_session_failure):
        yield


@pytest.fixture(scope="function")
async def populated_test_db():
    """Create a test database with some sample data."""
    from app.services import database as db_service

    # Use in-memory database
    test_db_url = "sqlite+aiosqlite:///:memory:"

    with patch.object(Settings, "DATABASE_URL", test_db_url):
        with patch("app.db.settings.DATABASE_URL", test_db_url):
            # Initialize database
            await init_db()

            # Create sample data
            async with async_session() as session:
                # Create test users
                user1 = await db_service.create_user(
                    session, "testuser1", "test1@example.com", "hashed_password_1"
                )
                user2 = await db_service.create_user(
                    session, "testuser2", "test2@example.com", "hashed_password_2"
                )

                # Create test messages
                await db_service.save_message(
                    session, user1.id, "Hello world!", False, 0.01, "chat"
                )
                await db_service.save_message(
                    session, user2.id, "This is toxic content", True, 0.95, "chat"
                )

                # Create test gift event
                await db_service.save_gift_event(session, user1.id, "heart", 5)

                # Create test admin action
                await db_service.log_admin_action(
                    session, user2.id, "kick", user1.id, "Test kick action"
                )

                yield session
