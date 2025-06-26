"""Smoke tests for SafeStream FastAPI application.

# Requires httpx via fastapi.testclient – declared in [project.optional-dependencies].dev
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test that root endpoint returns HTTP 200 and correct response."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_endpoint():
    """Test that health endpoint returns HTTP 200 and correct response."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
