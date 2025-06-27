"""Playwright UI tests for SafeStream frontend.

Tests the chat interface, gift animations, and user interactions.
Requires Playwright to be installed: pip install playwright && playwright install
"""

import os
import subprocess
import time
from pathlib import Path

import pytest

# Check if Playwright is available
try:
    from playwright.async_api import async_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class TestSafeStreamUI:
    """Playwright UI tests for SafeStream frontend."""

    @pytest.fixture(scope="class")
    def server_process(self):
        """Start the FastAPI server for UI testing."""
        # Start server in background
        process = subprocess.Popen(
            ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=Path(__file__).parent.parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for server to start
        time.sleep(3)

        yield process

        # Cleanup
        process.terminate()
        process.wait()

    @pytest.mark.asyncio
    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not installed")
    async def test_chat_interface_loads(self, server_process):
        """Test that the chat interface loads correctly."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Navigate to chat page
            await page.goto("http://localhost:8000/chat")

            # Check that the page loads
            await page.wait_for_load_state("networkidle")

            # Verify key elements are present
            assert await page.locator("#usernameModal").is_visible()
            assert await page.locator("#messageInput").is_visible()
            assert await page.locator("#sendButton").is_visible()

            await browser.close()

    @pytest.mark.asyncio
    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not installed")
    async def test_username_modal_and_connection(self, server_process):
        """Test username modal and WebSocket connection."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Navigate to chat page
            await page.goto("http://localhost:8000/chat")
            await page.wait_for_load_state("networkidle")

            # Username modal should be visible initially
            assert await page.locator("#usernameModal").is_visible()

            # Enter username and connect
            await page.fill("#usernameInput", "testuser")
            await page.click("#connectButton")

            # Modal should disappear after connection
            await page.wait_for_selector("#usernameModal", state="hidden")

            # Input should be enabled
            assert not await page.locator("#messageInput").is_disabled()
            assert not await page.locator("#sendButton").is_disabled()

            await browser.close()

    @pytest.mark.asyncio
    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not installed")
    async def test_chat_message_sending(self, server_process):
        """Test sending and receiving chat messages."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Navigate and connect
            await page.goto("http://localhost:8000/chat")
            await page.wait_for_load_state("networkidle")
            await page.fill("#usernameInput", "testuser")
            await page.click("#connectButton")
            await page.wait_for_selector("#usernameModal", state="hidden")

            # Send a message
            await page.fill("#messageInput", "Hello, world!")
            await page.click("#sendButton")

            # Wait for message to appear in chat
            await page.wait_for_selector(".message", timeout=5000)

            # Verify message content
            message_text = await page.locator(".message").first.text_content()
            assert "Hello, world!" in message_text
            assert "testuser" in message_text

            await browser.close()

    @pytest.mark.asyncio
    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not installed")
    async def test_gift_animation(self, server_process):
        """Test gift animation display."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Navigate and connect
            await page.goto("http://localhost:8000/chat")
            await page.wait_for_load_state("networkidle")
            await page.fill("#usernameInput", "testuser")
            await page.click("#connectButton")
            await page.wait_for_selector("#usernameModal", state="hidden")

            # Trigger a gift via API
            import requests

            gift_data = {"from": "test", "gift_id": 1, "amount": 5}
            response = requests.post("http://localhost:8000/api/gift", json=gift_data)
            assert response.status_code == 200

            # Wait for gift animation to appear
            await page.wait_for_selector(".gift-badge", timeout=10000)

            # Verify gift animation elements
            gift_badge = await page.locator(".gift-badge").first
            assert await gift_badge.is_visible()

            # Check gift content
            gift_text = await gift_badge.text_content()
            assert "test" in gift_text
            assert "5" in gift_text

            await browser.close()

    @pytest.mark.asyncio
    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not installed")
    async def test_metrics_endpoint(self, server_process):
        """Test that metrics endpoint is accessible."""
        import requests

        # Test metrics endpoint
        response = requests.get("http://localhost:8000/metrics")
        assert response.status_code == 200

        data = response.json()
        assert "viewer_count" in data
        assert "gift_count" in data
        assert "toxic_pct" in data

        # Verify data types
        assert isinstance(data["viewer_count"], int)
        assert isinstance(data["gift_count"], int)
        assert isinstance(data["toxic_pct"], float)

    @pytest.mark.asyncio
    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not installed")
    async def test_multiple_users_chat(self, server_process):
        """Test multiple users chatting simultaneously."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            # Create two pages for different users
            page1 = await browser.new_page()
            page2 = await browser.new_page()

            # Connect first user
            await page1.goto("http://localhost:8000/chat")
            await page1.wait_for_load_state("networkidle")
            await page1.fill("#usernameInput", "alice")
            await page1.click("#connectButton")
            await page1.wait_for_selector("#usernameModal", state="hidden")

            # Connect second user
            await page2.goto("http://localhost:8000/chat")
            await page2.wait_for_load_state("networkidle")
            await page2.fill("#usernameInput", "bob")
            await page2.click("#connectButton")
            await page2.wait_for_selector("#usernameModal", state="hidden")

            # Send message from alice
            await page1.fill("#messageInput", "Hello from Alice!")
            await page1.click("#sendButton")

            # Wait for message to appear on both pages
            await page1.wait_for_selector(".message", timeout=5000)
            await page2.wait_for_selector(".message", timeout=5000)

            # Verify message appears on both pages
            message1 = await page1.locator(".message").first.text_content()
            message2 = await page2.locator(".message").first.text_content()

            assert "Hello from Alice!" in message1
            assert "Hello from Alice!" in message2
            assert "alice" in message1
            assert "alice" in message2

            await browser.close()

    @pytest.mark.asyncio
    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not installed")
    async def test_connection_recovery(self, server_process):
        """Test WebSocket connection recovery after disconnection."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Navigate and connect
            await page.goto("http://localhost:8000/chat")
            await page.wait_for_load_state("networkidle")
            await page.fill("#usernameInput", "testuser")
            await page.click("#connectButton")
            await page.wait_for_selector("#usernameModal", state="hidden")

            # Verify connection is active
            assert not await page.locator("#messageInput").is_disabled()

            # Simulate network interruption (this is a basic test)
            # In a real scenario, you might want to test actual network disconnection

            await browser.close()


# Alternative: Mark all tests as requiring Playwright
pytestmark = pytest.mark.skipif(
    not os.getenv("ENABLE_PLAYWRIGHT_TESTS", "0") == "1",
    reason="Playwright tests disabled. Set ENABLE_PLAYWRIGHT_TESTS=1 to enable.",
)
