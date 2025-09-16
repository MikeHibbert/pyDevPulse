"""Command-line interface for DevPulse."""

import argparse
import asyncio
import json
import logging
import os
import sys
from typing import Dict, Any, List, Optional

from . import __version__
from .database import init_db, get_events, clear_events

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("devpulse.cli")


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="DevPulse - Distributed tracing and error tracking for Python applications"
    )
    parser.add_argument(
        "--version", action="version", version=f"DevPulse {__version__}"
    )

    # Create subparsers
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Server command
    server_parser = subparsers.add_parser(
        "server", help="Start the WebSocket server"
    )
    server_parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="Host to bind to"
    )
    server_parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind to"
    )

    # Client command
    client_parser = subparsers.add_parser(
        "client", help="Connect to the WebSocket server"
    )
    client_parser.add_argument(
        "trace_id", type=str, help="Trace ID to subscribe to"
    )
    client_parser.add_argument(
        "--url", type=str, default="ws://localhost:8000/ws", help="WebSocket server URL"
    )

    # DB command
    db_parser = subparsers.add_parser(
        "db", help="Interact with the database"
    )
    db_subparsers = db_parser.add_subparsers(dest="db_command", help="Database command")

    # DB list command
    db_list_parser = db_subparsers.add_parser(
        "list", help="List events from the database"
    )
    db_list_parser.add_argument(
        "--trace-id", type=str, help="Filter by trace ID"
    )
    db_list_parser.add_argument(
        "--limit", type=int, default=10, help="Maximum number of events to return"
    )
    db_list_parser.add_argument(
        "--format", type=str, choices=["json", "table"], default="table",
        help="Output format"
    )

    # DB clear command
    db_clear_parser = db_subparsers.add_parser(
        "clear", help="Clear events from the database"
    )
    db_clear_parser.add_argument(
        "--trace-id", type=str, help="Clear events with this trace ID"
    )
    db_clear_parser.add_argument(
        "--all", action="store_true", help="Clear all events"
    )

    return parser


async def start_server(host: str, port: int) -> None:
    """Start the WebSocket server."""
    # Import here to avoid circular imports
    from .websocket import start_server as ws_start_server

    await ws_start_server(host, port)


async def start_client(trace_id: str, url: str) -> None:
    """Connect to the WebSocket server and listen for events."""
    # Import here to avoid circular imports
    import websockets
    from websockets.exceptions import ConnectionClosed

    # Construct URL with trace ID
    full_url = f"{url}/{trace_id}"
    logger.info(f"Connecting to {full_url}")

    try:
        async with websockets.connect(full_url) as websocket:
            logger.info(f"Connected to {full_url}")

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
    """Print an event to the console."""
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


def list_events(trace_id: Optional[str], limit: int, format_type: str) -> None:
    """List events from the database."""
    # Initialize database
    db_url = os.environ.get("DEVPULSE_DB_URL", "sqlite:///devpulse.db")
    init_db(db_url)

    # Get events
    events = get_events(trace_id=trace_id, limit=limit)

    # Print events
    if not events:
        print("No events found")
        return

    if format_type == "json":
        print(json.dumps(events, indent=2))
    else:  # table
        # Print table header
        print(f"{'Trace ID':<36} | {'Timestamp':<24} | {'Severity':<8} | {'System':<10} | Details")
        print("-" * 100)

        # Print table rows
        for event in events:
            trace_id = event.get("traceId", "unknown")
            timestamp = event.get("timestamp", "unknown")
            severity = event.get("severity", "info")
            system = event.get("system", "unknown")
            details = event.get("details", "")

            print(f"{trace_id:<36} | {timestamp:<24} | {severity:<8} | {system:<10} | {details}")


def clear_db_events(trace_id: Optional[str], clear_all: bool) -> None:
    """Clear events from the database."""
    # Initialize database
    db_url = os.environ.get("DEVPULSE_DB_URL", "sqlite:///devpulse.db")
    init_db(db_url)

    # Clear events
    if clear_all:
        count = clear_events()
        print(f"Cleared {count} events from the database")
    elif trace_id:
        count = clear_events(trace_id=trace_id)
        print(f"Cleared {count} events with trace ID {trace_id} from the database")
    else:
        print("Error: Must specify --trace-id or --all")


def main() -> None:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "server":
        asyncio.run(start_server(args.host, args.port))
    elif args.command == "client":
        asyncio.run(start_client(args.trace_id, args.url))
    elif args.command == "db":
        if args.db_command == "list":
            list_events(args.trace_id, args.limit, args.format)
        elif args.db_command == "clear":
            clear_db_events(args.trace_id, args.all)
        else:
            parser.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()