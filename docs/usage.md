# DevPulse Usage Guide

This guide explains how to use DevPulse to track errors and data flow across your Python applications.

## Installation

Install DevPulse using pip:

```bash
pip install devpulse
```

## Basic Setup

Initialize DevPulse in your application:

```python
import devpulse

# Initialize with default Docker WebSocket URL (ws://localhost:8008)
devpulse.init()

# Or specify a custom WebSocket URL
devpulse.init(websocket_url="ws://localhost:8000/ws")
```

## Docker WebSocket Server and Web UI

DevPulse includes Docker support for running both the WebSocket server and web UI. This allows you to run the WebSocket server in a container on port 8008 (the default URL that DevPulse will connect to) and the web UI on port 8088.

### Running with Docker Compose

```bash
# Start the WebSocket server and web UI
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the server
docker-compose down
```

### Accessing the Web UI

Once the Docker container is running, you can access the web UI at:

```
http://localhost:8088
```

The web UI provides a dashboard to view all traces and their events, making it easier to debug and monitor your application.

### Building and Running Manually

```bash
# Build the Docker image
docker build -f Dockerfile.websocket -t devpulse-websocket .

# Run the container
docker run -d -p 8008:8008 -p 8088:8088 --name devpulse-websocket devpulse-websocket
```

## API Endpoints

DevPulse provides API endpoints for programmatic access to trace data:

### Get Events for a Trace ID

```
GET /api/traces/{trace_id}
```

Returns all events associated with the specified trace ID.

Example response:
```json
{
  "trace_id": "abc123",
  "events": [
    {
      "id": 1,
      "trace_id": "abc123",
      "system": "api",
      "event_type": "request",
      "timestamp": "2023-01-01T12:00:00Z",
      "data": {...}
    },
    ...
  ]
}
```

### Get Timeline for a Trace ID

```
GET /api/traces/{trace_id}/timeline
```

Returns a timeline of events organized by stages with duration and status information.

Example response:
```json
{
  "trace_id": "abc123",
  "stages": [
    {
      "system": "api",
      "start_time": "2023-01-01T12:00:00Z",
      "end_time": "2023-01-01T12:00:01Z",
      "duration_ms": 1000,
      "status": "success",
      "event_count": 3,
      "events": [...]
    },
    {
      "system": "worker",
      "start_time": "2023-01-01T12:00:01Z",
      "end_time": "2023-01-01T12:00:03Z",
      "duration_ms": 2000,
      "status": "error",
      "event_count": 2,
      "events": [...]
    }
  ],
  "total_stages": 2,
  "has_errors": true,
  "total_duration_ms": 3000
}
```

## Trace ID Propagation

DevPulse uses trace IDs to correlate events across different parts of your application. You can get and set trace IDs manually:

```python
# Generate a new trace ID
trace_id = devpulse.generate_trace_id()

# Set the trace ID in the current context
devpulse.set_trace_id(trace_id)

# Get the current trace ID
current_trace_id = devpulse.get_trace_id()
```

## FastAPI Integration

Add DevPulse middleware to your FastAPI application:

```python
from fastapi import FastAPI
from devpulse.integrations import add_devpulse_middleware

app = FastAPI()
add_devpulse_middleware(app)
```

The middleware will:

1. Extract trace ID from request headers or generate a new one
2. Add trace ID to response headers
3. Log request and response details
4. Capture errors and local variables

## Celery Integration

Set up DevPulse tracing for your Celery application:

```python
from celery import Celery
from devpulse.integrations import setup_celery_tracing

app = Celery(...)
setup_celery_tracing(app)
```

This will:

1. Connect signal handlers to Celery signals
2. Capture task execution details
3. Propagate trace IDs across tasks

## Huey Integration

Set up DevPulse tracing for your Huey application:

```python
from huey import RedisHuey
from devpulse.integrations import setup_huey_tracing

huey = RedisHuey('tasks')
setup_huey_tracing(huey)
```

This will:

1. Override Huey's task decorator to add tracing hooks
2. Capture task execution details including start, completion, and failures
3. Propagate trace IDs across tasks

## WebSocket Server

DevPulse includes a WebSocket server for real-time event streaming. Start the server:

```bash
python -m devpulse.websocket_server
```

Or run the example server:

```bash
python examples/websocket_server.py
```

## Database Logging

Enable database logging for persistent event storage:

```python
import devpulse

devpulse.init(
    websocket_url="ws://localhost:8000/ws",
    enable_db_logging=True,
    db_url="sqlite:///devpulse.db",  # or "postgresql://user:password@localhost/devpulse"
)
```

## Event Format

DevPulse events are formatted as JSON with the following structure:

```json
{
  "traceId": "trace-123",
  "timestamp": "2025-09-16T07:12:00Z",
  "severity": "error|warning|info",
  "system": "backend|celery|database",
  "file": "app.py",
  "line": 42,
  "source": "function foo()",
  "locals": { "var": "value" },
  "stacktrace": ["line1", "line2"],
  "response": "success|fail",
  "details": "Database insert failed",
  "environment": "dev"
}
```

## Examples

See the `examples` directory for complete examples:

- `fastapi_example.py`: FastAPI integration
- `celery_example.py`: Celery integration
- `websocket_server.py`: WebSocket server
- `websocket_client.py`: WebSocket client

## Advanced Configuration

### Custom Logging

DevPulse uses Python's logging module. You can configure it to your needs:

```python
import logging

# Configure root logger
logging.basicConfig(level=logging.INFO)

# Configure DevPulse logger
logger = logging.getLogger("devpulse")
logger.setLevel(logging.DEBUG)
```

### Environment Configuration

Specify the environment when initializing DevPulse:

```python
devpulse.init(
    websocket_url="ws://localhost:8000/ws",
    environment="dev"  # or "staging", "prod"
)
```

## Troubleshooting

### WebSocket Connection Issues

If you're having trouble connecting to the WebSocket server:

1. Make sure the server is running
2. Check that the WebSocket URL is correct
3. Verify that there are no firewall or network issues

### Missing Events

If events are not being captured:

1. Check that DevPulse is properly initialized
2. Verify that the trace ID is being propagated
3. Check the logging configuration

## Best Practices

1. Initialize DevPulse early in your application
2. Use middleware for automatic trace ID propagation
3. Add trace IDs to external API calls
4. Use descriptive log messages
5. Include relevant context in log messages