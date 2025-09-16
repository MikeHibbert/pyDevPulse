"""Tests for DevPulse core functionality."""

import unittest
from unittest.mock import patch, MagicMock

from devpulse.core import (
    init, generate_trace_id, get_trace_id, set_trace_id, get_config, is_initialized
)


class TestCore(unittest.TestCase):
    """Test the core functionality of DevPulse."""

    def setUp(self):
        """Set up the test environment."""
        # Reset the global configuration
        from devpulse.core import _config, _initialized
        _config.clear()
        _initialized.set(False)

    def test_init(self):
        """Test initialization of DevPulse."""
        # Test with default values
        init()
        config = get_config()
        self.assertTrue(is_initialized())
        self.assertIsNone(config.get("websocket_url"))
        self.assertFalse(config.get("enable_db_logging"))
        self.assertEqual(config.get("environment"), "dev")

        # Reset
        self.setUp()

        # Test with custom values
        init(
            websocket_url="ws://example.com/ws",
            enable_db_logging=True,
            db_url="sqlite:///test.db",
            environment="test"
        )
        config = get_config()
        self.assertTrue(is_initialized())
        self.assertEqual(config.get("websocket_url"), "ws://example.com/ws")
        self.assertTrue(config.get("enable_db_logging"))
        self.assertEqual(config.get("db_url"), "sqlite:///test.db")
        self.assertEqual(config.get("environment"), "test")

    def test_trace_id(self):
        """Test trace ID generation and management."""
        # Generate a trace ID
        trace_id = generate_trace_id()
        self.assertIsNotNone(trace_id)
        self.assertIsInstance(trace_id, str)
        self.assertEqual(len(trace_id), 36)  # UUID4 length

        # Set and get trace ID
        set_trace_id(trace_id)
        self.assertEqual(get_trace_id(), trace_id)

        # Test with a different trace ID
        new_trace_id = "test-trace-id"
        set_trace_id(new_trace_id)
        self.assertEqual(get_trace_id(), new_trace_id)

    @patch("devpulse.core.logger")
    def test_init_with_logging(self, mock_logger):
        """Test initialization with logging."""
        init(websocket_url="ws://example.com/ws")
        mock_logger.info.assert_called_with("DevPulse initialized with config: {'websocket_url': 'ws://example.com/ws', 'enable_db_logging': False, 'environment': 'dev'}")

    def test_get_trace_id_not_set(self):
        """Test getting trace ID when not set."""
        # Should return None when not set
        self.assertIsNone(get_trace_id())


if __name__ == "__main__":
    unittest.main()