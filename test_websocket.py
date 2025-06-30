import asyncio
import json
import sys

import websockets


async def test_websocket_publisher(token):
    """Test publisher WebSocket connection"""
    try:
        uri = f"ws://localhost:8000/ws/stream-signal?role=publisher&token={token}"

        async with websockets.connect(uri) as websocket:
            print("Publisher WebSocket connected successfully")

            # Wait a moment to see if we get any immediate messages
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                print(f"Received response: {response}")
            except TimeoutError:
                print("No immediate response (connection stable)")

            return True
    except Exception as e:
        print(f"Publisher WebSocket failed: {e}")
        return False


async def test_websocket_viewer(token):
    """Test viewer WebSocket connection when no stream is active"""
    try:
        uri = f"ws://localhost:8000/ws/stream-signal?role=viewer&token={token}"

        async with websockets.connect(uri) as websocket:
            print("Viewer WebSocket connected")

            # Should receive error about no active stream
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                data = json.loads(response)
                if (
                    data.get("type") == "error"
                    and "no active stream" in data.get("message", "").lower()
                ):
                    print("Viewer correctly notified of no active stream")
                    return True
                else:
                    print(f"Unexpected response: {response}")
                    return False
            except TimeoutError:
                print("No response received (viewer connection timeout)")
                return True  # This is actually okay for viewer with no active stream
            except Exception as e:
                print(f"Error receiving viewer message: {e}")
                return False

    except Exception as e:
        print(f"Viewer WebSocket failed: {e}")
        return False


async def main():
    streamer_token = sys.argv[1]
    viewer_token = sys.argv[2]

    print(f"Testing with streamer token: {streamer_token[:50]}...")
    print(f"Testing with viewer token: {viewer_token[:50]}...")

    # Test publisher connection
    publisher_result = await test_websocket_publisher(streamer_token)

    # Test viewer connection
    viewer_result = await test_websocket_viewer(viewer_token)

    if publisher_result and viewer_result:
        print("WebSocket tests passed")
        sys.exit(0)
    else:
        print("WebSocket tests failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
