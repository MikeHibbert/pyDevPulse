"""Tests for DevPulse Huey integration."""

import unittest
from unittest.mock import patch, MagicMock

from huey import RedisHuey

from devpulse.integrations.huey import setup_huey_tracing, trace_task


class TestHueyIntegration(unittest.TestCase):
    """Test the Huey integration of DevPulse."""

    def setUp(self):
        """Set up the test environment."""
        # Create a Huey instance
        self.huey = RedisHuey('test_app', fake=True)  # Use fake mode for testing

    @patch('devpulse.integrations.huey.logger')
    def test_setup_huey_tracing(self, mock_logger):
        """Test setting up Huey tracing."""
        # Store original task method
        original_task = self.huey.task
        
        # Setup tracing
        setup_huey_tracing(self.huey)
        
        # Verify that task method was replaced
        self.assertNotEqual(original_task, self.huey.task)
        
        # Verify that logger was called
        mock_logger.info.assert_called_with("DevPulse tracing set up for Huey")

    @patch('devpulse.integrations.huey.set_trace_id')
    @patch('devpulse.integrations.huey.logger')
    def test_task_execution(self, mock_logger, mock_set_trace_id):
        """Test task execution with tracing."""
        # Mock trace ID
        mock_set_trace_id.return_value = "test-trace-id"
        
        # Setup tracing
        setup_huey_tracing(self.huey)
        
        # Define a task
        @self.huey.task()
        def test_task(x, y):
            return x + y
        
        # Execute the task
        result = test_task(2, 3)
        
        # Execute the task immediately (since we're using fake mode)
        result = result.get(blocking=True)
        
        # Verify the result
        self.assertEqual(result, 5)
        
        # Verify that logger was called for task start and completion
        self.assertEqual(mock_logger.info.call_count, 3)  # setup + start + completion

    @patch('devpulse.integrations.huey.set_trace_id')
    @patch('devpulse.integrations.huey.logger')
    def test_task_failure(self, mock_logger, mock_set_trace_id):
        """Test task failure with tracing."""
        # Mock trace ID
        mock_set_trace_id.return_value = "test-trace-id"
        
        # Setup tracing
        setup_huey_tracing(self.huey)
        
        # Define a task that raises an exception
        @self.huey.task()
        def failing_task():
            raise ValueError("Test error")
        
        # Execute the task
        result = failing_task()
        
        # Execute the task immediately (since we're using fake mode)
        with self.assertRaises(ValueError):
            result.get(blocking=True)
        
        # Verify that logger was called for task start and failure
        mock_logger.info.assert_any_call(
            "DevPulse tracing set up for Huey",
            extra=None
        )
        mock_logger.error.assert_called()

    @patch('devpulse.integrations.huey.set_trace_id')
    @patch('devpulse.integrations.huey.logger')
    def test_trace_task_decorator(self, mock_logger, mock_set_trace_id):
        """Test the trace_task decorator."""
        # Mock trace ID
        mock_set_trace_id.return_value = "test-trace-id"
        
        # Define a task with the decorator
        @trace_task
        def test_task(x, y):
            return x + y
        
        # Execute the task
        result = test_task(2, 3)
        
        # Verify the result
        self.assertEqual(result, 5)
        
        # Verify that trace ID was set
        mock_set_trace_id.assert_called_once_with(None)

    @patch('devpulse.integrations.huey.set_trace_id')
    @patch('devpulse.integrations.huey.logger')
    def test_trace_task_decorator_with_exception(self, mock_logger, mock_set_trace_id):
        """Test the trace_task decorator with an exception."""
        # Mock trace ID
        mock_set_trace_id.return_value = "test-trace-id"
        
        # Define a task with the decorator that raises an exception
        @trace_task
        def failing_task():
            raise ValueError("Test error")
        
        # Execute the task
        with self.assertRaises(ValueError):
            failing_task()
        
        # Verify that trace ID was set
        mock_set_trace_id.assert_called_once_with(None)
        
        # Verify that logger was called for the exception
        mock_logger.exception.assert_called()


if __name__ == "__main__":
    unittest.main()