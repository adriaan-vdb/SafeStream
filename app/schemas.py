"""SafeStream Pydantic data models and schemas.

Implements the exact JSON protocols specified in README Section 6.
All models are JSON-serialisable with primitive types only.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageIn(BaseModel):
    """Schema for incoming chat messages via WebSocket.

    Matches README API protocol: {"type":"chat","message":"hello"}
    """

    type: Literal["chat"] = Field(default="chat", description="Message type")
    message: str = Field(..., description="Chat message content")


class ChatMessageOut(BaseModel):
    """Schema for outgoing chat messages via WebSocket.

    Matches README API protocol: {"type":"chat","user":"alice","message":"hello","toxic":false,"score":0.02,"ts":"2025-06-26T12:34:56Z"}
    """

    type: Literal["chat"] = Field(default="chat", description="Message type")
    id: int = Field(..., description="Unique message ID from database")
    user: str = Field(..., description="Username of message sender")
    message: str = Field(..., description="Chat message content")
    toxic: bool = Field(..., description="Whether message was flagged as toxic")
    score: float = Field(..., description="Toxicity score from moderation")
    ts: datetime = Field(..., description="Timestamp of message")


class GiftEventOut(BaseModel):
    """Schema for gift events broadcast to all clients.

    Matches README API protocol: {"from":"admin","gift_id":999,"amount":1}
    Note: README shows 'from' but we use 'from_user' for Python compatibility.
    """

    model_config = ConfigDict(validate_by_name=True)

    type: Literal["gift"] = Field(default="gift", description="Event type")
    from_user: str = Field(..., alias="from", description="Username sending the gift")
    gift_id: int = Field(..., description="Unique gift identifier", ge=0)
    amount: int = Field(..., description="Quantity of gifts sent", ge=1)


# Authentication schemas
class UserLogin(BaseModel):
    """Schema for user login requests."""

    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class UserRegister(BaseModel):
    """Schema for user registration requests."""

    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")
    email: str | None = Field(None, description="Email address")


class AuthResponse(BaseModel):
    """Schema for authentication responses."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    username: str = Field(..., description="Authenticated username")


class UserInfo(BaseModel):
    """Schema for user information."""

    username: str = Field(..., description="Username")
    email: str | None = Field(None, description="Email address")
    disabled: bool = Field(default=False, description="Whether user is disabled")


# TODO(stage-6): Add database models for persistence
# Database logging schemas implemented in db/models.py
