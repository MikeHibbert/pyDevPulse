"""Example WebSocket client for DevPulse."""

import asyncio
import json
import logging
import sys
from typing import Dict, Any, Optional

import websockets
from websockets.exceptions import ConnectionClosed

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("websocket_client")


async def connect_and_listen(trace_id: str, websocket_url: str = "ws://localhost:8000/ws") -> None:
    """Connect to the WebSocket server and listen for events.

    Args:
        trace_id: The trace ID to subscribe to
        websocket_url: The WebSocket server URL
    """
    # Construct URL with trace ID
    url = f"{websocket_url}/{trace_id}"
    logger.info(f"Connecting to {url}")

    try:
        async with websockets.connect(url) as websocket:
            logger.info(f"Connected to {url}")

            # Listen for events
            while True:
                try:
                    # Receive message
                    message = await websocket.recv()

                    # Parse message as JSON
                    try:
                        event = json.loads(message)
                        print_event(event)
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON message: {message}")
                except ConnectionClosed:
                    logger.warning("Connection closed")
                    break
                except Exception as e:
                    logger.error(f"Error receiving message: {str(e)}")
                    break
    except Exception as e:
        logger.error(f"Error connecting to WebSocket server: {str(e)}")


def print_event(event: Dict[str, Any]) -> None:
    """Print an event to the console.

    Args:
        event: The event to print
    """
    # Get event details
    trace_id = event.get("traceId", "unknown")
    timestamp = event.get("timestamp", "unknown")
    severity = event.get("severity", "info")
    system = event.get("system", "unknown")
    details = event.get("details", "")
    file = event.get("file", "")
    line = event.get("line", "")
    source = event.get("source", "")

    # Print event
    print(f"\n[{timestamp}] {severity.upper()} [{system}] {trace_id}")
    print(f"  {details}")
    if file and line:
        print(f"  at {file}:{line} in {source}")

    # Print locals if available
    locals_dict = event.get("locals", {})
    if locals_dict:
        print("  Locals:")
        for key, value in locals_dict.items():
            print(f"    {key} = {value}")

    # Print stacktrace if available
    stacktrace = event.get("stacktrace", [])
    if stacktrace:
        print("  Stacktrace:")
        for line in stacktrace:
            print(f"    {line.strip()}")


async def main() -> None:
    """Main function."""
    # Get trace ID from command line
    if len(sys.argv) < 2:
        print("Usage: python websocket_client.py <trace_id>")
        return

    trace_id = sys.argv[1]
    websocket_url = "ws://localhost:8000/ws"

    # Connect to WebSocket server
    await connect_and_listen(trace_id, websocket_url)


if __name__ == "__main__":
    asyncio.run(main())