"""SafeStream FastAPI main application.

TODO(stage-2): Implement WebSocket route /ws/{username} with in-memory socket storage
TODO(stage-5): Add config loading from environment variables
TODO(stage-3): Integrate moderation pipeline
TODO(stage-4): Add gift simulation and API endpoints
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


# TODO(stage-2): Add WebSocket route /ws/{username}
# TODO(stage-4): Add POST /api/gift endpoint
# TODO(stage-5): Add logging middleware
# TODO(stage-3): Add moderation integration
