"""Tests for JWT authentication functionality."""

import importlib
import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

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


def get_unique_username(prefix: str = "testuser") -> str:
    """Generate a unique username for testing."""
    timestamp = int(time.time() * 1000)
    return f"{prefix}_{timestamp}"


class TestPasswordHashing:
    """Test password hashing functionality."""

    def test_password_hashing(self):
        """Test that passwords are properly hashed and verified."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrongpassword", hashed)

    def test_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes."""
        hash1 = get_password_hash("password1")
        hash2 = get_password_hash("password2")

        assert hash1 != hash2


class TestUserManagement:
    """Test user creation and management."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.users_file = Path(self.temp_dir) / "users.json"
        self.patcher = patch("app.auth.USERS_FILE", self.users_file)
        self.patcher.start()
        # Ensure the file is empty for each test
        self.users_file.write_text("{}", encoding="utf-8")

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.patcher.stop()
        if "SAFESTREAM_USERS_FILE" in os.environ:
            del os.environ["SAFESTREAM_USERS_FILE"]

    def test_create_user(self):
        """Test creating a new user with unique username"""
        # Use timestamp to ensure unique username
        username = get_unique_username()
        password = "testpass"

        # Create user
        with patch("app.auth.USERS_FILE", self.users_file):
            user = create_user(username, password)

            assert user.username == username
            assert user.hashed_password != password
            assert verify_password(password, user.hashed_password)

    def test_create_duplicate_user(self):
        """Test that duplicate usernames are rejected."""
        username = get_unique_username()
        password = "testpass123"

        with patch("app.auth.USERS_FILE", self.users_file):
            create_user(username, password)

            with pytest.raises(Exception) as exc_info:
                create_user(username, "anotherpass")

            assert "already registered" in str(exc_info.value)

    def test_authenticate_user_success(self):
        """Test successful user authentication."""
        username = get_unique_username()
        password = "testpass123"

        with patch("app.auth.USERS_FILE", self.users_file):
            create_user(username, password)
            user = authenticate_user(username, password)

            assert user is not None
            assert user.username == username

    def test_authenticate_user_wrong_password(self):
        """Test authentication with wrong password."""
        username = get_unique_username()
        password = "testpass123"

        with patch("app.auth.USERS_FILE", self.users_file):
            create_user(username, password)
            user = authenticate_user(username, "wrongpass")

            assert user is None

    def test_authenticate_user_nonexistent(self):
        """Test authentication with non-existent user."""
        with patch("app.auth.USERS_FILE", self.users_file):
            user = authenticate_user("nonexistent", "testpass123")

            assert user is None

    def test_get_user(self):
        """Test getting user by username."""
        username = get_unique_username()
        password = "testpass123"

        with patch("app.auth.USERS_FILE", self.users_file):
            create_user(username, password)
            user = get_user(username)

            assert user is not None
            assert user.username == username

    def test_get_user_nonexistent(self):
        """Test getting non-existent user."""
        with patch("app.auth.USERS_FILE", self.users_file):
            user = get_user("nonexistent")

            assert user is None


class TestJWTTokens:
    """Test JWT token creation and validation."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.users_file = Path(self.temp_dir) / "users.json"
        self.patcher = patch("app.auth.USERS_FILE", self.users_file)
        self.patcher.start()

    def teardown_method(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.patcher.stop()
        if "SAFESTREAM_USERS_FILE" in os.environ:
            del os.environ["SAFESTREAM_USERS_FILE"]

    def test_create_access_token(self):
        """Test JWT token creation."""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expiry(self):
        """Test JWT token creation with custom expiry."""
        from datetime import timedelta

        data = {"sub": "testuser"}
        token = create_access_token(data, expires_delta=timedelta(minutes=5))

        assert token is not None

    def test_get_user_by_token_valid(self):
        """Test getting user from valid JWT token."""
        username = get_unique_username()

        with patch("app.auth.USERS_FILE", Path("/tmp/test_users.json")):
            # Create a user first
            create_user(username, "testpass123")

            # Create token
            token = create_access_token({"sub": username})

            # Get user from token
            user = get_user_by_token(token)

            assert user is not None
            assert user.username == username

    def test_get_user_by_token_invalid(self):
        """Test getting user from invalid JWT token."""
        user = get_user_by_token("invalid-token")
        assert user is None

    def test_get_user_by_token_expired(self):
        """Test getting user from expired JWT token."""
        from datetime import timedelta

        # Create token with very short expiry
        data = {"sub": "testuser"}
        token = create_access_token(data, expires_delta=timedelta(seconds=1))

        # Wait for token to expire
        time.sleep(2)

        user = get_user_by_token(token)
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
        """Test custom secret key configuration."""
        # Set custom secret key
        os.environ["JWT_SECRET_KEY"] = "custom-secret-key"

        # Re-import to get the new value
        import app.auth

        importlib.reload(app.auth)

        assert app.auth.SECRET_KEY == "custom-secret-key"

    def test_custom_expire_minutes(self):
        """Test custom token expiry configuration."""
        # Set custom expiry
        os.environ["JWT_EXPIRE_MINUTES"] = "60"

        # Re-import to get the new value
        import app.auth

        importlib.reload(app.auth)

        assert app.auth.ACCESS_TOKEN_EXPIRE_MINUTES == 60


class TestAPIIntegration:
    """Test API integration with FastAPI."""

    def setup_method(self):
        """Set up test environment."""
        self.app = create_app(testing=True)
        self.client = TestClient(self.app)

    def teardown_method(self):
        """Clean up test environment."""
        # Clean up any test files
        test_files = ["users.json", "test_users.json"]
        for file in test_files:
            if os.path.exists(file):
                os.remove(file)

    def test_register_endpoint(self):
        """Test user registration endpoint."""
        username = get_unique_username()
        response = self.client.post(
            "/auth/register",
            json={"username": username, "password": "testpass123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["username"] == username

    def test_register_duplicate_username(self):
        """Test duplicate username registration."""
        username = get_unique_username()

        # First registration
        response1 = self.client.post(
            "/auth/register",
            json={"username": username, "password": "testpass123"},
        )
        assert response1.status_code == 200

        # Second registration with same username
        response2 = self.client.post(
            "/auth/register",
            json={"username": username, "password": "anotherpass"},
        )
        assert response2.status_code == 400

    def test_login_endpoint(self):
        """Test user login endpoint."""
        username = get_unique_username()

        # Register user first
        self.client.post(
            "/auth/register",
            json={"username": username, "password": "testpass123"},
        )

        # Login
        response = self.client.post(
            "/auth/login",
            data={"username": username, "password": "testpass123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["username"] == username

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = self.client.post(
            "/auth/login",
            data={"username": "nonexistent", "password": "wrongpass"},
        )
        assert response.status_code == 401

    def test_protected_endpoint_with_token(self):
        """Test accessing protected endpoint with valid token."""
        username = get_unique_username()

        # Register and get token
        response = self.client.post(
            "/auth/register",
            json={"username": username, "password": "testpass123"},
        )
        token = response.json()["access_token"]

        # Access protected endpoint
        response = self.client.get(
            "/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

    def test_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token."""
        response = self.client.get("/auth/me")
        assert response.status_code == 401

    def test_admin_endpoints_with_authentication(self):
        """Test admin endpoints with authentication."""
        username = get_unique_username()

        # Register and get token
        response = self.client.post(
            "/auth/register",
            json={"username": username, "password": "testpass123"},
        )
        token = response.json()["access_token"]

        # Test admin kick endpoint
        response = self.client.post(
            "/api/admin/kick",
            json={"username": "target_user"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_admin_endpoints_without_authentication(self):
        """Test admin endpoints without authentication."""
        response = self.client.post("/api/admin/kick", json={"username": "target_user"})
        assert response.status_code == 401


class TestWebSocketAuthentication:
    """Test WebSocket authentication."""

    def setup_method(self):
        """Set up test environment."""
        self.app = create_app(testing=True)
        self.client = TestClient(self.app)

    def teardown_method(self):
        """Clean up test environment."""
        # Clean up any test files
        test_files = ["users.json", "test_users.json"]
        for file in test_files:
            if os.path.exists(file):
                os.remove(file)

    def test_websocket_with_valid_token(self):
        """Test WebSocket connection with valid token."""
        username = get_unique_username()

        # Register and get token
        response = self.client.post(
            "/auth/register",
            json={"username": username, "password": "testpass123"},
        )
        token = response.json()["access_token"]

        # Connect to WebSocket with token
        with self.client.websocket_connect(
            f"/ws/{username}?token={token}"
        ) as websocket:
            # Send a message
            websocket.send_text('{"type": "chat", "message": "Hello, world!"}')

            # Receive response
            data = websocket.receive_text()
            message = json.loads(data)

            assert isinstance(message, dict)
            assert "type" in message
            assert message["type"] == "chat"
            assert message["user"] == username
            assert message["message"] == "Hello, world!"

    def test_websocket_without_token(self):
        """Test WebSocket connection without token."""
        username = get_unique_username()

        with pytest.raises(WebSocketDisconnect):
            with self.client.websocket_connect(f"/ws/{username}"):
                pass

    def test_websocket_with_invalid_token(self):
        """Test WebSocket connection with invalid token."""
        username = get_unique_username()

        with pytest.raises(WebSocketDisconnect):
            with self.client.websocket_connect(f"/ws/{username}?token=invalid"):
                pass

    def test_websocket_token_username_mismatch(self):
        username1 = get_unique_username("user1")
        username2 = get_unique_username("user2")
        response = self.client.post(
            "/auth/register",
            json={"username": username1, "password": "testpass123"},
        )
        token = response.json()["access_token"]
        # Only check that connecting as username2 with username1's token fails
        with pytest.raises(WebSocketDisconnect):
            with self.client.websocket_connect(f"/ws/{username2}?token={token}"):
                pass


if __name__ == "__main__":
    pytest.main([__file__])
