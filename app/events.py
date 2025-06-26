"""SafeStream event handling and gift simulation.

Implements random gift generation and broadcasting to all connected WebSocket clients.
"""

import asyncio
import json
import logging
import os
import random
from datetime import UTC, datetime

from app import schemas

# Configuration
GIFT_RATE_SEC = int(os.getenv("GIFT_RATE_SEC", "15"))
TOXIC_THRESHOLD = float(os.getenv("TOXIC_THRESHOLD", "0.6"))

# Sample gift data for random generation
SAMPLE_GIFTS = [
    {"from_user": "admin", "gift_id": 1, "amount": 1},
    {"from_user": "moderator", "gift_id": 2, "amount": 5},
    {"from_user": "viewer", "gift_id": 3, "amount": 10},
    {"from_user": "fan", "gift_id": 4, "amount": 2},
    {"from_user": "supporter", "gift_id": 5, "amount": 3},
]


async def start_gift_simulation(websocket_connections: dict[str, any]):
    """Start background task for random gift events.

    Sleeps GIFT_RATE_SEC±random seconds between gifts.
    Broadcasts random gift events to all connected clients.
    """
    logger = logging.getLogger("gift_simulation")
    logger.info(f"Starting gift simulation with rate: {GIFT_RATE_SEC}±5 seconds")

    while True:
        try:
            # Random sleep time: GIFT_RATE_SEC ± 5 seconds
            sleep_time = GIFT_RATE_SEC + random.randint(-5, 5)
            sleep_time = max(1, sleep_time)  # Ensure minimum 1 second

            await asyncio.sleep(sleep_time)

            # Generate random gift
            gift_data = random.choice(SAMPLE_GIFTS).copy()

            # Create gift event with timestamp
            gift_event = schemas.GiftEventOut(**gift_data)
            gift_event_dict = gift_event.model_dump(by_alias=True)
            gift_event_dict["ts"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")

            # Broadcast to all connected clients
            await broadcast_gift(websocket_connections, gift_event_dict)

            logger.info(f"Broadcasted gift: {gift_event_dict}")

        except asyncio.CancelledError:
            # Task was cancelled, exit gracefully
            logger.info("Gift simulation task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in gift simulation: {e}")
            await asyncio.sleep(5)  # Wait before retrying


async def broadcast_gift(connections: dict[str, any], gift_data: dict):
    """Broadcast gift event to all connected clients.

    Sends JSON matching README protocol: {"type":"gift","from":"admin","gift_id":999,"amount":1}
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


async def create_gift_task(websocket_connections: dict[str, any]):
    """Create and return the gift simulation background task.

    This function allows main.py to start the gift simulation as a background task.
    """
    return asyncio.create_task(start_gift_simulation(websocket_connections))
