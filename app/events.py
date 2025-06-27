"""SafeStream event handling and gift simulation.

Implements random gift generation and broadcasting to all connected WebSocket clients.
"""

import asyncio
import json
import logging
import os
import random
from datetime import UTC, datetime
from typing import Any

from fastapi import WebSocket

from app import schemas
from app.metrics import metrics

# Configuration
GIFT_INTERVAL_SECS = int(os.getenv("GIFT_INTERVAL_SECS", "15"))
TOXIC_THRESHOLD = float(os.getenv("TOXIC_THRESHOLD", "0.6"))


async def gift_producer(websocket_connections: dict[str, WebSocket]):
    """Async background task that periodically generates and broadcasts random gift events.

    Runs in an infinite loop, generating gifts at GIFT_INTERVAL_SECS intervals.
    Uses deterministic random generation for testability.
    """
    logger = logging.getLogger("gift_producer")
    logger.info(f"Starting gift producer with interval: {GIFT_INTERVAL_SECS} seconds")

    while True:
        try:
            # Wait for the configured interval
            await asyncio.sleep(GIFT_INTERVAL_SECS)

            # Generate random gift data
            gift_id = random.randint(1, 1000)
            amount = random.randint(1, 5)

            # Create gift event with bot sender
            gift_event = schemas.GiftEventOut(
                from_user="bot", gift_id=gift_id, amount=amount  # type: ignore
            )

            # Track metrics for gift event
            metrics.increment_gift_count()

            # Convert to dict with proper aliasing and add timestamp
            gift_event_dict = gift_event.model_dump(by_alias=True)
            gift_event_dict["ts"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")

            # Log the gift event
            logger.info(json.dumps(gift_event_dict))

            # Broadcast to all connected clients
            await broadcast_gift(websocket_connections, gift_event_dict)

        except asyncio.CancelledError:
            # Task was cancelled, exit gracefully
            logger.info("Gift producer task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in gift producer: {e}")
            await asyncio.sleep(5)  # Wait before retrying


async def broadcast_gift(connections: dict[str, WebSocket], gift_data: dict[str, Any]):
    """Broadcast gift event to all connected clients.

    Sends JSON matching README protocol: {"type":"gift","from":"bot","gift_id":123,"amount":5,"ts":"2025-06-26T12:34:56Z"}
    """
    message_json = json.dumps(gift_data)
    disconnected_clients = []

    for client_username, client_websocket in connections.items():
        try:
            await client_websocket.send_text(message_json)
        except Exception as e:
            # Mark for removal
            disconnected_clients.append(client_username)
            logging.warning(f"Failed to send gift to {client_username}: {e}")

    # Clean up disconnected clients
    for username in disconnected_clients:
        if username in connections:
            del connections[username]


async def create_gift_task(websocket_connections: dict[str, WebSocket]):
    """Create and return the gift producer background task.

    This function allows main.py to start the gift producer as a background task.
    """
    return asyncio.create_task(gift_producer(websocket_connections))
