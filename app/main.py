"""SafeStream FastAPI main application.

Implements WebSocket chat gateway with real-time moderation and broadcasting.
Includes JWT authentication and database-backed persistence.
"""

import asyncio
import json
import logging
import logging.handlers
import os
import re
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
from app.db import async_session, init_db
from app.metrics import metrics
from app.services import database as db_service

# In-memory storage for connected WebSocket clients
connected: set[WebSocket] = set()
# Keep track of username mappings for admin actions
websocket_usernames: dict[WebSocket, str] = {}

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
    # Initialize database
    await init_db()
    logging.info("Database initialized successfully")

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
    """Test lifespan that initializes database but does not start background tasks."""
    # Initialize database for testing
    await init_db()
    logging.info("Database initialized for testing")

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

    @app.get("/")
    async def root():
        """Root endpoint redirecting to login page."""
        return Response(
            """
            <html>
            <head><title>SafeStream</title></head>
            <body>
                <script>window.location.href = '/login';</script>
                <p>Redirecting to SafeStream...</p>
            </body>
            </html>
            """,
            media_type="text/html",
        )

    @app.get("/healthz")
    async def health():
        """Health check endpoint returning 200."""
        return {"status": "healthy"}

    @app.get("/chat", include_in_schema=False)
    async def chat_page():
        """Serve the main chat page (legacy - redirects to login)."""
        return Response(
            """
            <html>
            <head><title>SafeStream - Redirecting</title></head>
            <body>
                <script>window.location.href = '/login';</script>
                <p>Redirecting to login page...</p>
            </body>
            </html>
            """,
            media_type="text/html",
        )

    @app.get("/login", include_in_schema=False)
    async def login_page():
        """Serve the login page."""
        return Response(
            Path("static/login.html").read_text(encoding="utf-8"),
            media_type="text/html",
        )

    @app.get("/app", include_in_schema=False)
    async def app_page():
        """Serve the main application page."""
        return Response(
            Path("static/app.html").read_text(encoding="utf-8"),
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
            user = await create_user(
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
    async def login(
        request: Request,
        form_data: OAuth2PasswordRequestForm = Depends(),
    ):
        """Authenticate user and return JWT token with session management.

        Args:
            form_data: OAuth2 form data with username and password
            request: HTTP request for extracting user agent and IP

        Returns:
            JWT token for authenticated user

        Raises:
            HTTPException: If credentials invalid or user already logged in
        """
        user = await authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user already has an active session
        async with async_session() as session:
            # Get the actual database user model (with id field)
            db_user = await db_service.get_user_by_username(session, user.username)
            if not db_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="User not found in database",
                )

            existing_session = await db_service.get_active_session_by_user(
                session, db_user.id
            )
            if existing_session:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User is already logged in from another session. Please logout from other devices first.",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Create new session
            user_agent = request.headers.get("user-agent")
            ip_address = (
                getattr(request.client, "host", None) if request.client else None
            )

            user_session = await db_service.create_user_session(
                session,
                user_id=db_user.id,
                session_duration_hours=24,  # 24 hour session
                user_agent=user_agent,
                ip_address=ip_address,
            )

        # Create JWT token with session info
        access_token = create_access_token(
            data={"sub": user.username, "session_token": user_session.session_token}
        )

        logging.info(f"User {user.username} logged in successfully from {ip_address}")

        return schemas.AuthResponse(
            access_token=access_token, token_type="bearer", username=user.username
        )

    @app.post("/auth/logout")
    async def logout(current_user: User = Depends(get_current_active_user)):
        """Logout user and invalidate their session.

        Args:
            current_user: Current authenticated user from JWT token

        Returns:
            Success message
        """
        async with async_session() as session:
            # Get the actual database user model (with id field)
            db_user = await db_service.get_user_by_username(
                session, current_user.username
            )
            if not db_user:
                return {"message": "User not found in database"}

            # Invalidate all sessions for the user (for now - could be more specific with session token)
            success = await db_service.invalidate_user_session(session, db_user.id)

        if success:
            logging.info(f"User {current_user.username} logged out successfully")
            return {"message": "Successfully logged out"}
        else:
            return {"message": "No active session found"}

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
        - Database logging of all messages and events
        - Metrics tracking
        """
        # Get JWT token from query parameter
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=1008, reason="Authentication required")
            return

        # Validate JWT token
        user = await get_user_by_token(token)
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
        connected.add(websocket)
        websocket_usernames[websocket] = username
        logging.info(f"User {username} connected. Total connections: {len(connected)}")

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

                    # Save message to database first to get the ID
                    async with async_session() as session:
                        # Get or create user for database
                        db_user = await db_service.get_user_by_username(
                            session, username
                        )
                        if not db_user:
                            # Create user with temporary password (they'll need to register properly)
                            db_user = await db_service.create_user(
                                session, username, None, "temp_websocket_user"
                            )

                        # Save message to database
                        saved_message = await db_service.save_message(
                            session,
                            db_user.id,
                            chat_message.message,
                            toxic,
                            score,
                            "chat",
                        )

                    # Build outgoing message with moderation results and database ID
                    outgoing_message = schemas.ChatMessageOut(
                        id=saved_message.id,
                        user=username,
                        message=chat_message.message,
                        toxic=toxic,
                        score=score,
                        ts=saved_message.timestamp,
                    )

                    # Broadcast to all connected clients
                    message_json = outgoing_message.model_dump_json()
                    disconnected_clients = []
                    broadcast_count = 0

                    for (
                        client_websocket
                    ) in (
                        connected.copy()
                    ):  # Use copy to avoid modification during iteration
                        try:
                            await client_websocket.send_text(message_json)
                            broadcast_count += 1
                        except Exception:
                            # Mark for removal
                            disconnected_clients.append(client_websocket)

                    # Log broadcast success
                    logging.info(
                        f"Message from {username} broadcast to {broadcast_count} clients"
                    )

                    # Clean up disconnected clients
                    for client_websocket in disconnected_clients:
                        connected.discard(client_websocket)
                        websocket_usernames.pop(client_websocket, None)

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
            connected.discard(websocket)
            websocket_usernames.pop(websocket, None)

            # Clean up user session when disconnecting
            async with async_session() as db_session:
                db_user = await db_service.get_user_by_username(db_session, username)
                if db_user:
                    await db_service.invalidate_user_session(db_session, db_user.id)
                    logging.info(
                        f"Invalidated session for user {username} on disconnect"
                    )

            logging.info(
                f"User {username} disconnected. Total connections: {len(connected)}"
            )
        except Exception as e:
            # Log errors and clean up
            logging.error(f"WebSocket error for {username}: {e}")
            connected.discard(websocket)
            websocket_usernames.pop(websocket, None)

            # Clean up user session on error
            async with async_session() as db_session:
                db_user = await db_service.get_user_by_username(db_session, username)
                if db_user:
                    await db_service.invalidate_user_session(db_session, db_user.id)
                    logging.info(f"Invalidated session for user {username} on error")

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

            # Save gift event to database
            async with async_session() as session:
                # Get or create user for database
                db_user = await db_service.get_user_by_username(
                    session, gift_event.from_user
                )
                if not db_user:
                    # Create user with temporary password
                    db_user = await db_service.create_user(
                        session, gift_event.from_user, None, "temp_gift_user"
                    )

                # Save gift event to database
                await db_service.save_gift_event(
                    session, db_user.id, str(gift_event.gift_id), gift_event.amount
                )

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

        # Remove all connections for the target user
        kicked_connections = []
        for websocket, ws_username in websocket_usernames.items():
            if ws_username == target_username:
                kicked_connections.append(websocket)

        kick_count = 0
        for websocket in kicked_connections:
            try:
                await websocket.close(code=1000, reason="Kicked by admin")
                kick_count += 1
            except Exception:
                pass  # Connection might already be closed
            connected.discard(websocket)
            websocket_usernames.pop(websocket, None)

        logging.info(
            f"Admin {current_user.username} kicked user {target_username}. Closed {kick_count} connections."
        )

        # Log the kick action to database and invalidate user session
        async with async_session() as session:
            # Get admin user from database
            admin_user = await db_service.get_user_by_username(
                session, current_user.username
            )
            if not admin_user:
                # Create admin user if not exists
                admin_user = await db_service.create_user(
                    session, current_user.username, None, "temp_admin_user"
                )

            # Get target user ID if exists
            target_user = await db_service.get_user_by_username(
                session, target_username
            )
            target_user_id = target_user.id if target_user else None

            # Invalidate target user's session
            if target_user:
                session_invalidated = await db_service.invalidate_user_session(
                    session, target_user.id
                )
                if session_invalidated:
                    logging.info(
                        f"Invalidated session for kicked user {target_username}"
                    )

            # Log admin action
            await db_service.log_admin_action(
                session,
                admin_user.id,
                "kick",
                target_user_id,
                f"Kicked user: {target_username}",
            )

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

        # Log the mute action to database
        async with async_session() as session:
            # Get admin user from database
            admin_user = await db_service.get_user_by_username(
                session, current_user.username
            )
            if not admin_user:
                # Create admin user if not exists
                admin_user = await db_service.create_user(
                    session, current_user.username, None, "temp_admin_user"
                )

            # Get target user ID if exists
            target_user = await db_service.get_user_by_username(
                session, target_username
            )
            target_user_id = target_user.id if target_user else None

            # Log admin action
            await db_service.log_admin_action(
                session,
                admin_user.id,
                "mute",
                target_user_id,
                f"Muted user: {target_username}",
            )

        return {"status": "ok", "message": f"Muted user: {target_username}"}

    @app.post("/api/admin/reset_metrics")
    async def admin_reset_metrics(
        current_user: User = Depends(get_current_active_user),
    ):
        """Reset metrics (admin only)."""
        metrics.reset()

        # Log the reset action to database
        async with async_session() as session:
            # Get admin user from database
            admin_user = await db_service.get_user_by_username(
                session, current_user.username
            )
            if not admin_user:
                # Create admin user if not exists
                admin_user = await db_service.create_user(
                    session, current_user.username, None, "temp_admin_user"
                )

            # Log admin action
            await db_service.log_admin_action(
                session,
                admin_user.id,
                "reset_metrics",
                None,
                "Reset system metrics",
            )

        return {"status": "metrics reset"}

    return app


# Create the main app instance for production
app = create_app(testing=False)


# TODO(stage-7): Add database logging and JWT authentication - see README Step 7


async def cleanup_stale_connections():
    """Periodically clean up stale WebSocket connections and expired sessions."""
    while True:
        try:
            await asyncio.sleep(CLEANUP_INTERVAL)
            stale_connections = []

            for websocket in connected:
                try:
                    # Try to send a ping to check if connection is alive
                    await websocket.ping()
                except Exception:
                    # Connection is stale, mark for removal
                    stale_connections.append(websocket)

            # Remove stale connections
            for websocket in stale_connections:
                connected.discard(websocket)
                username = websocket_usernames.pop(websocket, None)
                logging.info(f"Removed stale connection: {username or 'unknown'}")

            # Clean up expired sessions
            async with async_session() as session:
                expired_count = await db_service.cleanup_expired_sessions(session)
                if expired_count > 0:
                    logging.info(f"Cleaned up {expired_count} expired sessions")

        except asyncio.CancelledError:
            break
        except Exception as e:
            logging.error(f"Error in connection cleanup: {e}")
            await asyncio.sleep(60)  # Wait before retrying
