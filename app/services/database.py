"""SafeStream database service layer.

Provides async database operations using SQLAlchemy 2.0 ORM patterns.
This service layer encapsulates all database interactions for users, messages,
gifts, and admin actions with proper type safety and async patterns.
"""

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AdminAction, GiftEvent, Message, User

# ============================================================================
# USER OPERATIONS
# ============================================================================


async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
    """Get user by username.

    Args:
        session: Async SQLAlchemy session
        username: Username to search for

    Returns:
        User instance if found, None otherwise
    """
    stmt = select(User).where(User.username == username)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Get user by email address.

    Args:
        session: Async SQLAlchemy session
        email: Email address to search for

    Returns:
        User instance if found, None otherwise
    """
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession, username: str, email: str | None, hashed_password: str
) -> User:
    """Create a new user.

    Args:
        session: Async SQLAlchemy session
        username: Unique username
        email: Email address (optional)
        hashed_password: BCrypt hashed password

    Returns:
        Created User instance

    Raises:
        IntegrityError: If username or email already exists
    """
    user = User(
        username=username,
        email=email or f"{username}@safestream.local",  # Default email if none provided
        hashed_password=hashed_password,
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate_user(
    session: AsyncSession, username: str, password: str
) -> User | None:
    """Authenticate user with username and password.

    Args:
        session: Async SQLAlchemy session
        username: Username to authenticate
        password: Plain text password to verify

    Returns:
        User instance if authentication successful, None otherwise
    """
    # Import here to avoid circular imports
    from app.auth import verify_password

    user = await get_user_by_username(session, username)
    if user and user.is_active and verify_password(password, user.hashed_password):
        return user
    return None


# ============================================================================
# MESSAGE OPERATIONS
# ============================================================================


async def save_message(
    session: AsyncSession,
    user_id: int,
    text: str,
    toxic: bool,
    score: float | None = None,
    message_type: str = "chat",
) -> Message:
    """Save a chat message to the database.

    Args:
        session: Async SQLAlchemy session
        user_id: ID of the user sending the message
        text: Message content
        toxic: Whether the message is flagged as toxic
        score: Toxicity confidence score (0.0-1.0)
        message_type: Type of message (chat, system, admin, etc.)

    Returns:
        Created Message instance
    """
    message = Message(
        user_id=user_id,
        message_text=text,
        toxicity_flag=toxic,
        toxicity_score=score,
        message_type=message_type,
    )
    session.add(message)
    await session.commit()
    await session.refresh(message)
    return message


async def get_recent_messages(session: AsyncSession, limit: int = 100) -> list[Message]:
    """Get recent messages ordered by timestamp (newest first).

    Args:
        session: Async SQLAlchemy session
        limit: Maximum number of messages to return

    Returns:
        List of Message instances ordered by timestamp desc
    """
    stmt = select(Message).order_by(desc(Message.timestamp)).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_messages_by_user(
    session: AsyncSession, user_id: int, limit: int = 50
) -> list[Message]:
    """Get messages by a specific user.

    Args:
        session: Async SQLAlchemy session
        user_id: ID of the user whose messages to retrieve
        limit: Maximum number of messages to return

    Returns:
        List of Message instances ordered by timestamp desc
    """
    stmt = (
        select(Message)
        .where(Message.user_id == user_id)
        .order_by(desc(Message.timestamp))
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


# ============================================================================
# GIFT OPERATIONS
# ============================================================================


async def save_gift_event(
    session: AsyncSession, from_user_id: int, gift_id: str, amount: int
) -> GiftEvent:
    """Save a gift event to the database.

    Args:
        session: Async SQLAlchemy session
        from_user_id: ID of the user sending the gift
        gift_id: Identifier for the gift type
        amount: Quantity of gifts sent

    Returns:
        Created GiftEvent instance
    """
    gift_event = GiftEvent(from_user_id=from_user_id, gift_id=gift_id, amount=amount)
    session.add(gift_event)
    await session.commit()
    await session.refresh(gift_event)
    return gift_event


# ============================================================================
# ADMIN ACTIONS
# ============================================================================


async def log_admin_action(
    session: AsyncSession,
    admin_user_id: int,
    action: str,
    target_user_id: int | None = None,
    action_details: str | None = None,
) -> AdminAction:
    """Log an administrative action.

    Args:
        session: Async SQLAlchemy session
        admin_user_id: ID of the admin user performing the action
        action: Type of action performed (ban, kick, warn, etc.)
        target_user_id: ID of the user being acted upon (optional)
        action_details: Additional context about the action (optional)

    Returns:
        Created AdminAction instance
    """
    admin_action = AdminAction(
        admin_user_id=admin_user_id,
        action=action,
        target_user_id=target_user_id,
        action_details=action_details,
    )
    session.add(admin_action)
    await session.commit()
    await session.refresh(admin_action)
    return admin_action


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


async def get_user_message_count(session: AsyncSession, user_id: int) -> int:
    """Get total message count for a user.

    Args:
        session: Async SQLAlchemy session
        user_id: ID of the user

    Returns:
        Total number of messages sent by the user
    """
    stmt = select(Message).where(Message.user_id == user_id)
    result = await session.execute(stmt)
    return len(list(result.scalars().all()))


async def get_toxic_message_count(session: AsyncSession, user_id: int) -> int:
    """Get toxic message count for a user.

    Args:
        session: Async SQLAlchemy session
        user_id: ID of the user

    Returns:
        Number of toxic messages sent by the user
    """
    stmt = select(Message).where(
        Message.user_id == user_id, Message.toxicity_flag == True  # noqa: E712
    )
    result = await session.execute(stmt)
    return len(list(result.scalars().all()))
