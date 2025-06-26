"""Unit tests for SafeStream Pydantic schemas.

Tests serialization and deserialization of all message models
to ensure they match README Section 6 protocols exactly.
"""

import json
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas import ChatMessageIn, ChatMessageOut, GiftEventOut


class TestChatMessageIn:
    """Test incoming chat message schema."""

    def test_valid_chat_message_in(self):
        """Test valid ChatMessageIn creation and serialization."""
        message = ChatMessageIn(message="Hello, world!")

        # Check default type
        assert message.type == "chat"
        assert message.message == "Hello, world!"

        # Test JSON serialization
        json_data = message.model_dump()
        assert json_data == {"type": "chat", "message": "Hello, world!"}

        # Test JSON string serialization
        json_str = message.model_dump_json()
        assert json.loads(json_str) == {"type": "chat", "message": "Hello, world!"}

    def test_chat_message_in_from_dict(self):
        """Test ChatMessageIn creation from dictionary."""
        data = {"type": "chat", "message": "Test message"}
        message = ChatMessageIn(**data)

        assert message.type == "chat"
        assert message.message == "Test message"

    def test_chat_message_in_validation(self):
        """Test ChatMessageIn validation."""
        # Missing required field
        with pytest.raises(ValidationError):
            ChatMessageIn()

        # Invalid type (should fail due to Literal)
        with pytest.raises(ValidationError):
            ChatMessageIn(type="invalid", message="test")


class TestChatMessageOut:
    """Test outgoing chat message schema."""

    def test_valid_chat_message_out(self):
        """Test valid ChatMessageOut creation and serialization."""
        timestamp = datetime(2025, 6, 26, 12, 34, 56)
        message = ChatMessageOut(
            user="alice", message="hello", toxic=False, score=0.02, ts=timestamp
        )

        # Check default type
        assert message.type == "chat"
        assert message.user == "alice"
        assert message.message == "hello"
        assert message.toxic is False
        assert message.score == 0.02
        assert message.ts == timestamp

        # Test JSON serialization
        json_data = message.model_dump()
        assert json_data["type"] == "chat"
        assert json_data["user"] == "alice"
        assert json_data["message"] == "hello"
        assert json_data["toxic"] is False
        assert json_data["score"] == 0.02
        assert "ts" in json_data  # datetime serialization handled by Pydantic

    def test_chat_message_out_from_dict(self):
        """Test ChatMessageOut creation from dictionary."""
        timestamp = datetime(2025, 6, 26, 12, 34, 56)
        data = {
            "type": "chat",
            "user": "bob",
            "message": "test message",
            "toxic": True,
            "score": 0.8,
            "ts": timestamp,
        }
        message = ChatMessageOut(**data)

        assert message.user == "bob"
        assert message.toxic is True
        assert message.score == 0.8

    def test_chat_message_out_validation(self):
        """Test ChatMessageOut validation."""
        timestamp = datetime.now()

        # Missing required fields
        with pytest.raises(ValidationError):
            ChatMessageOut(user="alice", message="test")

        with pytest.raises(ValidationError):
            ChatMessageOut(user="alice", toxic=False, score=0.0, ts=timestamp)


class TestGiftEventOut:
    """Test gift event schema."""

    def test_valid_gift_event_out(self):
        """Test valid GiftEventOut creation and serialization."""
        gift = GiftEventOut(from_user="admin", gift_id=999, amount=1)

        # Check default type
        assert gift.type == "gift"
        assert gift.from_user == "admin"
        assert gift.gift_id == 999
        assert gift.amount == 1

        # Test JSON serialization with alias
        json_data = gift.model_dump(by_alias=True)
        assert json_data == {
            "type": "gift",
            "from": "admin",  # Uses alias
            "gift_id": 999,
            "amount": 1,
        }

        # Test JSON string serialization
        json_str = gift.model_dump_json(by_alias=True)
        assert json.loads(json_str) == {
            "type": "gift",
            "from": "admin",
            "gift_id": 999,
            "amount": 1,
        }

    def test_gift_event_out_from_dict_with_alias(self):
        """Test GiftEventOut creation from dictionary using alias."""
        data = {
            "type": "gift",
            "from": "admin",  # Using alias
            "gift_id": 123,
            "amount": 5,
        }
        gift = GiftEventOut(**data)

        assert gift.from_user == "admin"  # Internal field name
        assert gift.gift_id == 123
        assert gift.amount == 5

    def test_gift_event_out_from_dict_with_field_name(self):
        """Test GiftEventOut creation from dictionary using field name."""
        data = {
            "type": "gift",
            "from_user": "moderator",  # Using field name
            "gift_id": 456,
            "amount": 10,
        }
        gift = GiftEventOut(**data)

        assert gift.from_user == "moderator"
        assert gift.gift_id == 456
        assert gift.amount == 10

    def test_gift_event_out_validation(self):
        """Test GiftEventOut validation."""
        # Missing required fields
        with pytest.raises(ValidationError):
            GiftEventOut(from_user="admin")

        with pytest.raises(ValidationError):
            GiftEventOut(gift_id=999, amount=1)


class TestSchemaProtocolCompliance:
    """Test that schemas match README Section 6 protocols exactly."""

    def test_chat_message_in_protocol(self):
        """Test ChatMessageIn matches README protocol exactly."""
        # README: {"type":"chat","message":"hello"}
        data = {"type": "chat", "message": "hello"}
        message = ChatMessageIn(**data)

        json_data = message.model_dump()
        assert json_data == data

    def test_chat_message_out_protocol(self):
        """Test ChatMessageOut matches README protocol exactly."""
        # README: {"type":"chat","user":"alice","message":"hello","toxic":false,"score":0.02,"ts":"2025-06-26T12:34:56Z"}
        timestamp = datetime(2025, 6, 26, 12, 34, 56)
        message = ChatMessageOut(
            user="alice", message="hello", toxic=False, score=0.02, ts=timestamp
        )

        json_data = message.model_dump()
        assert json_data["type"] == "chat"
        assert json_data["user"] == "alice"
        assert json_data["message"] == "hello"
        assert json_data["toxic"] is False
        assert json_data["score"] == 0.02
        assert "ts" in json_data

    def test_gift_event_out_protocol(self):
        """Test GiftEventOut matches README protocol exactly."""
        # README: {"from":"admin","gift_id":999,"amount":1}
        data = {"from": "admin", "gift_id": 999, "amount": 1}
        gift = GiftEventOut(**data)

        json_data = gift.model_dump(by_alias=True)
        assert json_data["type"] == "gift"  # Default added
        assert json_data["from"] == "admin"
        assert json_data["gift_id"] == 999
        assert json_data["amount"] == 1
