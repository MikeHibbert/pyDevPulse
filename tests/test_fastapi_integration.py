"""Tests for DevPulse FastAPI integration."""

import unittest
from unittest.mock import patch, MagicMock

from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient

from devpulse.integrations.fastapi import (
    DevPulseMiddleware, add_devpulse_middleware, DevPulseAPIRoute, add_devpulse_routes
)


class TestFastAPIIntegration(unittest.TestCase):
    """Test the FastAPI integration of DevPulse."""

    def setUp(self):
        """Set up the test environment."""
        # Create a FastAPI app
        self.app = FastAPI()

        # Add a test route
        @self.app.get("/test")
        def test_route():
            return {"message": "Hello, world!"}

        # Add a test route with parameters
        @self.app.get("/test/{param}")
        def test_route_with_param(param: str, query: str = None):
            return {"param": param, "query": query}

        # Add a test route that raises an exception
        @self.app.get("/error")
        def test_error_route():
            raise ValueError("Test error")

    @patch("devpulse.integrations.fastapi.get_trace_id")
    @patch("devpulse.integrations.fastapi.set_trace_id")
    @patch("devpulse.integrations.fastapi.generate_trace_id")
    @patch("devpulse.integrations.fastapi.logger")
    def test_middleware(self, mock_logger, mock_generate_trace_id, mock_set_trace_id, mock_get_trace_id):
        """Test the DevPulse middleware."""
        # Mock trace ID
        mock_generate_trace_id.return_value = "test-trace-id"
        mock_get_trace_id.return_value = "test-trace-id"

        # Add middleware
        self.app.add_middleware(DevPulseMiddleware)

        # Create test client
        client = TestClient(self.app)

        # Test request
        response = client.get("/test")

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Hello, world!"})

        # Check trace ID
        self.assertEqual(response.headers.get("X-Trace-ID"), "test-trace-id")

        # Check that trace ID was set
        mock_set_trace_id.assert_called_once_with("test-trace-id")

        # Check that the request was logged
        mock_logger.info.assert_called()

    @patch("devpulse.integrations.fastapi.get_trace_id")
    @patch("devpulse.integrations.fastapi.set_trace_id")
    @patch("devpulse.integrations.fastapi.generate_trace_id")
    @patch("devpulse.integrations.fastapi.logger")
    def test_middleware_with_existing_trace_id(self, mock_logger, mock_generate_trace_id, mock_set_trace_id, mock_get_trace_id):
        """Test the DevPulse middleware with an existing trace ID."""
        # Mock trace ID
        mock_get_trace_id.return_value = None

        # Add middleware
        self.app.add_middleware(DevPulseMiddleware)

        # Create test client
        client = TestClient(self.app)

        # Test request with trace ID
        response = client.get("/test", headers={"X-Trace-ID": "existing-trace-id"})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Hello, world!"})

        # Check trace ID
        self.assertEqual(response.headers.get("X-Trace-ID"), "existing-trace-id")

        # Check that trace ID was set
        mock_set_trace_id.assert_called_once_with("existing-trace-id")

        # Check that the request was logged
        mock_logger.info.assert_called()

    @patch("devpulse.integrations.fastapi.get_trace_id")
    @patch("devpulse.integrations.fastapi.set_trace_id")
    @patch("devpulse.integrations.fastapi.generate_trace_id")
    @patch("devpulse.integrations.fastapi.logger")
    def test_middleware_with_error(self, mock_logger, mock_generate_trace_id, mock_set_trace_id, mock_get_trace_id):
        """Test the DevPulse middleware with an error."""
        # Mock trace ID
        mock_generate_trace_id.return_value = "test-trace-id"
        mock_get_trace_id.return_value = "test-trace-id"

        # Add middleware
        self.app.add_middleware(DevPulseMiddleware)

        # Create test client
        client = TestClient(self.app)

        # Test request with error
        with self.assertRaises(ValueError):
            client.get("/error")

        # Check that the error was logged
        mock_logger.error.assert_called()

    @patch("devpulse.integrations.fastapi.DevPulseMiddleware")
    def test_add_devpulse_middleware(self, mock_middleware_class):
        """Test adding DevPulse middleware."""
        # Mock middleware
        mock_middleware = MagicMock()
        mock_middleware_class.return_value = mock_middleware

        # Add middleware
        add_devpulse_middleware(self.app)

        # Check that the middleware was added
        self.app.user_middleware.append({
            "middleware": mock_middleware_class,
            "kwargs": {}
        })

    def test_api_route(self):
        """Test the DevPulse API route."""
        # Create a FastAPI app with DevPulse routes
        app = FastAPI()
        app.router.route_class = DevPulseAPIRoute

        # Add a test route
        @app.get("/test")
        def test_route():
            return {"message": "Hello, world!"}

        # Create test client
        client = TestClient(app)

        # Test request
        response = client.get("/test")

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Hello, world!"})

    def test_add_devpulse_routes(self):
        """Test adding DevPulse routes."""
        # Add DevPulse routes
        add_devpulse_routes(self.app)

        # Check that the route class was changed
        self.assertEqual(self.app.router.route_class, DevPulseAPIRoute)


if __name__ == "__main__":
    unittest.main()