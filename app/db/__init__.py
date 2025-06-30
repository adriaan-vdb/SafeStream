"""SafeStream database module.

Provides SQLAlchemy 2 async database setup with session management
and initialization functions.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


# Create async engine
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.db_echo,
    future=True,
)

# Create async session factory
async_session = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Initialize database by creating all tables and demo accounts."""
    # Create tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create demo accounts if they don't exist
    await _create_demo_accounts()


async def close_db() -> None:
    """Close database connections."""
    await async_engine.dispose()


async def _create_demo_accounts() -> None:
    """Create demo accounts for testing if they don't exist."""
    from app.auth import get_password_hash
    from app.services import database as db_service

    demo_accounts = [
        {"username": "demo_user", "email": "demo_user@safestream.local"},
        {"username": "test_streamer", "email": "test_streamer@safestream.local"},
        {"username": "chat_viewer", "email": "chat_viewer@safestream.local"},
    ]

    async with async_session() as session:
        for account in demo_accounts:
            # Check if user already exists
            existing_user = await db_service.get_user_by_username(
                session, account["username"]
            )
            if not existing_user:
                # Create user with password same as username
                hashed_password = get_password_hash(account["username"])
                await db_service.create_user(
                    session, account["username"], account["email"], hashed_password
                )
                print(f"Created demo account: {account['username']}")


# Import models after Base is defined to avoid circular imports
from app.db.models import (  # noqa: E402
    AdminAction,
    GiftEvent,
    Message,
    Setting,
    User,
    UserSession,
)

# Export public API
__all__ = [
    "Base",
    "async_engine",
    "async_session",
    "init_db",
    "close_db",
    # Models
    "User",
    "Message",
    "GiftEvent",
    "AdminAction",
    "UserSession",
    "Setting",
]
