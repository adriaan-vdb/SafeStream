"""SafeStream moderation pipeline.

Implements toxicity detection using Detoxify (HuggingFace model).

- First-time model download: ~60MB
- First inference may be slow (model load); subsequent calls ~10ms on CPU
- Memory: ~200MB RAM
- Set DISABLE_DETOXIFY=1 to use stub (always non-toxic, 0.0)
- Set TOXIC_THRESHOLD (default 0.6) to adjust sensitivity
"""

import os
from functools import lru_cache


@lru_cache
def _get_model():
    """Lazy load Detoxify model to prevent loading unless required."""
    from detoxify import Detoxify

    return Detoxify("original-small")


async def predict(text: str) -> tuple[bool, float]:
    """Predict toxicity of input text.

    Args:
        text: Input text to analyze

    Returns:
        Tuple of (is_toxic: bool, toxicity_score: float)

    Environment Variables:
        DISABLE_DETOXIFY: Set to "1" to use stub mode (default: "0")
        TOXIC_THRESHOLD: Threshold for toxic classification (default: 0.6)
    """
    if os.getenv("DISABLE_DETOXIFY", "0") == "1":
        return False, 0.0

    score = float(_get_model().predict(text)["toxicity"])
    is_toxic = score >= float(os.getenv("TOXIC_THRESHOLD", 0.6))
    return is_toxic, score
