"""DevPulse: A reusable development tool for tracking errors and data flow across backend systems in real-time."""

from .core import init, get_trace_id, set_trace_id, generate_trace_id
from .version import __version__

__all__ = [
    "init",
    "get_trace_id",
    "set_trace_id",
    "generate_trace_id",
    "__version__",
]

def main():
    """Entry point for the CLI."""
    from .cli import main as cli_main
    cli_main()