"""WebSocket functionality for DevPulse."""

import asyncio
import json
import logging
from typing import Dict, Any, List, Set, Optional

import websockets
from websockets.exceptions import ConnectionClosed

from .core import get_config

# Setup logger
logger = logging.getLogger("devpulse.websocket")

# Global variables
_websocket_client = None
_event_queue = asyncio.Queue()
_connected = False


async def connect_websocket() -> None:
    """Connect to the WebSocket server."""
    global _websocket_client, _connected

    websocket_url = get_config().get("websocket_url")
    if not websocket_url:
        logger.error("WebSocket URL not configured")
        return

    try:
        _websocket_client = await websockets.connect(websocket_url)
        _connected = True
        logger.info(f"Connected to WebSocket server at {websocket_url}")

        # Start background task to process event queue
        asyncio.create_task(process_event_queue())
    except Exception as e:
        logger.error(f"Failed to connect to WebSocket server: {str(e)}")
        _connected = False


async def process_event_queue() -> None:
    """Process events from the queue and send them to the WebSocket server."""
    global _websocket_client, _connected

    while True:
        try:
            # Get event from queue
            event = await _event_queue.get()

            # Send event to WebSocket server
            if _websocket_client and _connected:
                await _websocket_client.send(json.dumps(event))
            else:
                # Try to reconnect
                await connect_websocket()
                if _websocket_client and _connected:
                    await _websocket_client.send(json.dumps(event))
                else:
                    logger.error(f"Failed to send event: {event['traceId']}")

            # Mark task as done
            _event_queue.task_done()
        except ConnectionClosed:
            logger.warning("WebSocket connection closed, reconnecting...")
            _connected = False
            await connect_websocket()
        except Exception as e:
            logger.error(f"Error processing event queue: {str(e)}")
            await asyncio.sleep(1)  # Avoid tight loop on error


def send_event(event: Dict[str, Any]) -> None:
    """Send an event to the WebSocket server.

    This function adds the event to the queue for processing by the
    background task. If the queue is full, the event is dropped.

    Args:
        event: The event to send
    """
    try:
        # Add event to queue
        asyncio.create_task(_event_queue.put_nowait(event))
    except asyncio.QueueFull:
        logger.warning("Event queue full, dropping event")
    except Exception as e:
        logger.error(f"Error sending event: {str(e)}")


async def start_websocket_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Start a WebSocket server for receiving events.

    This function starts a WebSocket server that listens for incoming
    connections and processes events received from clients.

    Args:
        host: The host to bind to
        port: The port to listen on
    """
    # Connected clients by trace ID
    clients: Dict[str, Set[websockets.WebSocketServerProtocol]] = {}

    async def register(websocket: websockets.WebSocketServerProtocol, trace_id: str) -> None:
        """Register a client for a specific trace ID."""
        if trace_id not in clients:
            clients[trace_id] = set()
        clients[trace_id].add(websocket)
        logger.info(f"Client registered for trace ID: {trace_id}")

    async def unregister(websocket: websockets.WebSocketServerProtocol, trace_id: str) -> None:
        """Unregister a client for a specific trace ID."""
        if trace_id in clients:
            clients[trace_id].remove(websocket)
            if not clients[trace_id]:
                del clients[trace_id]
            logger.info(f"Client unregistered for trace ID: {trace_id}")

    async def handler(websocket: websockets.WebSocketServerProtocol, path: str) -> None:
        """Handle incoming WebSocket connections."""
        # Extract trace ID from path
        trace_id = path.strip("/")
        if not trace_id:
            await websocket.close(1008, "Trace ID required")
            return

        # Register client
        await register(websocket, trace_id)

        try:
            # Keep connection open
            async for message in websocket:
                # Process incoming messages (if any)
                pass
        except ConnectionClosed:
            pass
        finally:
            # Unregister client
            await unregister(websocket, trace_id)

    # Start server
    async with websockets.serve(handler, host, port):
        logger.info(f"WebSocket server started at ws://{host}:{port}")
        await asyncio.Future()  # Run forever


async def broadcast_event(event: Dict[str, Any]) -> None:
    """Broadcast an event to all clients subscribed to its trace ID.

    Args:
        event: The event to broadcast
    """
    trace_id = event.get("traceId")
    if not trace_id:
        logger.warning("Event missing trace ID, cannot broadcast")
        return

    # Get clients for trace ID
    clients_for_trace = clients.get(trace_id, set())
    if not clients_for_trace:
        return

    # Broadcast event to clients
    event_json = json.dumps(event)
    websockets_to_remove = set()

    for websocket in clients_for_trace:
        try:
            await websocket.send(event_json)
        except ConnectionClosed:
            websockets_to_remove.add(websocket)
        except Exception as e:
            logger.error(f"Error broadcasting event: {str(e)}")
            websockets_to_remove.add(websocket)

    # Remove closed connections
    for websocket in websockets_to_remove:
        await unregister(websocket, trace_id)