"""Test frontend basic functionality."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app(testing=True)
    return TestClient(app)


def test_chat_route_returns_html(client):
    """Test that /chat route returns HTML content."""
    response = client.get("/chat")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<!DOCTYPE html>" in response.text


def test_chat_route_includes_websocket_script(client):
    """Test that /chat route includes WebSocket client script."""
    response = client.get("/chat")
    assert response.status_code == 200
    # Check for WebSocket usage in the HTML (the script tag references main.js)
    assert "main.js" in response.text
    # The actual WebSocket code is in main.js, not in the HTML


def test_chat_route_includes_styles(client):
    """Test that /chat route includes CSS styles."""
    response = client.get("/chat")
    assert response.status_code == 200
    assert "styles.css" in response.text


def test_static_files_served(client):
    """Test that static files are served correctly."""
    # Test CSS file
    response = client.get("/static/css/styles.css")
    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]

    # Test JS file
    response = client.get("/static/js/main.js")
    assert response.status_code == 200
    # FastAPI serves JS as text/javascript, not application/javascript
    assert "text/javascript" in response.headers["content-type"]


def test_chat_route_has_tiktok_style_elements(client):
    """Test that /chat route has TikTok-style live chat elements."""
    response = client.get("/chat")
    assert response.status_code == 200
    html = response.text.lower()

    # Check for common live chat elements
    assert "chat" in html
    assert "live" in html
    assert "message" in html
    # Check for specific elements from the actual HTML
    assert "chat-messages" in html
    assert "input-bar" in html
    assert "username" in html
