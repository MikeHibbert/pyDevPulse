# DevPulse

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

DevPulse is a distributed tracing and error tracking system for Python applications. It helps you monitor and debug your applications by tracking errors and data flow across different services.

## Features

- **Distributed Tracing**: Track requests across multiple services with trace IDs
- **Real-time Monitoring**: Stream events to a WebSocket server for real-time monitoring
- **Error Tracking**: Capture errors with context, local variables, and stack traces
- **Framework Integrations**: Ready-to-use integrations for FastAPI, Celery, and Huey
- **Database Logging**: Persist events to SQLite or PostgreSQL for later analysis
- **Command-line Interface**: Interact with DevPulse from the terminal

A reusable development tool for Python applications, designed to simplify debugging by tracking errors and data flow across backend systems in real-time.

## Features

- Trace ID propagation across backend systems and Celery tasks
- Real-time event and error capture
- WebSocket streaming for live debugging
- Optional persistent event logging
- Data flow tracking at system boundaries

## Installation

```bash
pip install devpulse
```

## Quick Start

```python
import devpulse

# Initialize DevPulse with default Docker WebSocket URL (ws://localhost:8008)
devpulse.init()

# For FastAPI integration
from fastapi import FastAPI
from devpulse.integrations import add_devpulse_middleware

app = FastAPI()
add_devpulse_middleware(app)

# For Celery integration
from devpulse.integrations import setup_celery_tracing

setup_celery_tracing(celery_app)
```

## Docker Support

DevPulse includes Docker support for running the WebSocket server on port 8008 and the web UI on port 8088:

```bash
# Start the WebSocket server and web UI
docker-compose up -d
```

## Web UI

DevPulse provides a web-based user interface for viewing traces and events:

- Access the web UI at http://localhost:8088
- View all traces in a single dashboard
- Inspect individual trace details and events

## API Endpoints

DevPulse offers API endpoints for programmatic access to trace data:

- `/api/traces/{trace_id}` - Get all events for a specific trace ID
- `/api/traces/{trace_id}/timeline` - Get a timeline of events organized by stages with duration and status information

See the [usage documentation](docs/usage.md) for more details.

## Documentation

For detailed documentation and examples, see the [docs](docs/).

## License

MIT