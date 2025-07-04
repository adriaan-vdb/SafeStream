"""SafeStream database models.

SQLAlchemy ORM models for SafeStream's core entities with proper relationships,
constraints, and indexing for optimal performance.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    """User model for authentication and profile management."""

    __tablename__ = "users"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # User credentials and profile
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Status and metadata
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="user", cascade="all, delete-orphan"
    )
    sent_gifts: Mapped[list["GiftEvent"]] = relationship(
        "GiftEvent", back_populates="from_user", cascade="all, delete-orphan"
    )
    admin_actions: Mapped[list["AdminAction"]] = relationship(
        "AdminAction",
        foreign_keys="AdminAction.admin_user_id",
        back_populates="admin_user",
        cascade="all, delete-orphan",
    )
    targeted_actions: Mapped[list["AdminAction"]] = relationship(
        "AdminAction",
        foreign_keys="AdminAction.target_user_id",
        back_populates="target_user",
    )
    sessions: Mapped[list["UserSession"]] = relationship(
        "UserSession", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<User(id={self.id}, username='{self.username}', active={self.is_active})>"
        )


class Message(Base):
    """Chat message model with toxicity detection and moderation."""

    __tablename__ = "messages"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # User relationship
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )

    # Message content
    message_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Toxicity detection
    toxicity_flag: Mapped[bool] = mapped_column(
        default=False, nullable=False, index=True
    )
    toxicity_score: Mapped[float | None] = mapped_column(nullable=True)

    # Message classification
    message_type: Mapped[str] = mapped_column(
        String(20), default="chat", nullable=False, index=True
    )  # 'chat', 'system', 'admin', etc.

    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(
        default=func.now(), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="messages")

    # Composite indexes for common queries
    __table_args__ = (
        Index("idx_messages_user_timestamp", "user_id", "timestamp"),
        Index("idx_messages_toxicity_timestamp", "toxicity_flag", "timestamp"),
        Index("idx_messages_type_timestamp", "message_type", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, user_id={self.user_id}, type='{self.message_type}', toxic={self.toxicity_flag})>"


class GiftEvent(Base):
    """Gift/donation event model for tracking virtual gifts."""

    __tablename__ = "gift_events"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # User relationship
    from_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )

    # Gift details
    gift_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    amount: Mapped[int] = mapped_column(default=1, nullable=False)

    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(
        default=func.now(), nullable=False, index=True
    )

    # Relationships
    from_user: Mapped["User"] = relationship("User", back_populates="sent_gifts")

    # Composite indexes for analytics
    __table_args__ = (
        Index("idx_gifts_user_timestamp", "from_user_id", "timestamp"),
        Index("idx_gifts_type_timestamp", "gift_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<GiftEvent(id={self.id}, from_user_id={self.from_user_id}, gift_id='{self.gift_id}', amount={self.amount})>"


class AdminAction(Base):
    """Administrative action model for moderation audit trail."""

    __tablename__ = "admin_actions"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Admin user relationship
    admin_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )

    # Action details
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    target_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )

    # Additional context (JSON-serializable data)
    action_details: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(
        default=func.now(), nullable=False, index=True
    )

    # Relationships
    admin_user: Mapped["User"] = relationship(
        "User", foreign_keys=[admin_user_id], back_populates="admin_actions"
    )
    target_user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[target_user_id], back_populates="targeted_actions"
    )

    # Composite indexes for audit queries
    __table_args__ = (
        Index("idx_admin_actions_admin_timestamp", "admin_user_id", "timestamp"),
        Index("idx_admin_actions_target_timestamp", "target_user_id", "timestamp"),
        Index("idx_admin_actions_action_timestamp", "action", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<AdminAction(id={self.id}, admin_user_id={self.admin_user_id}, action='{self.action}', target_user_id={self.target_user_id})>"


class UserSession(Base):
    """User session model for tracking active logins and preventing multiple sessions."""

    __tablename__ = "user_sessions"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # User relationship
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )

    # Session details
    session_token: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)

    # Session metadata
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(
        String(45), nullable=True
    )  # IPv6 compatible

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    last_activity: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now(), nullable=False, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(nullable=False, index=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    # Composite indexes for session management
    __table_args__ = (
        Index("idx_user_sessions_user_active", "user_id", "is_active"),
        Index("idx_user_sessions_token_active", "session_token", "is_active"),
        Index("idx_user_sessions_expires", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"


class Setting(Base):
    """Application settings model for runtime configuration."""

    __tablename__ = "settings"

    # Primary key
    key: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Setting value (stored as text, converted on retrieval)
    value: Mapped[str] = mapped_column(Text, nullable=False)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Setting(key='{self.key}', value='{self.value}')>"
