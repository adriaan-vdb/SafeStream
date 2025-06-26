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
    gift_id: int = Field(..., description="Unique gift identifier")
    amount: int = Field(..., description="Quantity of gifts sent")


# TODO(stage-5): Add database models for persistence
# TODO(stage-5): Add logging schemas for JSONL output
