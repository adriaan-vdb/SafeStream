"""Authentication tests for SafeStream.

Tests JWT authentication, user management, and database integration.
"""

import importlib
import os
import time
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.auth import (
    authenticate_user,
    create_access_token,
    create_user,
    get_password_hash,
    get_user,
    get_user_by_token,
    verify_password,
)
from app.main import create_app

# Import database fixtures directly


def get_unique_username(prefix: str = "testuser") -> str:
    """Generate a unique username for testing."""
    import random
    import string

    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}_{suffix}"


class TestPasswordHashing:
    """Test password hashing functionality."""

    def test_password_hashing(self):
        """Test that passwords are properly hashed."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed)

    def test_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes."""
        password1 = "testpassword123"
        password2 = "differentpassword456"

        hash1 = get_password_hash(password1)
        hash2 = get_password_hash(password2)

        assert hash1 != hash2


class TestUserManagementDB:
    """Test database-backed user creation and management."""

    @pytest.mark.asyncio
    async def test_create_user(self, test_session):
        """Test creating a new user in database."""
        username = get_unique_username()
        password = "testpass"
        email = f"{username}@test.com"

        user = await create_user(username, password, email)

        assert user.username == username
        assert user.email == email
        assert user.hashed_password != password
        assert verify_password(password, user.hashed_password)
        assert user.disabled is False

    @pytest.mark.asyncio
    async def test_create_duplicate_user(self, test_session, sample_user):
        """Test that duplicate usernames are rejected."""
        with pytest.raises(Exception) as exc_info:
            await create_user(sample_user.username, "anotherpass")

        assert "already registered" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, test_session):
        """Test successful user authentication."""
        username = get_unique_username()
        password = "testpass123"
        email = f"{username}@test.com"

        await create_user(username, password, email)
        user = await authenticate_user(username, password)

        assert user is not None
        assert user.username == username

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, test_session, sample_user):
        """Test authentication with wrong password."""
        user = await authenticate_user(sample_user.username, "wrongpass")
        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_nonexistent(self, test_session):
        """Test authentication with non-existent user."""
        user = await authenticate_user("nonexistent", "testpass123")
        assert user is None

    @pytest.mark.asyncio
    async def test_get_user(self, test_session, sample_user):
        """Test getting user by username."""
        user = await get_user(sample_user.username)

        assert user is not None
        assert user.username == sample_user.username

    @pytest.mark.asyncio
    async def test_get_user_nonexistent(self, test_session):
        """Test getting non-existent user."""
        user = await get_user("nonexistent")
        assert user is None


class TestJWTTokens:
    """Test JWT token creation and validation."""

    def test_create_access_token(self):
        """Test JWT token creation."""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expiry(self):
        """Test JWT token creation with custom expiry."""
        data = {"sub": "testuser"}
        token = create_access_token(data, expires_delta=timedelta(minutes=5))

        assert token is not None

    @pytest.mark.asyncio
    async def test_get_user_by_token_valid(self, test_session, sample_user):
        """Test getting user from valid JWT token."""
        # Create token
        token = create_access_token({"sub": sample_user.username})

        # Get user from token
        user = await get_user_by_token(token)

        assert user is not None
        assert user.username == sample_user.username

    @pytest.mark.asyncio
    async def test_get_user_by_token_invalid(self, test_session):
        """Test getting user from invalid JWT token."""
        user = await get_user_by_token("invalid-token")
        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_token_expired(self, test_session):
        """Test getting user from expired JWT token."""
        # Create token with very short expiry
        data = {"sub": "testuser"}
        token = create_access_token(data, expires_delta=timedelta(seconds=1))

        # Wait for token to expire
        time.sleep(2)

        user = await get_user_by_token(token)
        assert user is None


class TestEnvironmentConfiguration:
    """Test environment configuration."""

    def test_default_secret_key(self):
        """Test default secret key configuration."""
        # Clear any existing environment variable to test default
        original_secret_key = os.environ.get("JWT_SECRET_KEY")
        if "JWT_SECRET_KEY" in os.environ:
            del os.environ["JWT_SECRET_KEY"]

        try:
            # Re-import to get the default value
            import app.auth

            importlib.reload(app.auth)

            # Test that the default value is used when no environment variable is set
            assert app.auth.SECRET_KEY == "your-secret-key-change-in-production"
        finally:
            # Restore original environment variable
            if original_secret_key is not None:
                os.environ["JWT_SECRET_KEY"] = original_secret_key
            else:
                # Re-import to restore the original state
                import app.auth

                importlib.reload(app.auth)

    def test_custom_secret_key(self):
        """Test custom secret key from environment."""
        original_secret_key = os.environ.get("JWT_SECRET_KEY")
        os.environ["JWT_SECRET_KEY"] = "custom-test-secret-key"

        try:
            import app.auth

            importlib.reload(app.auth)
            assert app.auth.SECRET_KEY == "custom-test-secret-key"
        finally:
            if original_secret_key is not None:
                os.environ["JWT_SECRET_KEY"] = original_secret_key
            else:
                del os.environ["JWT_SECRET_KEY"]

    def test_custom_expire_minutes(self):
        """Test custom token expiry from environment."""
        original_expire_minutes = os.environ.get("JWT_EXPIRE_MINUTES")
        os.environ["JWT_EXPIRE_MINUTES"] = "60"

        try:
            import app.auth

            importlib.reload(app.auth)
            assert app.auth.ACCESS_TOKEN_EXPIRE_MINUTES == 60
        finally:
            if original_expire_minutes is not None:
                os.environ["JWT_EXPIRE_MINUTES"] = original_expire_minutes
            elif "JWT_EXPIRE_MINUTES" in os.environ:
                del os.environ["JWT_EXPIRE_MINUTES"]


class TestAPIIntegration:
    """Test API integration with database authentication."""

    def test_register_endpoint(self):
        """Test user registration endpoint."""
        app = create_app(testing=True)
        username = get_unique_username()

        with TestClient(app) as client:
            response = client.post(
                "/auth/register",
                json={
                    "username": username,
                    "password": "testpass123",
                    "email": f"{username}@test.com",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["username"] == username
            assert "access_token" in data
            assert data["token_type"] == "bearer"

    def test_register_duplicate_username(self):
        """Test registration with duplicate username."""
        app = create_app(testing=True)
        username = get_unique_username()

        with TestClient(app) as client:
            # Register first user
            response1 = client.post(
                "/auth/register",
                json={
                    "username": username,
                    "password": "testpass123",
                    "email": f"{username}@test.com",
                },
            )
            assert response1.status_code == 200

            # Try to register duplicate
            response2 = client.post(
                "/auth/register",
                json={
                    "username": username,
                    "password": "anotherpass",
                    "email": f"{username}2@test.com",
                },
            )
            assert response2.status_code == 400

    def test_login_endpoint(self):
        """Test user login endpoint."""
        app = create_app(testing=True)
        username = get_unique_username()
        password = "testpass123"

        with TestClient(app) as client:
            # Register user first
            client.post(
                "/auth/register",
                json={
                    "username": username,
                    "password": password,
                    "email": f"{username}@test.com",
                },
            )

            # Login
            response = client.post(
                "/auth/login",
                data={"username": username, "password": password},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["username"] == username
            assert "access_token" in data
            assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        app = create_app(testing=True)

        with TestClient(app) as client:
            response = client.post(
                "/auth/login",
                data={"username": "nonexistent", "password": "wrongpass"},
            )

            assert response.status_code == 401

    def test_protected_endpoint_with_token(self):
        """Test accessing protected endpoint with valid token."""
        app = create_app(testing=True)
        username = get_unique_username()

        with TestClient(app) as client:
            # Register and get token
            register_response = client.post(
                "/auth/register",
                json={
                    "username": username,
                    "password": "testpass123",
                    "email": f"{username}@test.com",
                },
            )
            token = register_response.json()["access_token"]

            # Access protected endpoint
            response = client.get(
                "/auth/me", headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["username"] == username

    def test_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token."""
        app = create_app(testing=True)

        with TestClient(app) as client:
            response = client.get("/auth/me")
            assert response.status_code == 401

    def test_admin_endpoints_with_authentication(self):
        """Test admin endpoints with valid authentication."""
        app = create_app(testing=True)
        username = get_unique_username()

        with TestClient(app) as client:
            # Register and get token
            register_response = client.post(
                "/auth/register",
                json={
                    "username": username,
                    "password": "testpass123",
                    "email": f"{username}@test.com",
                },
            )
            token = register_response.json()["access_token"]

            # Test admin endpoints (these should work with any authenticated user for testing)
            headers = {"Authorization": f"Bearer {token}"}

            kick_response = client.post(
                "/api/admin/kick", json={"username": "someuser"}, headers=headers
            )
            assert kick_response.status_code == 200

    def test_admin_endpoints_without_authentication(self):
        """Test admin endpoints without authentication."""
        app = create_app(testing=True)

        with TestClient(app) as client:
            response = client.post("/api/admin/kick", json={"username": "someuser"})
            assert response.status_code == 401


class TestWebSocketAuthentication:
    """Test WebSocket authentication with database."""

    def test_websocket_authentication_flow(self):
        """Test WebSocket authentication flow."""
        app = create_app(testing=True)
        username = get_unique_username()

        with TestClient(app) as client:
            # Register user and get token
            register_response = client.post(
                "/auth/register",
                json={
                    "username": username,
                    "password": "testpass123",
                    "email": f"{username}@test.com",
                },
            )
            assert register_response.status_code == 200
            token = register_response.json()["access_token"]

            # Test WebSocket connection with authentication
            with client.websocket_connect(f"/ws/{username}?token={token}") as websocket:
                # Send a test message
                websocket.send_json({"message": "Hello, world!"})

                # Should receive the message back
                data = websocket.receive_json()
                assert data["user"] == username
                assert data["message"] == "Hello, world!"

    def test_websocket_without_token(self):
        """Test WebSocket connection without token."""
        app = create_app(testing=True)
        username = get_unique_username()

        with TestClient(app) as client:
            # Try to connect without token - should be rejected
            with pytest.raises((Exception, ValueError)):
                with client.websocket_connect(f"/ws/{username}"):
                    pass

    def test_websocket_with_invalid_token(self):
        """Test WebSocket connection with invalid token."""
        app = create_app(testing=True)
        username = get_unique_username()

        with TestClient(app) as client:
            # Try to connect with invalid token - should be rejected
            with pytest.raises((Exception, ValueError)):
                with client.websocket_connect(f"/ws/{username}?token=invalid-token"):
                    pass

    def test_websocket_token_username_mismatch(self):
        """Test WebSocket connection with token-username mismatch."""
        app = create_app(testing=True)
        username1 = get_unique_username()
        username2 = get_unique_username()

        with TestClient(app) as client:
            # Register user and get token
            register_response = client.post(
                "/auth/register",
                json={
                    "username": username1,
                    "password": "testpass123",
                    "email": f"{username1}@test.com",
                },
            )
            token = register_response.json()["access_token"]

            # Try to connect with different username - should be rejected
            with pytest.raises((Exception, ValueError)):
                with client.websocket_connect(f"/ws/{username2}?token={token}"):
                    pass
