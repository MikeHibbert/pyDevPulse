"""Tests for DevPulse WebSocket functionality."""

import asyncio
import json
import unittest
from unittest.mock import patch, MagicMock, AsyncMock

from devpulse.websocket import (
    connect, process_queue, send_event, start_server, broadcast_event
)


class TestWebSocket(unittest.TestCase):
    """Test the WebSocket functionality of DevPulse."""

    @patch("devpulse.websocket.websockets.connect")
    @patch("devpulse.websocket.logger")
    def test_connect(self, mock_logger, mock_connect):
        """Test connecting to a WebSocket server."""
        # Mock websocket
        mock_websocket = AsyncMock()
        mock_connect.return_value.__aenter__.return_value = mock_websocket

        # Run the connect function
        asyncio.run(connect("ws://example.com/ws"))

        # Check that the connection was made
        mock_connect.assert_called_once_with("ws://example.com/ws")
        mock_logger.info.assert_called_once_with("Connected to WebSocket server: ws://example.com/ws")

    @patch("devpulse.websocket.asyncio.Queue")
    @patch("devpulse.websocket.connect")
    @patch("devpulse.websocket.logger")
    def test_process_queue(self, mock_logger, mock_connect, mock_queue_class):
        """Test processing the event queue."""
        # Mock queue
        mock_queue = AsyncMock()
        mock_queue_class.return_value = mock_queue

        # Mock websocket
        mock_websocket = AsyncMock()
        mock_connect.return_value = mock_websocket

        # Mock event
        event = {"traceId": "test-trace-id", "details": "Test event"}
        mock_queue.get.side_effect = [event, asyncio.CancelledError]

        # Run the process_queue function
        with self.assertRaises(asyncio.CancelledError):
            asyncio.run(process_queue("ws://example.com/ws"))

        # Check that the event was sent
        mock_websocket.send.assert_called_once_with(json.dumps(event))
        mock_logger.info.assert_called_with("Sent event to WebSocket server: {'traceId': 'test-trace-id', 'details': 'Test event'}")

    @patch("devpulse.websocket._event_queue")
    @patch("devpulse.websocket.is_initialized")
    @patch("devpulse.websocket.get_config")
    @patch("devpulse.websocket.logger")
    def test_send_event(self, mock_logger, mock_get_config, mock_is_initialized, mock_event_queue):
        """Test sending an event."""
        # Mock initialization
        mock_is_initialized.return_value = True

        # Mock config
        mock_get_config.return_value = {"websocket_url": "ws://example.com/ws"}

        # Mock event queue
        mock_event_queue.put_nowait = MagicMock()

        # Send an event
        event = {"traceId": "test-trace-id", "details": "Test event"}
        send_event(event)

        # Check that the event was added to the queue
        mock_event_queue.put_nowait.assert_called_once_with(event)

    @patch("devpulse.websocket.websockets.serve")
    @patch("devpulse.websocket.logger")
    def test_start_server(self, mock_logger, mock_serve):
        """Test starting a WebSocket server."""
        # Mock server
        mock_server = AsyncMock()
        mock_serve.return_value.__aenter__.return_value = mock_server

        # Create a future that will never complete
        future = asyncio.Future()

        # Mock asyncio.Future to return our future
        with patch("devpulse.websocket.asyncio.Future", return_value=future):
            # Run the start_server function with a timeout
            with self.assertRaises(asyncio.TimeoutError):
                asyncio.run(asyncio.wait_for(start_server("localhost", 8000), 0.1))

        # Check that the server was started
        mock_serve.assert_called_once()
        mock_logger.info.assert_called_once_with("WebSocket server started at ws://localhost:8000")

    @patch("devpulse.websocket._clients")
    @patch("devpulse.websocket.logger")
    def test_broadcast_event(self, mock_logger, mock_clients):
        """Test broadcasting an event."""
        # Mock clients
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()
        mock_clients.get.return_value = {mock_websocket1, mock_websocket2}

        # Create an event
        event = {"traceId": "test-trace-id", "details": "Test event"}

        # Broadcast the event
        asyncio.run(broadcast_event(event))

        # Check that the event was sent to all clients
        mock_websocket1.send.assert_called_once_with(json.dumps(event))
        mock_websocket2.send.assert_called_once_with(json.dumps(event))


if __name__ == "__main__":
    unittest.main()