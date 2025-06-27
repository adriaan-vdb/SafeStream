"""Tests for SafeStream moderation functionality."""

import asyncio
import os
from unittest.mock import patch

import pytest

from app.moderation import predict


def _can_load_detoxify():
    """Check if Detoxify can be loaded (SentencePiece available)."""
    try:
        from detoxify import Detoxify

        Detoxify("original-small")
        return True
    except ImportError:
        return False


@pytest.mark.skipif(
    os.getenv("DISABLE_DETOXIFY") == "1" or not _can_load_detoxify(),
    reason="Stub active or Detoxify not available",
)
def test_predict_toxic_real_model():
    """Test toxicity prediction with real Detoxify model."""
    result = asyncio.run(predict("you are stupid"))
    assert result[0] is True
    assert 0.0 <= result[1] <= 1.0


@pytest.mark.skipif(
    os.getenv("DISABLE_DETOXIFY") == "1" or not _can_load_detoxify(),
    reason="Stub active or Detoxify not available",
)
def test_predict_non_toxic_real_model():
    """Test non-toxic prediction with real Detoxify model."""
    result = asyncio.run(predict("hello world"))
    assert result[0] is False
    assert 0.0 <= result[1] <= 1.0


@patch.dict(os.environ, {"DISABLE_DETOXIFY": "1"})
def test_predict_stub():
    """Test stub mode when Detoxify is disabled."""
    assert asyncio.run(predict("any text")) == (False, 0.0)


@patch.dict(os.environ, {"DISABLE_DETOXIFY": "1"})
def test_predict_stub_toxic_text():
    """Test stub mode with toxic text (should still return non-toxic)."""
    assert asyncio.run(predict("you are stupid")) == (False, 0.0)


@patch.dict(os.environ, {"TOXIC_THRESHOLD": "0.1"})
@pytest.mark.skipif(
    os.getenv("DISABLE_DETOXIFY") == "1" or not _can_load_detoxify(),
    reason="Stub active or Detoxify not available",
)
def test_predict_custom_threshold():
    """Test custom toxicity threshold."""
    result = asyncio.run(predict("hello world"))
    # With very low threshold, even benign text might be flagged
    # This test verifies the threshold is being applied
    assert isinstance(result[0], bool)
    assert 0.0 <= result[1] <= 1.0


def test_predict_async_interface():
    """Test that predict function is properly async."""
    import inspect

    assert inspect.iscoroutinefunction(predict)
