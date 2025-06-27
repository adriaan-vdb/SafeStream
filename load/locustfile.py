"""Locust load testing for SafeStream.

Simulates multiple users connecting to the chat and sending messages.
Install with: pip install locust
Run with: locust -f load/locustfile.py --host=http://localhost:8000
"""

import json
import random
import time

from locust import HttpUser, between, events, task
from websocket import create_connection


class ChatUser(HttpUser):
    """Simulates a user connecting to the chat and sending messages."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self):
        """Initialize user session."""
        self.username = f"user_{random.randint(1000, 9999)}"
        self.websocket = None
        self.connected = False

    def on_stop(self):
        """Clean up user session."""
        if self.websocket:
            try:
                self.websocket.close()
            except Exception:
                pass

    def connect_websocket(self):
        """Connect to WebSocket chat."""
        try:
            # Convert HTTP URL to WebSocket URL
            ws_url = (
                self.client.base_url.replace("http://", "ws://")
                + f"/ws/{self.username}"
            )
            self.websocket = create_connection(ws_url)
            self.connected = True
            return True
        except Exception as e:
            self.client.environment.events.request.fire(
                request_type="WebSocket",
                name="connect",
                response_time=0,
                response_length=0,
                exception=e,
            )
            return False

    @task(3)
    def send_chat_message(self):
        """Send a chat message."""
        if not self.connected:
            if not self.connect_websocket():
                return

        try:
            # Generate random message
            messages = [
                "Hello everyone!",
                "How's it going?",
                "Great stream!",
                "Thanks for the content!",
                "This is awesome!",
                "Keep it up!",
                "Love this!",
                "Amazing work!",
                "Can't wait for more!",
                "You're doing great!",
            ]

            message = random.choice(messages)
            chat_data = {"type": "chat", "message": message}

            start_time = time.time()
            self.websocket.send(json.dumps(chat_data))

            # Wait for response
            response = self.websocket.recv()
            response_time = int((time.time() - start_time) * 1000)

            # Log success
            self.client.environment.events.request.fire(
                request_type="WebSocket",
                name="chat_message",
                response_time=response_time,
                response_length=len(response),
                exception=None,
            )

        except Exception as e:
            self.client.environment.events.request.fire(
                request_type="WebSocket",
                name="chat_message",
                response_time=0,
                response_length=0,
                exception=e,
            )
            self.connected = False

    @task(1)
    def send_gift(self):
        """Send a gift via API."""
        try:
            gift_data = {
                "from": self.username,
                "gift_id": random.randint(1, 100),
                "amount": random.randint(1, 10),
            }

            with self.client.post(
                "/api/gift", json=gift_data, catch_response=True
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Gift API returned {response.status_code}")

        except Exception as e:
            self.client.environment.events.request.fire(
                request_type="HTTP",
                name="send_gift",
                response_time=0,
                response_length=0,
                exception=e,
            )

    @task(1)
    def check_metrics(self):
        """Check metrics endpoint."""
        try:
            with self.client.get("/metrics", catch_response=True) as response:
                if response.status_code == 200:
                    data = response.json()
                    # Verify metrics structure
                    if all(
                        key in data
                        for key in ["viewer_count", "gift_count", "toxic_pct"]
                    ):
                        response.success()
                    else:
                        response.failure("Invalid metrics response structure")
                else:
                    response.failure(
                        f"Metrics endpoint returned {response.status_code}"
                    )

        except Exception as e:
            self.client.environment.events.request.fire(
                request_type="HTTP",
                name="check_metrics",
                response_time=0,
                response_length=0,
                exception=e,
            )

    @task(1)
    def check_health(self):
        """Check health endpoint."""
        try:
            with self.client.get("/healthz", catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Health endpoint returned {response.status_code}")

        except Exception as e:
            self.client.environment.events.request.fire(
                request_type="HTTP",
                name="check_health",
                response_time=0,
                response_length=0,
                exception=e,
            )


class MetricsUser(HttpUser):
    """Simulates a monitoring system checking metrics."""

    wait_time = between(5, 10)  # Check metrics every 5-10 seconds

    @task
    def check_metrics(self):
        """Check metrics endpoint."""
        try:
            with self.client.get("/metrics", catch_response=True) as response:
                if response.status_code == 200:
                    data = response.json()
                    # Verify metrics structure and types
                    if (
                        isinstance(data.get("viewer_count"), int)
                        and isinstance(data.get("gift_count"), int)
                        and isinstance(data.get("toxic_pct"), int | float)
                    ):
                        response.success()
                    else:
                        response.failure("Invalid metrics data types")
                else:
                    response.failure(
                        f"Metrics endpoint returned {response.status_code}"
                    )

        except Exception as e:
            self.client.environment.events.request.fire(
                request_type="HTTP",
                name="check_metrics",
                response_time=0,
                response_length=0,
                exception=e,
            )


# Custom event handlers for better reporting
@events.request.add_listener
def my_request_handler(
    request_type, name, response_time, response_length, exception, **kwargs
):
    """Custom request handler for detailed logging."""
    if exception:
        print(f"Request failed: {request_type} {name} - {exception}")
    else:
        print(f"Request success: {request_type} {name} - {response_time}ms")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when a test starts."""
    print("Starting SafeStream load test...")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when a test stops."""
    print("SafeStream load test completed.")
