import time

from fastapi.testclient import TestClient

from app.main import create_app


def get_unique_username(prefix: str = "testuser") -> str:
    """Generate a unique username for testing."""
    timestamp = int(time.time() * 1000)
    return f"{prefix}_{timestamp}"


def create_test_user_and_token(client: TestClient, username: str) -> str:
    """Create a test user and return JWT token."""
    response = client.post(
        "/auth/register",
        json={"username": username, "password": "testpass123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_admin_kick():
    app = create_app(testing=True)
    client = TestClient(app)

    # Create test user and get token
    username = get_unique_username("admin")
    token = create_test_user_and_token(client, username)

    # Test admin kick endpoint with authentication
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post(
        "/api/admin/kick", json={"username": "testuser"}, headers=headers
    )
    assert resp.status_code == 200
