"""Example WebSocket server for DevPulse."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set, Any

import websockets
from websockets.exceptions import ConnectionClosed

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("websocket_server")

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


async def broadcast_event(event: Dict[str, Any]) -> None:
    """Broadcast an event to all clients subscribed to its trace ID."""
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


async def handler(websocket: websockets.WebSocketServerProtocol, path: str) -> None:
    """Handle incoming WebSocket connections."""
    # Extract trace ID from path
    parts = path.strip("/").split("/")
    if len(parts) < 2 or parts[0] != "ws":
        await websocket.close(1008, "Invalid path")
        return

    trace_id = parts[1]
    if not trace_id:
        await websocket.close(1008, "Trace ID required")
        return

    # Register client
    await register(websocket, trace_id)

    try:
        # Process incoming messages
        async for message in websocket:
            try:
                # Parse message as JSON
                event = json.loads(message)

                # Add timestamp if not present
                if "timestamp" not in event:
                    event["timestamp"] = datetime.utcnow().isoformat() + "Z"

                # Broadcast event to clients
                await broadcast_event(event)

                # Log event
                logger.info(f"Event received for trace ID {trace_id}: {event.get('details', '')}")
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON message: {message}")
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
    except ConnectionClosed:
        pass
    finally:
        # Unregister client
        await unregister(websocket, trace_id)


async def main() -> None:
    """Start the WebSocket server."""
    host = "0.0.0.0"
    port = 8000

    # Start server
    async with websockets.serve(handler, host, port):
        logger.info(f"WebSocket server started at ws://{host}:{port}")
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    asyncio.run(main())