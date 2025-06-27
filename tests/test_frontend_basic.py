"""Frontend basic functionality tests for SafeStream.

Tests that the frontend loads correctly and contains expected elements.
"""

from fastapi.testclient import TestClient

from app.main import create_app

# Create test app without background tasks
app = create_app(testing=True)


class TestFrontendBasic:
    """Test basic frontend functionality."""

    def test_chat_page_loads(self):
        """Test that the chat page loads and contains expected elements."""
        with TestClient(app) as client:
            response = client.get("/chat")
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]

            # Check for key HTML elements
            html_content = response.text
            assert "<title>SafeStream - Live Chat</title>" in html_content
            assert 'id="chatMessages"' in html_content
            assert 'id="messageInput"' in html_content
            assert 'id="sendButton"' in html_content
            assert 'id="authModal"' in html_content
            assert 'class="video-bg"' in html_content
            assert 'class="chat-panel"' in html_content

    def test_static_files_accessible(self):
        """Test that static CSS and JS files are accessible."""
        with TestClient(app) as client:
            # Test CSS file
            css_response = client.get("/static/css/styles.css")
            assert css_response.status_code == 200
            assert "text/css" in css_response.headers["content-type"]

            # Test JS file
            js_response = client.get("/static/js/main.js")
            assert js_response.status_code == 200
            assert "text/javascript" in js_response.headers["content-type"]

    def test_frontend_contains_gift_animation_styles(self):
        """Test that the frontend contains gift badge animation styles."""
        with TestClient(app) as client:
            css_response = client.get("/static/css/styles.css")
            assert css_response.status_code == 200

            css_content = css_response.text
            assert ".gift-badge" in css_content
            assert "gift-float-up" in css_content
            assert "gift-glow" in css_content
            assert "#FF1493" in css_content  # TikTok pink color

    def test_frontend_contains_websocket_logic(self):
        """Test that the frontend contains WebSocket connection logic."""
        with TestClient(app) as client:
            js_response = client.get("/static/js/main.js")
            assert js_response.status_code == 200

            js_content = js_response.text
            assert "WebSocket" in js_content
            assert "renderGift" in js_content
            assert "renderMessage" in js_content

    def test_frontend_smoke_test(self):
        """Comprehensive smoke test for frontend functionality."""
        with TestClient(app) as client:
            # Test main chat page
            response = client.get("/chat")
            assert response.status_code == 200

            # Test static assets
            css_response = client.get("/static/css/styles.css")
            js_response = client.get("/static/js/main.js")

            assert css_response.status_code == 200
            assert js_response.status_code == 200

            # Verify content length is reasonable
            assert len(response.text) > 1000  # HTML should be substantial
            assert len(css_response.text) > 500  # CSS should be substantial
            assert len(js_response.text) > 200  # JS should be substantial

    def test_frontend_contains_live_metrics_badge(self):
        """Test that the frontend contains live metrics badge functionality."""
        with TestClient(app) as client:
            # Test that the JavaScript creates the live metrics badge
            js_response = client.get("/static/js/main.js")
            assert js_response.status_code == 200

            js_content = js_response.text
            assert "live-metrics" in js_content
            assert "updateLiveMetrics" in js_content
            assert "fetchMetrics" in js_content

            # Test that the CSS contains live metrics styles
            css_response = client.get("/static/css/styles.css")
            assert css_response.status_code == 200

            css_content = css_response.text
            assert "#live-metrics" in css_content
            assert "position: fixed" in css_content
            assert "top: 8px" in css_content
            assert "left: 8px" in css_content
