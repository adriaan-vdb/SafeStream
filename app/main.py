"""SafeStream FastAPI main application.

TODO(stage-2): Implement WebSocket route /ws/{username} with in-memory socket storage
TODO(stage-5): Add config loading from environment variables (APP_PORT, TOXIC_THRESHOLD, etc.)
TODO(stage-3): Integrate moderation pipeline from app.moderation
TODO(stage-4): Add gift simulation and POST /api/gift endpoint
"""

from fastapi import FastAPI

app = FastAPI(
    title="SafeStream",
    description="A Real-Time Moderated Live-Chat Simulator",
    version="0.1.0",
)


@app.get("/")
async def root():
    """Root endpoint returning basic status."""
    return {"status": "ok"}


@app.get("/healthz")
async def health():
    """Health check endpoint returning 200."""
    return {"status": "healthy"}


# TODO(stage-2): Add WebSocket route /ws/{username} - see README Step 2
# TODO(stage-4): Add POST /api/gift endpoint - see README Step 4
# TODO(stage-5): Add logging middleware for JSONL output - see README Step 5
# TODO(stage-3): Add moderation integration - see README Step 3
