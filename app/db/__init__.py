"""SafeStream database module.

Provides SQLAlchemy 2 async database setup with session management
and initialization functions.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings
from app.db.models import AdminAction, GiftEvent, Message, User


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
    """Initialize database by creating all tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await async_engine.dispose()


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
]
