"""Core functionality for TraceFlow."""

import contextvars
import logging
import uuid
from typing import Dict, Optional, Any, Union

# Context variable for trace ID propagation
trace_id_var = contextvars.ContextVar[str]("trace_id", default="")

# Global configuration
_config: Dict[str, Any] = {
    "websocket_url": None,
    "enable_db_logging": False,
    "db_url": None,
    "environment": "dev",
    "initialized": False,
}

# Setup logger
logger = logging.getLogger("traceflow")


def init(
    websocket_url: str,
    enable_db_logging: bool = False,
    db_url: Optional[str] = None,
    environment: str = "dev",
) -> None:
    """Initialize TraceFlow with configuration options.

    Args:
        websocket_url: URL for the WebSocket server
        enable_db_logging: Whether to enable database logging
        db_url: Database URL for persistent logging
        environment: Environment name (dev, staging, prod)
    """
    global _config
    _config["websocket_url"] = websocket_url
    _config["enable_db_logging"] = enable_db_logging
    _config["db_url"] = db_url
    _config["environment"] = environment
    _config["initialized"] = True

    # Setup logging handlers
    from .logging import setup_logging
    setup_logging()

    logger.info(f"TraceFlow initialized with WebSocket URL: {websocket_url}")


def generate_trace_id() -> str:
    """Generate a unique trace ID.

    Returns:
        A unique trace ID as a string
    """
    return str(uuid.uuid4())


def get_trace_id() -> str:
    """Get the current trace ID from context.

    Returns:
        The current trace ID or empty string if not set
    """
    return trace_id_var.get()


def set_trace_id(trace_id: Optional[str] = None) -> str:
    """Set the trace ID in the current context.

    Args:
        trace_id: The trace ID to set, or None to generate a new one

    Returns:
        The trace ID that was set
    """
    if not trace_id:
        trace_id = generate_trace_id()
    trace_id_var.set(trace_id)
    return trace_id


def get_config() -> Dict[str, Any]:
    """Get the current configuration.

    Returns:
        The current configuration dictionary
    """
    return _config


def is_initialized() -> bool:
    """Check if TraceFlow has been initialized.

    Returns:
        True if initialized, False otherwise
    """
    return _config.get("initialized", False)