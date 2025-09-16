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

# Initialize DevPulse with WebSocket URL
devpulse.init(websocket_url="ws://localhost:8000/ws")

# For FastAPI integration
from fastapi import FastAPI
from devpulse.integrations import add_devpulse_middleware

app = FastAPI()
add_devpulse_middleware(app)

# For Celery integration
from devpulse.integrations import setup_celery_tracing

setup_celery_tracing(celery_app)
```

## Documentation

For detailed documentation and examples, see the [docs](docs/).

## License

MIT