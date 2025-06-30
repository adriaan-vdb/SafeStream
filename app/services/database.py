"""SafeStream database service layer.

Provides async database operations using SQLAlchemy 2.0 ORM patterns.
This service layer encapsulates all database interactions for users, messages,
gifts, and admin actions with proper type safety and async patterns.
"""

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AdminAction, GiftEvent, Message, Setting, User, UserSession

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


async def delete_user(session: AsyncSession, user_id: int) -> bool:
    """Delete a user and all associated data.

    Args:
        session: Async SQLAlchemy session
        user_id: ID of the user to delete

    Returns:
        True if user was deleted, False if user not found

    Note:
        This cascades to delete all associated messages, gifts, sessions, and admin actions
        due to the cascade settings in the User model relationships.
    """
    user = await session.get(User, user_id)
    if not user:
        return False

    await session.delete(user)
    await session.commit()
    return True


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


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================


async def create_user_session(
    session: AsyncSession,
    user_id: int,
    session_duration_hours: int = 24,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> UserSession:
    """Create a new user session.

    Args:
        session: Async SQLAlchemy session
        user_id: ID of the user
        session_duration_hours: How long the session should last in hours
        user_agent: User agent string from request headers
        ip_address: IP address of the client

    Returns:
        Created UserSession instance
    """
    # Generate secure session token
    session_token = secrets.token_urlsafe(32)

    # Calculate expiry time
    expires_at = datetime.now(UTC) + timedelta(hours=session_duration_hours)

    user_session = UserSession(
        user_id=user_id,
        session_token=session_token,
        is_active=True,
        user_agent=user_agent,
        ip_address=ip_address,
        expires_at=expires_at,
    )

    session.add(user_session)
    await session.commit()
    await session.refresh(user_session)
    return user_session


async def get_active_session_by_user(
    session: AsyncSession, user_id: int
) -> UserSession | None:
    """Get active session for a user.

    Args:
        session: Async SQLAlchemy session
        user_id: ID of the user

    Returns:
        Active UserSession if found, None otherwise
    """
    stmt = select(UserSession).where(
        UserSession.user_id == user_id,
        UserSession.is_active == True,  # noqa: E712
        UserSession.expires_at > datetime.now(UTC),
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_session_by_token(
    session: AsyncSession, session_token: str
) -> UserSession | None:
    """Get session by token.

    Args:
        session: Async SQLAlchemy session
        session_token: Session token to look up

    Returns:
        UserSession if found and valid, None otherwise
    """
    stmt = select(UserSession).where(
        UserSession.session_token == session_token,
        UserSession.is_active == True,  # noqa: E712
        UserSession.expires_at > datetime.now(UTC),
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def invalidate_user_session(
    session: AsyncSession, user_id: int, session_token: str | None = None
) -> bool:
    """Invalidate user session(s).

    Args:
        session: Async SQLAlchemy session
        user_id: ID of the user
        session_token: Specific session token to invalidate (optional)
                      If None, invalidates all sessions for the user

    Returns:
        True if session(s) were invalidated, False otherwise
    """
    if session_token:
        # Invalidate specific session
        stmt = select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.session_token == session_token,
            UserSession.is_active == True,  # noqa: E712
        )
    else:
        # Invalidate all active sessions for user
        stmt = select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.is_active == True,  # noqa: E712
        )

    result = await session.execute(stmt)
    sessions_to_invalidate = result.scalars().all()

    if not sessions_to_invalidate:
        return False

    # Mark sessions as inactive
    for user_session in sessions_to_invalidate:
        user_session.is_active = False

    await session.commit()
    return True


async def update_session_activity(session: AsyncSession, session_token: str) -> bool:
    """Update session last activity timestamp.

    Args:
        session: Async SQLAlchemy session
        session_token: Session token to update

    Returns:
        True if session was updated, False if not found
    """
    stmt = select(UserSession).where(
        UserSession.session_token == session_token,
        UserSession.is_active == True,  # noqa: E712
    )
    result = await session.execute(stmt)
    user_session = result.scalar_one_or_none()

    if not user_session:
        return False

    user_session.last_activity = datetime.now(UTC)
    await session.commit()
    return True


async def cleanup_expired_sessions(session: AsyncSession) -> int:
    """Clean up expired sessions.

    Args:
        session: Async SQLAlchemy session

    Returns:
        Number of sessions cleaned up
    """
    # Get expired active sessions
    stmt = select(UserSession).where(
        UserSession.is_active == True,  # noqa: E712
        UserSession.expires_at <= datetime.now(UTC),
    )
    result = await session.execute(stmt)
    expired_sessions = result.scalars().all()

    if not expired_sessions:
        return 0

    # Mark as inactive
    for user_session in expired_sessions:
        user_session.is_active = False

    await session.commit()
    return len(expired_sessions)


# ============================================================================
# SETTINGS OPERATIONS
# ============================================================================


async def get_setting(
    session: AsyncSession, key: str, default: str | None = None
) -> str | None:
    """Get a setting value by key.

    Args:
        session: Async SQLAlchemy session
        key: Setting key to retrieve
        default: Default value if setting not found

    Returns:
        Setting value if found, default otherwise
    """
    stmt = select(Setting).where(Setting.key == key)
    result = await session.execute(stmt)
    setting = result.scalar_one_or_none()
    return setting.value if setting else default


async def set_setting(session: AsyncSession, key: str, value: str) -> Setting:
    """Set a setting value by key.

    Args:
        session: Async SQLAlchemy session
        key: Setting key to set
        value: Setting value to set

    Returns:
        Created or updated Setting instance
    """
    # Try to get existing setting
    stmt = select(Setting).where(Setting.key == key)
    result = await session.execute(stmt)
    setting = result.scalar_one_or_none()

    if setting:
        # Update existing setting
        setting.value = value
    else:
        # Create new setting
        setting = Setting(key=key, value=value)
        session.add(setting)

    await session.commit()
    await session.refresh(setting)
    return setting


async def get_toxicity_threshold(session: AsyncSession) -> float:
    """Get the current toxicity threshold from settings.

    Args:
        session: Async SQLAlchemy session

    Returns:
        Toxicity threshold (0.0-1.0), defaults to 0.6 if not set
    """
    threshold_str = await get_setting(session, "toxicity_threshold", "0.6")
    try:
        return float(threshold_str)
    except (ValueError, TypeError):
        return 0.6  # Default fallback


async def set_toxicity_threshold(session: AsyncSession, threshold: float) -> Setting:
    """Set the toxicity threshold in settings.

    Args:
        session: Async SQLAlchemy session
        threshold: Toxicity threshold (0.0-1.0)

    Returns:
        Updated Setting instance

    Raises:
        ValueError: If threshold is not between 0.0 and 1.0
    """
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("Toxicity threshold must be between 0.0 and 1.0")

    return await set_setting(session, "toxicity_threshold", str(threshold))


# ============================================================================
# MUTE OPERATIONS
# ============================================================================


async def set_user_mute(
    session: AsyncSession, user_id: int, mute_until: datetime
) -> bool:
    """Set a user's mute status until a specific time.

    Args:
        session: Async SQLAlchemy session
        user_id: ID of the user to mute
        mute_until: Datetime when the mute expires

    Returns:
        True if mute was set, False if user not found
    """
    mute_key = f"user_mute_{user_id}"
    mute_value = mute_until.isoformat()

    await set_setting(session, mute_key, mute_value)
    return True


async def get_user_mute(session: AsyncSession, user_id: int) -> datetime | None:
    """Get a user's mute expiration time.

    Args:
        session: Async SQLAlchemy session
        user_id: ID of the user to check

    Returns:
        Datetime when mute expires, or None if not muted
    """
    mute_key = f"user_mute_{user_id}"
    mute_value = await get_setting(session, mute_key)

    if not mute_value:
        return None

    try:
        return datetime.fromisoformat(mute_value)
    except ValueError:
        # Invalid datetime format, remove the setting
        await set_setting(session, mute_key, "")
        return None


async def is_user_muted(session: AsyncSession, user_id: int) -> bool:
    """Check if a user is currently muted.

    Args:
        session: Async SQLAlchemy session
        user_id: ID of the user to check

    Returns:
        True if user is currently muted, False otherwise
    """
    mute_until = await get_user_mute(session, user_id)
    if not mute_until:
        return False

    now = datetime.now(UTC)
    is_muted = now < mute_until.replace(tzinfo=UTC)

    # Clean up expired mutes
    if not is_muted:
        mute_key = f"user_mute_{user_id}"
        await set_setting(session, mute_key, "")

    return is_muted


async def clear_user_mute(session: AsyncSession, user_id: int) -> bool:
    """Clear a user's mute status.

    Args:
        session: Async SQLAlchemy session
        user_id: ID of the user to unmute

    Returns:
        True if mute was cleared, False if user was not muted
    """
    mute_key = f"user_mute_{user_id}"
    current_mute = await get_setting(session, mute_key)

    if not current_mute:
        return False

    await set_setting(session, mute_key, "")
    return True
