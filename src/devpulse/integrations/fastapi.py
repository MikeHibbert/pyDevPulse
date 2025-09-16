"""FastAPI integration for DevPulse."""

import inspect
import json
import logging
import time
from typing import Callable, Dict, Any, Optional

from fastapi import FastAPI, Request, Response
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..core import get_trace_id, set_trace_id

# Setup logger
logger = logging.getLogger("devpulse.integrations.fastapi")


class DevPulseMiddleware(BaseHTTPMiddleware):
    """Middleware for FastAPI integration with DevPulse.

    This middleware captures request and response details, sets trace ID,
    and logs events for each request.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process a request and capture details for DevPulse.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            The response from the next middleware or route handler
        """
        # Get trace ID from header or generate a new one
        trace_id = request.headers.get("X-Trace-ID")
        trace_id = set_trace_id(trace_id)

        # Add trace ID to response headers
        start_time = time.time()
        response = None
        status_code = 500  # Default to error

        try:
            # Process request
            response = await call_next(request)
            status_code = response.status_code

            # Add trace ID to response headers
            response.headers["X-Trace-ID"] = trace_id

            return response
        except Exception as e:
            # Log exception
            logger.exception(f"Error processing request: {str(e)}")
            raise
        finally:
            # Calculate request duration
            duration = time.time() - start_time

            # Get request details
            method = request.method
            url = str(request.url)
            client = request.client.host if request.client else "unknown"

            # Log request details
            logger.info(
                f"Request: {method} {url} from {client} - {status_code} in {duration:.3f}s",
                extra={
                    "trace_id": trace_id,
                    "method": method,
                    "url": url,
                    "client": client,
                    "status_code": status_code,
                    "duration": duration,
                    "response": "success" if status_code < 400 else "fail",
                },
            )


def add_devpulse_middleware(app: FastAPI) -> None:
    """Add DevPulse middleware to a FastAPI application.

    Args:
        app: The FastAPI application
    """
    # Add middleware
    app.add_middleware(DevPulseMiddleware)

    # Log initialization
    logger.info("DevPulse middleware added to FastAPI application")


class DevPulseAPIRoute(APIRoute):
    """Custom API route for DevPulse integration.

    This route captures function arguments and return values for each endpoint.
    """

    async def app(self, scope, receive, send) -> None:
        """Process a request and capture details for DevPulse.

        Args:
            scope: The ASGI scope
            receive: The ASGI receive function
            send: The ASGI send function
        """
        # Get trace ID from context or generate a new one
        trace_id = get_trace_id()
        if not trace_id:
            trace_id = set_trace_id()

        # Process request
        await super().app(scope, receive, send)


def add_devpulse_routes(app: FastAPI) -> None:
    """Add DevPulse routes to a FastAPI application.

    This function replaces the default APIRoute with DevPulseAPIRoute
    for all routes in the application.

    Args:
        app: The FastAPI application
    """
    # Replace default route class
    app.router.route_class = DevPulseAPIRoute

    # Log initialization
    logger.info("DevPulse routes added to FastAPI application")