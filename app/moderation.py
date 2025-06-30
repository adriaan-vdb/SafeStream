"""SafeStream moderation pipeline.

Implements toxicity detection using Detoxify (HuggingFace model).

- First-time model download: ~60MB
- First inference may be slow (model load); subsequent calls ~10ms on CPU
- Memory: ~200MB RAM
- Set DISABLE_DETOXIFY=1 to use stub (always non-toxic, 0.0)
- Call warmup() during app startup to pre-load model and eliminate cold start delay
- Toxicity threshold now controlled by database setting via dashboard
"""

import os
from functools import lru_cache


@lru_cache
def _get_model():
    """Lazy load Detoxify model to prevent loading unless required."""
    try:
        from detoxify import Detoxify

        return Detoxify("original-small")
    except ImportError:
        print("Detoxify not available, using stub moderation.")
        return None


async def warmup():
    """Pre-load the model during startup to eliminate cold start delay.

    Call this during application startup to ensure the first message
    doesn't experience the model loading delay.
    """
    if os.getenv("DISABLE_DETOXIFY", "0") == "1":
        print("Detoxify disabled, skipping model warmup")
        return

    try:
        print("Warming up Detoxify model...")
        model = _get_model()
        if model is not None:
            # Run a quick prediction to fully initialize the model
            _ = model.predict("warmup message")
            print("✓ Detoxify model warmed up successfully")
        else:
            print("Detoxify model not available, using stub mode")
    except Exception as e:
        print(f"Warning: Model warmup failed: {e}")
        print("Falling back to lazy loading")


async def predict(text: str, threshold: float | None = None) -> tuple[bool, float]:
    """Predict toxicity of input text with configurable threshold.

    Args:
        text: Input text to analyze
        threshold: Toxicity threshold (0.0-1.0). If None, uses TOXIC_THRESHOLD env var.
                  This allows for unified control from the database/dashboard.

    Returns:
        Tuple of (is_toxic: bool, toxicity_score: float)

    Environment Variables:
        DISABLE_DETOXIFY: Set to "1" to use stub mode (default: "0")
        TOXIC_THRESHOLD: Fallback threshold if none provided (default: 0.6)
    """
    if os.getenv("DISABLE_DETOXIFY", "0") == "1":
        return False, 0.0

    model = _get_model()
    if model is None:
        return False, 0.0

    score = float(model.predict(text)["toxicity"])

    # Use provided threshold or fall back to environment variable
    effective_threshold = (
        threshold if threshold is not None else float(os.getenv("TOXIC_THRESHOLD", 0.6))
    )
    is_toxic = score >= effective_threshold

    return is_toxic, score
