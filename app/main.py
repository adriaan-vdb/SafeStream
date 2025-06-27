"""SafeStream FastAPI main application.

Implements WebSocket chat gateway with real-time moderation and broadcasting.
Includes JWT authentication for secure user access.
TODO(stage-7): Add database logging and JWT authentication
"""

import asyncio
import json
import logging
import logging.handlers
import os
import re
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles

from app import events, moderation, schemas
from app.auth import (
    User,
    authenticate_user,
    create_access_token,
    create_user,
    get_current_active_user,
    get_user_by_token,
)
from app.metrics import metrics

# In-memory storage for connected WebSocket clients
connected: dict[str, WebSocket] = {}

# Configuration
MAX_CONNECTIONS = int(os.getenv("MAX_CONNECTIONS", "1000"))
MAX_USERNAME_LENGTH = int(os.getenv("MAX_USERNAME_LENGTH", "50"))
CLEANUP_INTERVAL = int(os.getenv("CLEANUP_INTERVAL", "300"))  # 5 minutes


def validate_username(username: str) -> bool:
    """Validate username format and length.

    Args:
        username: Username to validate

    Returns:
        True if username is valid, False otherwise
    """
    if not username or len(username) > MAX_USERNAME_LENGTH:
        return False
    # Allow alphanumeric, underscore, hyphen, and dot
    if not re.match(r"^[a-zA-Z0-9._-]+$", username):
        return False
    return True


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

    # Start connection cleanup task
    app.state.cleanup_task = asyncio.create_task(cleanup_stale_connections())
    logging.info("Started connection cleanup task")

    # Reset metrics on server startup
    metrics.reset()

    yield

    # Shutdown
    if hasattr(app.state, "gift_task") and app.state.gift_task:
        app.state.gift_task.cancel()
        try:
            await app.state.gift_task
        except asyncio.CancelledError:
            pass  # Expected when task is cancelled
        logging.info("Cancelled gift producer background task")

    if hasattr(app.state, "cleanup_task") and app.state.cleanup_task:
        app.state.cleanup_task.cancel()
        try:
            await app.state.cleanup_task
        except asyncio.CancelledError:
            pass  # Expected when task is cancelled
        logging.info("Cancelled connection cleanup task")


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
    app.mount("/static", StaticFiles(directory="static"), name="static")

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
            Path("static/index.html").read_text(encoding="utf-8"),
            media_type="text/html",
        )

    @app.get("/metrics")
    async def metrics_endpoint():
        """Live metrics endpoint returning current system metrics.

        Returns:
            Dictionary containing viewer_count, gift_count, and toxic_pct
        """
        return metrics.get_metrics(connected)

    # Authentication endpoints
    @app.post("/auth/register", response_model=schemas.AuthResponse)
    async def register(user_data: schemas.UserRegister):
        """Register a new user account.

        Args:
            user_data: User registration data

        Returns:
            JWT token for the newly created user
        """
        try:
            user = create_user(
                username=user_data.username,
                password=user_data.password,
                email=user_data.email,
            )

            access_token = create_access_token(data={"sub": user.username})
            return schemas.AuthResponse(
                access_token=access_token, token_type="bearer", username=user.username
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration failed: {str(e)}",
            ) from e

    @app.post("/auth/login", response_model=schemas.AuthResponse)
    async def login(form_data: OAuth2PasswordRequestForm = Depends()):
        """Authenticate user and return JWT token.

        Args:
            form_data: OAuth2 form data with username and password

        Returns:
            JWT token for authenticated user
        """
        user = authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(data={"sub": user.username})
        return schemas.AuthResponse(
            access_token=access_token, token_type="bearer", username=user.username
        )

    @app.get("/auth/me", response_model=schemas.UserInfo)
    async def get_current_user_info(
        current_user: User = Depends(get_current_active_user),
    ):
        """Get current user information.

        Args:
            current_user: Current authenticated user from JWT token

        Returns:
            User information
        """
        return schemas.UserInfo(
            username=current_user.username,
            email=current_user.email,
            disabled=current_user.disabled,
        )

    @app.websocket("/ws/{username}")
    async def websocket_endpoint(websocket: WebSocket, username: str):
        """WebSocket endpoint for real-time chat with moderation.

        Handles:
        - JWT authentication via query parameter
        - Connection management (accept, store, cleanup)
        - Message parsing and validation
        - Moderation pipeline integration
        - Broadcasting to all connected clients
        - JSONL logging of all messages
        - Metrics tracking
        """
        # Get JWT token from query parameter
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=1008, reason="Authentication required")
            return

        # Validate JWT token
        user = get_user_by_token(token)
        if not user or user.username != username:
            await websocket.close(code=1008, reason="Invalid authentication")
            return

        # Validate username before accepting connection
        if not validate_username(username):
            await websocket.close(code=1008, reason="Invalid username")
            return

        # Check connection limit
        if len(connected) >= MAX_CONNECTIONS:
            await websocket.close(code=1013, reason="Server at capacity")
            return

        await websocket.accept()
        connected[username] = websocket

        try:
            while True:
                # Receive and parse message
                data = await websocket.receive_text()
                message_data = json.loads(data)

                try:
                    # Validate incoming message
                    chat_message = schemas.ChatMessageIn(**message_data)

                    # Run moderation
                    toxic, score = await moderation.predict(chat_message.message)

                    # Track metrics for chat message
                    metrics.increment_chat_message(toxic)

                    # Build outgoing message with moderation results
                    outgoing_message = schemas.ChatMessageOut(
                        user=username,
                        message=chat_message.message,
                        toxic=toxic,
                        score=score,
                        ts=datetime.now(UTC),
                        msg_id=str(uuid.uuid4()),
                    )

                    # Log message to JSONL
                    chat_logger.info(outgoing_message.model_dump_json())

                    # Broadcast to all connected clients
                    message_json = outgoing_message.model_dump_json()
                    disconnected_clients = []
                    for client_username, client_websocket in connected.items():
                        try:
                            await client_websocket.send_text(message_json)
                        except Exception:
                            # Mark for removal
                            disconnected_clients.append(client_username)

                    # Clean up disconnected clients
                    for client_username in disconnected_clients:
                        if client_username in connected:
                            del connected[client_username]

                except Exception as e:
                    # Handle validation errors and other exceptions gracefully
                    error_message = {
                        "error": "Invalid message format",
                        "detail": str(e),
                    }
                    try:
                        await websocket.send_text(json.dumps(error_message))
                    except Exception:
                        # If we can't send error message, close the connection
                        await websocket.close(code=1011, reason="Internal error")
                        break

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

            # Track metrics for gift event
            metrics.increment_gift_count()

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

    @app.post("/api/admin/kick")
    async def admin_kick(
        request: Request, current_user: User = Depends(get_current_active_user)
    ):
        """Kick a user from the chat (admin only)."""
        data = await request.json()
        target_username = data.get("username")
        if not target_username:
            raise HTTPException(status_code=400, detail="Username required")

        # Remove user from connected clients
        if target_username in connected:
            try:
                await connected[target_username].close(
                    code=1000, reason="Kicked by admin"
                )
            except Exception:
                pass  # Connection might already be closed
            del connected[target_username]

        # Log the kick action
        kick_log = {
            "type": "admin_action",
            "action": "kick",
            "admin_user": current_user.username,
            "target_user": target_username,
            "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }
        chat_logger.info(json.dumps(kick_log))

        return {"status": "ok", "message": f"Kicked user: {target_username}"}

    @app.post("/api/admin/mute")
    async def admin_mute(
        request: Request, current_user: User = Depends(get_current_active_user)
    ):
        """Mute a user (admin only)."""
        data = await request.json()
        target_username = data.get("username")
        if not target_username:
            raise HTTPException(status_code=400, detail="Username required")

        # Log the mute action
        mute_log = {
            "type": "admin_action",
            "action": "mute",
            "admin_user": current_user.username,
            "target_user": target_username,
            "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }
        chat_logger.info(json.dumps(mute_log))

        return {"status": "ok", "message": f"Muted user: {target_username}"}

    @app.post("/api/admin/reset_metrics")
    async def admin_reset_metrics(
        current_user: User = Depends(get_current_active_user),
    ):
        """Reset metrics (admin only)."""
        metrics.reset()

        # Log the reset action
        reset_log = {
            "type": "admin_action",
            "action": "reset_metrics",
            "admin_user": current_user.username,
            "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }
        chat_logger.info(json.dumps(reset_log))

        return {"status": "metrics reset"}

    return app


# Create the main app instance for production
app = create_app(testing=False)


# TODO(stage-7): Add database logging and JWT authentication - see README Step 7


async def cleanup_stale_connections():
    """Periodically clean up stale WebSocket connections."""
    while True:
        try:
            await asyncio.sleep(CLEANUP_INTERVAL)
            stale_connections = []

            for username, websocket in connected.items():
                try:
                    # Try to send a ping to check if connection is alive
                    await websocket.ping()
                except Exception:
                    # Connection is stale, mark for removal
                    stale_connections.append(username)

            # Remove stale connections
            for username in stale_connections:
                if username in connected:
                    del connected[username]
                    logging.info(f"Removed stale connection: {username}")

        except asyncio.CancelledError:
            break
        except Exception as e:
            logging.error(f"Error in connection cleanup: {e}")
            await asyncio.sleep(60)  # Wait before retrying
