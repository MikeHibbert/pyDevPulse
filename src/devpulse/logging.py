"""Logging functionality for DevPulse."""

import json
import logging
import sys
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List

from .core import get_trace_id, get_config
from .websocket import send_event


class DevPulseHandler(logging.Handler):
    """Custom logging handler for DevPulse.

    This handler captures log records, formats them as JSON, and sends them
    to the WebSocket server for real-time streaming.
    """

    def __init__(self, level=logging.NOTSET):
        super().__init__(level)
        self.setFormatter(logging.Formatter("%(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        """Process a log record and send it to the WebSocket server.

        Args:
            record: The log record to process
        """
        try:
            # Get trace ID from context or use empty string
            trace_id = get_trace_id()
            if not trace_id:
                # Skip records without trace ID
                return

            # Extract exception info if available
            exc_info = sys.exc_info() if record.exc_info else None
            locals_dict = {}
            stacktrace = []

            if exc_info and exc_info[0]:
                # Extract locals from traceback frames
                tb = exc_info[2]
                while tb:
                    frame = tb.tb_frame
                    for key, value in frame.f_locals.items():
                        try:
                            # Try to convert value to string, skip if not serializable
                            locals_dict[key] = str(value)
                        except Exception:
                            locals_dict[key] = "<not serializable>"
                    tb = tb.tb_next

                # Format stacktrace
                stacktrace = traceback.format_exception(*exc_info)

            # Create event payload
            event = {
                "traceId": trace_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "severity": record.levelname.lower(),
                "system": "backend",  # Default to backend, can be overridden
                "file": record.pathname,
                "line": record.lineno,
                "source": f"{record.module}.{record.funcName}",
                "locals": locals_dict,
                "stacktrace": stacktrace,
                "details": record.getMessage(),
                "environment": get_config().get("environment", "dev"),
            }

            # Send event to WebSocket server
            send_event(event)

            # If database logging is enabled, save to database
            if get_config().get("enable_db_logging", False):
                from .database import save_event
                save_event(event)

        except Exception as e:
            # Fallback to stderr if something goes wrong
            sys.stderr.write(f"DevPulse logging error: {str(e)}\n")


def setup_logging() -> None:
    """Set up DevPulse logging.

    This function adds a DevPulseHandler to the root logger and configures
    it to capture log records at the INFO level and above.
    """
    # Create DevPulse handler
    handler = DevPulseHandler()
    handler.setLevel(logging.INFO)

    # Add handler to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    # Create logger for DevPulse itself
    logger = logging.getLogger("devpulse")
    logger.setLevel(logging.INFO)

    # Log initialization
    logger.info("DevPulse logging initialized")