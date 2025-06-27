"""SafeStream FastAPI main application.

Implements WebSocket chat gateway with real-time moderation and broadcasting.
TODO(stage-7): Add database logging and JWT authentication
"""

import asyncio
import json
import logging
import logging.handlers
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from app import events, moderation, schemas

# In-memory storage for connected WebSocket clients
connected: dict[str, WebSocket] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    # Read GIFT_INTERVAL_SECS from environment or use default
    gift_interval = int(os.getenv("GIFT_INTERVAL_SECS", "15"))
    logging.info(f"Starting gift producer with interval: {gift_interval} seconds")

    # Start gift producer as background task
    app.state.gift_task = await events.create_gift_task(connected)
    logging.info("Started gift producer background task")

    yield

    # Shutdown
    if hasattr(app.state, "gift_task") and app.state.gift_task:
        app.state.gift_task.cancel()
        try:
            await app.state.gift_task
        except asyncio.CancelledError:
            pass  # Expected when task is cancelled
        logging.info("Cancelled gift producer background task")


@asynccontextmanager
async def test_lifespan(app: FastAPI):
    """Test lifespan that does not start background tasks."""
    yield


def create_app(testing: bool = False) -> FastAPI:
    """Create FastAPI application instance.

    Args:
        testing: If True, creates a test app without background tasks
    """
    lifespan_func = test_lifespan if testing else lifespan

    app = FastAPI(
        title="SafeStream",
        description="A Real-Time Moderated Live-Chat Simulator",
        version="0.1.0",
        lifespan=lifespan_func,
    )

    # Mount static files for frontend
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

    # Configure logging
    def setup_logging():
        """Setup rotating JSONL logging for chat messages."""
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        # Create rotating file handler for chat messages
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        log_file = logs_dir / f"chat_{today}.jsonl"

        # Configure JSONL logger
        chat_logger = logging.getLogger("chat")
        chat_logger.setLevel(logging.INFO)

        # Rotating file handler: 10MB max size, keep 10 backup files
        handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=10
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
        chat_logger.addHandler(handler)

        return chat_logger

    chat_logger = setup_logging()

    @app.get("/")
    async def root():
        """Root endpoint returning basic status."""
        return {"status": "ok"}

    @app.get("/healthz")
    async def health():
        """Health check endpoint returning 200."""
        return {"status": "healthy"}

    @app.get("/chat", include_in_schema=False)
    async def chat_page():
        """Serve the main chat page."""
        return Response(
            Path("frontend/index.html").read_text(encoding="utf-8"),
            media_type="text/html",
        )

    @app.websocket("/ws/{username}")
    async def websocket_endpoint(websocket: WebSocket, username: str):
        """WebSocket endpoint for real-time chat with moderation.

        Handles:
        - Connection management (accept, store, cleanup)
        - Message parsing and validation
        - Moderation pipeline integration
        - Broadcasting to all connected clients
        - JSONL logging of all messages
        """
        await websocket.accept()
        connected[username] = websocket

        try:
            while True:
                # Receive and parse message
                data = await websocket.receive_text()
                message_data = json.loads(data)

                # Validate incoming message
                chat_message = schemas.ChatMessageIn(**message_data)

                # Run moderation
                toxic, score = await moderation.predict(chat_message.message)

                # Build outgoing message with moderation results
                outgoing_message = schemas.ChatMessageOut(
                    user=username,
                    message=chat_message.message,
                    toxic=toxic,
                    score=score,
                    ts=datetime.now(UTC),
                )

                # Log message to JSONL
                chat_logger.info(outgoing_message.model_dump_json())

                # Broadcast to all connected clients
                message_json = outgoing_message.model_dump_json()
                for client_username, client_websocket in connected.items():
                    try:
                        await client_websocket.send_text(message_json)
                    except Exception:
                        # Remove disconnected clients
                        del connected[client_username]

        except WebSocketDisconnect:
            # Clean up on disconnect
            if username in connected:
                del connected[username]
        except Exception as e:
            # Log errors and clean up
            logging.error(f"WebSocket error for {username}: {e}")
            if username in connected:
                del connected[username]

    @app.post("/api/gift")
    async def gift_endpoint(gift_data: dict):
        """Gift API endpoint for triggering gift events.

        Accepts: {"from": str, "gift_id": int, "amount": int}
        Broadcasts: GiftEventOut to all connected WebSocket clients
        Returns: HTTP 202 with {"status": "queued"}
        """
        try:
            # Validate gift data
            gift_event = schemas.GiftEventOut(**gift_data)

            # Add timestamp to outgoing message
            gift_event_dict = gift_event.model_dump(by_alias=True)
            gift_event_dict["ts"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")

            # Log gift event to JSONL
            chat_logger.info(json.dumps(gift_event_dict))

            # Broadcast to all connected WebSocket clients using events module
            await events.broadcast_gift(connected, gift_event_dict)

            return {"status": "queued"}

        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid gift data: {str(e)}"
            ) from e

    return app


# Create the main app instance for production
app = create_app(testing=False)


# TODO(stage-7): Add database logging and JWT authentication - see README Step 7
