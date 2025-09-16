"""Tests for DevPulse Celery integration."""

import unittest
from unittest.mock import patch, MagicMock

from celery import Celery
from celery.signals import task_prerun, task_postrun, task_success, task_failure

from devpulse.integrations.celery import setup_celery_tracing, trace_task


class TestCeleryIntegration(unittest.TestCase):
    """Test the Celery integration of DevPulse."""

    def setUp(self):
        """Set up the test environment."""
        # Create a Celery app
        self.app = Celery("test_app")
        self.app.conf.update(
            task_serializer="json",
            accept_content=["json"],
            result_serializer="json",
            broker_url="memory://",
            result_backend="rpc://",
            task_always_eager=True,
        )

    @patch("devpulse.integrations.celery.get_trace_id")
    @patch("devpulse.integrations.celery.set_trace_id")
    @patch("devpulse.integrations.celery.logger")
    def test_task_prerun_handler(self, mock_logger, mock_set_trace_id, mock_get_trace_id):
        """Test the task_prerun handler."""
        # Mock trace ID
        mock_get_trace_id.return_value = None

        # Setup tracing
        setup_celery_tracing(self.app)

        # Create a task
        @self.app.task
        def test_task():
            return "test"

        # Create a sender
        sender = MagicMock()
        sender.name = "test_task"

        # Create task_id
        task_id = "test-task-id"

        # Create args and kwargs
        args = (1, 2, 3)
        kwargs = {"a": 1, "b": 2}

        # Create headers with trace ID
        headers = {"X-Trace-ID": "test-trace-id"}

        # Create request
        request = MagicMock()
        request.headers = headers

        # Call the handler
        task_prerun.send(
            sender=sender,
            task_id=task_id,
            task=sender,
            args=args,
            kwargs=kwargs,
            request=request
        )

        # Check that trace ID was set
        mock_set_trace_id.assert_called_once_with("test-trace-id")

        # Check that the task was logged
        mock_logger.info.assert_called_once()

    @patch("devpulse.integrations.celery.get_trace_id")
    @patch("devpulse.integrations.celery.logger")
    def test_task_postrun_handler(self, mock_logger, mock_get_trace_id):
        """Test the task_postrun handler."""
        # Mock trace ID
        mock_get_trace_id.return_value = "test-trace-id"

        # Setup tracing
        setup_celery_tracing(self.app)

        # Create a task
        @self.app.task
        def test_task():
            return "test"

        # Create a sender
        sender = MagicMock()
        sender.name = "test_task"

        # Create task_id
        task_id = "test-task-id"

        # Create args and kwargs
        args = (1, 2, 3)
        kwargs = {"a": 1, "b": 2}

        # Create state
        state = "SUCCESS"

        # Call the handler
        task_postrun.send(
            sender=sender,
            task_id=task_id,
            task=sender,
            args=args,
            kwargs=kwargs,
            state=state
        )

        # Check that the task was logged
        mock_logger.info.assert_called_once()

    @patch("devpulse.integrations.celery.get_trace_id")
    @patch("devpulse.integrations.celery.logger")
    def test_task_success_handler(self, mock_logger, mock_get_trace_id):
        """Test the task_success handler."""
        # Mock trace ID
        mock_get_trace_id.return_value = "test-trace-id"

        # Setup tracing
        setup_celery_tracing(self.app)

        # Create a task
        @self.app.task
        def test_task():
            return "test"

        # Create a sender
        sender = MagicMock()
        sender.name = "test_task"

        # Create result
        result = "test-result"

        # Call the handler
        task_success.send(
            sender=sender,
            result=result
        )

        # Check that the task was logged
        mock_logger.info.assert_called_once()

    @patch("devpulse.integrations.celery.get_trace_id")
    @patch("devpulse.integrations.celery.logger")
    def test_task_failure_handler(self, mock_logger, mock_get_trace_id):
        """Test the task_failure handler."""
        # Mock trace ID
        mock_get_trace_id.return_value = "test-trace-id"

        # Setup tracing
        setup_celery_tracing(self.app)

        # Create a task
        @self.app.task
        def test_task():
            return "test"

        # Create a sender
        sender = MagicMock()
        sender.name = "test_task"

        # Create exception
        exception = ValueError("test-error")

        # Create traceback
        traceback = MagicMock()

        # Call the handler
        task_failure.send(
            sender=sender,
            exception=exception,
            traceback=traceback
        )

        # Check that the task was logged
        mock_logger.error.assert_called_once()

    @patch("devpulse.integrations.celery.get_trace_id")
    @patch("devpulse.integrations.celery.set_trace_id")
    @patch("devpulse.integrations.celery.logger")
    def test_trace_task_decorator(self, mock_logger, mock_set_trace_id, mock_get_trace_id):
        """Test the trace_task decorator."""
        # Mock trace ID
        mock_get_trace_id.return_value = None

        # Create a task with the decorator
        @self.app.task
        @trace_task
        def test_task(a, b):
            return a + b

        # Call the task
        result = test_task(1, 2)

        # Check the result
        self.assertEqual(result, 3)

        # Check that the task was logged
        mock_logger.info.assert_called()


if __name__ == "__main__":
    unittest.main()