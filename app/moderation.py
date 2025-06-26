"""SafeStream moderation pipeline.

Implements a stub moderation function that always returns non-toxic.
TODO(stage-5): Replace with Detoxify integration for actual toxicity detection.
"""


async def predict(text: str) -> tuple[bool, float]:
    """Predict toxicity of input text.

    Args:
        text: Input text to analyze

    Returns:
        Tuple of (is_toxic: bool, toxicity_score: float)

    TODO(stage-5): Replace stub with Detoxify integration using TOXIC_THRESHOLD (default 0.6)
    """
    # Stub implementation - always returns non-toxic
    # TODO(stage-5): from detoxify import Detoxify
    # TODO(stage-5): Load model at startup and use for predictions
    return False, 0.0
