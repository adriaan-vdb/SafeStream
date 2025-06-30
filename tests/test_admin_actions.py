"""Tests for admin actions: kick and mute functionality."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import database as db_service


@pytest.mark.asyncio
class TestMuteServiceFunctions:
    """Test suite for mute-related database service functions."""

    async def test_set_and_get_user_mute(self, test_session: AsyncSession):
        """Test setting and getting user mute status."""
        # Create a test user
        user = await db_service.create_user(
            test_session, "test_user", "test@example.com", "hashed_password"
        )

        # Set mute for 5 minutes from now
        mute_until = datetime.now(UTC) + timedelta(minutes=5)
        result = await db_service.set_user_mute(test_session, user.id, mute_until)
        assert result is True

        # Get mute status
        retrieved_mute = await db_service.get_user_mute(test_session, user.id)
        assert retrieved_mute is not None

        # Times should be very close (within 1 second)
        time_diff = abs(
            (retrieved_mute.replace(tzinfo=UTC) - mute_until).total_seconds()
        )
        assert time_diff < 1

    async def test_is_user_muted_active_mute(self, test_session: AsyncSession):
        """Test is_user_muted returns True for active mute."""
        # Create a test user
        user = await db_service.create_user(
            test_session, "test_user", "test@example.com", "hashed_password"
        )

        # Set mute for 5 minutes from now
        mute_until = datetime.now(UTC) + timedelta(minutes=5)
        await db_service.set_user_mute(test_session, user.id, mute_until)

        # Check if user is muted
        is_muted = await db_service.is_user_muted(test_session, user.id)
        assert is_muted is True

    async def test_delete_existing_user(self, test_session: AsyncSession):
        """Test deleting an existing user."""
        # Create a test user
        user = await db_service.create_user(
            test_session, "test_user", "test@example.com", "hashed_password"
        )
        user_id = user.id

        # Delete the user
        deleted = await db_service.delete_user(test_session, user_id)
        assert deleted is True

        # Verify user is gone
        deleted_user = await db_service.get_user_by_username(test_session, "test_user")
        assert deleted_user is None
