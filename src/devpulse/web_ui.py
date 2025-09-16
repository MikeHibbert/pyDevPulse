"""Web UI functionality for DevPulse."""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from .core import get_config
from .database import get_events, get_recent_trace_ids, init_database

# Setup logger
logger = logging.getLogger("devpulse.web_ui")

# Create FastAPI app
app = FastAPI(title="DevPulse", description="DevPulse Web UI")

# HTML templates for the web UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>DevPulse - Trace Viewer</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .search-form {
            background-color: #fff;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .search-form input[type="text"] {
            padding: 8px;
            width: 300px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .search-form button {
            padding: 8px 15px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .search-form button:hover {
            background-color: #45a049;
        }
        .events {
            background-color: #fff;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .event {
            padding: 15px;
            border-bottom: 1px solid #eee;
        }
        .event:last-child {
            border-bottom: none;
        }
        .event-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }
        .event-timestamp {
            color: #888;
            font-size: 0.9em;
        }
        .event-severity {
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.8em;
            font-weight: bold;
        }
        .severity-info {
            background-color: #e3f2fd;
            color: #0d47a1;
        }
        .severity-warning {
            background-color: #fff3e0;
            color: #e65100;
        }
        .severity-error {
            background-color: #ffebee;
            color: #b71c1c;
        }
        .event-details {
            margin-top: 10px;
            padding: 10px;
            background-color: #f9f9f9;
            border-radius: 4px;
            font-family: monospace;
            white-space: pre-wrap;
        }
        .no-events {
            padding: 20px;
            text-align: center;
            color: #888;
        }
        .event-system {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.8em;
            background-color: #e8eaf6;
            color: #3f51b5;
            margin-right: 10px;
        }
        .trace-list {
            background-color: #fff;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .trace-item {
            padding: 15px;
            border-bottom: 1px solid #eee;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        .trace-item:hover {
            background-color: #f8f9fa;
        }
        .trace-item:last-child {
            border-bottom: none;
        }
        .trace-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        .trace-id {
            font-family: monospace;
            font-weight: bold;
            color: #2196F3;
            font-size: 0.9em;
        }
        .trace-timestamp {
            color: #888;
            font-size: 0.85em;
        }
        .trace-info {
            display: flex;
            gap: 10px;
            align-items: center;
            font-size: 0.85em;
            color: #666;
        }
        .trace-count {
            background-color: #e3f2fd;
            color: #1976d2;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.8em;
        }
        .section-title {
            color: #333;
            margin-bottom: 15px;
            font-size: 1.2em;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>DevPulse - Trace Viewer</h1>
        
        <div class="search-form">
            <form action="/" method="get">
                <input type="text" name="trace_id" placeholder="Enter Trace ID" value="{{ trace_id or '' }}">
                <button type="submit">Search</button>
            </form>
        </div>
        
        {% if trace_id %}
            <!-- Show events for specific trace ID -->
            <div class="section-title">Events for Trace ID: {{ trace_id }}</div>
            <div class="events">
                {% if events %}
                    {% for event in events %}
                        <div class="event">
                            <div class="event-header">
                                <div>
                                    <span class="event-system">{{ event.system }}</span>
                                    <span class="event-severity severity-{{ event.severity }}">{{ event.severity }}</span>
                                </div>
                                <span class="event-timestamp">{{ event.timestamp }}</span>
                            </div>
                            <div>
                                <strong>{{ event.details }}</strong>
                            </div>
                            {% if event.locals or event.stacktrace %}
                                <div class="event-details">
                                    {% if event.locals %}
                                        <strong>Locals:</strong>
                                        {{ event.locals | tojson(indent=2) }}
                                    {% endif %}
                                    
                                    {% if event.stacktrace %}
                                        <strong>Stacktrace:</strong>
                                        {{ event.stacktrace | join('\n') }}
                                    {% endif %}
                                </div>
                            {% endif %}
                        </div>
                    {% endfor %}
                {% else %}
                    <div class="no-events">
                        No events found for trace ID: {{ trace_id }}
                    </div>
                {% endif %}
            </div>
        {% else %}
            <!-- Show recent trace IDs and events -->
            <div class="section-title">Recent Trace IDs</div>
            {% if recent_traces %}
                <div class="trace-list">
                    {% for trace in recent_traces %}
                        <div class="trace-item" onclick="window.location.href='/?trace_id={{ trace.trace_id }}'">
                            <div class="trace-header">
                                <span class="trace-id">{{ trace.trace_id }}</span>
                                <span class="trace-timestamp">{{ trace.latest_timestamp }}</span>
                            </div>
                            <div class="trace-info">
                                <span class="event-system">{{ trace.system }}</span>
                                <span class="trace-count">{{ trace.event_count }} events</span>
                                <span class="event-severity severity-{{ trace.event_type }}">{{ trace.event_type }}</span>
                            </div>
                        </div>
                    {% endfor %}
                </div>
            {% endif %}
            
            <div class="section-title">Recent Events (All Traces)</div>
            <div class="events">
                {% if recent_events %}
                    {% for event in recent_events %}
                        <div class="event">
                            <div class="event-header">
                                <div>
                                    <span class="trace-id" onclick="window.location.href='/?trace_id={{ event.traceId }}'" style="cursor: pointer; margin-right: 10px;">{{ event.traceId }}</span>
                                    <span class="event-system">{{ event.system }}</span>
                                    <span class="event-severity severity-{{ event.severity }}">{{ event.severity }}</span>
                                </div>
                                <span class="event-timestamp">{{ event.timestamp }}</span>
                            </div>
                            <div>
                                <strong>{{ event.details }}</strong>
                            </div>
                            {% if event.locals or event.stacktrace %}
                                <div class="event-details">
                                    {% if event.locals %}
                                        <strong>Locals:</strong>
                                        {{ event.locals | tojson(indent=2) }}
                                    {% endif %}
                                    
                                    {% if event.stacktrace %}
                                        <strong>Stacktrace:</strong>
                                        {{ event.stacktrace | join('\n') }}
                                    {% endif %}
                                </div>
                            {% endif %}
                        </div>
                    {% endfor %}
                {% else %}
                    <div class="no-events">
                        No recent events found
                    </div>
                {% endif %}
            </div>
        {% endif %}
    </div>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, trace_id: Optional[str] = None):
    """Render the index page."""
    # Initialize database
    init_database()
    
    # Get events and trace data
    events = []
    recent_traces = []
    recent_events = []
    
    if trace_id:
        # Get events for specific trace ID
        events = get_events(trace_id=trace_id)
    else:
        # Get recent trace IDs and recent events for overview
        recent_traces = get_recent_trace_ids(limit=20)
        recent_events = get_events(limit=50)  # Get recent events from all traces
    
    # Render template
    from jinja2 import Template
    template = Template(HTML_TEMPLATE)
    return template.render(
        request=request, 
        events=events, 
        trace_id=trace_id,
        recent_traces=recent_traces,
        recent_events=recent_events
    )


@app.get("/api/traces")
async def get_recent_traces(limit: int = 20):
    """Get recent trace IDs with summary information."""
    # Initialize database
    init_database()
    
    # Get recent trace IDs
    traces = get_recent_trace_ids(limit=limit)
    
    return {"traces": traces, "count": len(traces)}


@app.get("/api/traces/{trace_id}")
async def get_trace(trace_id: str):
    """Get events for a specific trace ID."""
    # Initialize database
    init_database()
    
    # Get events
    events = get_events(trace_id=trace_id)
    
    if not events:
        raise HTTPException(status_code=404, detail=f"No events found for trace ID: {trace_id}")
    
    return {"trace_id": trace_id, "events": events}


@app.get("/api/traces/{trace_id}/timeline")
async def get_trace_timeline(trace_id: str):
    """Get a timeline of events for a specific trace ID, organized by stages."""
    # Initialize database
    init_database()
    
    # Get events
    events = get_events(trace_id=trace_id)
    
    if not events:
        raise HTTPException(status_code=404, detail=f"No events found for trace ID: {trace_id}")
    
    # Organize events by system (stage)
    stages = {}
    for event in events:
        system = event.get("system", "unknown")
        if system not in stages:
            stages[system] = []
        stages[system].append(event)
    
    # Sort events within each stage by timestamp
    for system, system_events in stages.items():
        stages[system] = sorted(system_events, key=lambda e: e.get("timestamp", ""))
    
    # Calculate duration and status for each stage
    timeline = []
    for system, system_events in stages.items():
        first_event = system_events[0]
        last_event = system_events[-1]
        
        # Parse timestamps
        try:
            start_time = datetime.fromisoformat(first_event.get("timestamp", "").replace("Z", "+00:00"))
            end_time = datetime.fromisoformat(last_event.get("timestamp", "").replace("Z", "+00:00"))
            duration_ms = (end_time - start_time).total_seconds() * 1000
        except (ValueError, TypeError):
            duration_ms = None
        
        # Determine stage status based on event severities
        has_error = any(e.get("severity") == "error" for e in system_events)
        has_warning = any(e.get("severity") == "warning" for e in system_events)
        
        if has_error:
            status = "error"
        elif has_warning:
            status = "warning"
        else:
            status = "success"
        
        timeline.append({
            "system": system,
            "start_time": first_event.get("timestamp"),
            "end_time": last_event.get("timestamp"),
            "duration_ms": duration_ms,
            "status": status,
            "event_count": len(system_events),
            "events": system_events
        })
    
    # Sort stages by start time
    timeline = sorted(timeline, key=lambda s: s.get("start_time", ""))
    
    return {
        "trace_id": trace_id,
        "stages": timeline,
        "total_stages": len(timeline),
        "has_errors": any(stage["status"] == "error" for stage in timeline),
        "total_duration_ms": sum(stage["duration_ms"] for stage in timeline if stage["duration_ms"] is not None)
    }


async def start_web_ui(host: str = "0.0.0.0", port: int = 8088) -> None:
    """Start the web UI server.

    Args:
        host: The host to bind to
        port: The port to listen on
    """
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()