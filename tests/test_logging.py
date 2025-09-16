"""Tests for DevPulse logging functionality."""

import json
import logging
import unittest
from unittest.mock import patch, MagicMock

from devpulse.logging import DevPulseHandler, setup_logging


class TestLogging(unittest.TestCase):
    """Test the logging functionality of DevPulse."""

    def setUp(self):
        """Set up the test environment."""
        # Reset the root logger
        root = logging.getLogger()
        for handler in root.handlers[:]:  # Make a copy of the list
            root.removeHandler(handler)
        root.setLevel(logging.INFO)

        # Reset the DevPulse logger
        logger = logging.getLogger("devpulse")
        for handler in logger.handlers[:]:  # Make a copy of the list
            logger.removeHandler(handler)
        logger.setLevel(logging.INFO)

    @patch("devpulse.logging.websocket")
    @patch("devpulse.logging.database")
    def test_handler_init(self, mock_database, mock_websocket):
        """Test initialization of DevPulseHandler."""
        # Test with default values
        handler = DevPulseHandler()
        self.assertEqual(handler.level, logging.INFO)
        self.assertFalse(handler.save_to_db)

        # Test with custom values
        handler = DevPulseHandler(
            level=logging.DEBUG,
            save_to_db=True
        )
        self.assertEqual(handler.level, logging.DEBUG)
        self.assertTrue(handler.save_to_db)

    @patch("devpulse.logging.websocket")
    @patch("devpulse.logging.database")
    @patch("devpulse.logging.get_trace_id")
    def test_handler_emit(self, mock_get_trace_id, mock_database, mock_websocket):
        """Test emitting log records."""
        # Mock trace ID
        mock_get_trace_id.return_value = "test-trace-id"

        # Create handler
        handler = DevPulseHandler(save_to_db=True)

        # Create log record
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )

        # Emit record
        handler.emit(record)

        # Check that the record was sent to WebSocket
        mock_websocket.send_event.assert_called_once()
        event = mock_websocket.send_event.call_args[0][0]
        self.assertEqual(event["traceId"], "test-trace-id")
        self.assertEqual(event["severity"], "error")
        self.assertEqual(event["details"], "Test message")
        self.assertEqual(event["file"], "test.py")
        self.assertEqual(event["line"], 42)

        # Check that the record was saved to database
        mock_database.save_event.assert_called_once()
        event = mock_database.save_event.call_args[0][0]
        self.assertEqual(event["traceId"], "test-trace-id")
        self.assertEqual(event["severity"], "error")
        self.assertEqual(event["details"], "Test message")
        self.assertEqual(event["file"], "test.py")
        self.assertEqual(event["line"], 42)

    @patch("devpulse.logging.DevPulseHandler")
    def test_setup_logging(self, mock_handler_class):
        """Test setting up logging."""
        # Mock handler
        mock_handler = MagicMock()
        mock_handler_class.return_value = mock_handler

        # Setup logging
        setup_logging(level=logging.DEBUG, save_to_db=True)

        # Check that the handler was created with the right parameters
        mock_handler_class.assert_called_once_with(
            level=logging.DEBUG,
            save_to_db=True
        )

        # Check that the handler was added to the logger
        logger = logging.getLogger("devpulse")
        self.assertIn(mock_handler, logger.handlers)


if __name__ == "__main__":
    unittest.main()