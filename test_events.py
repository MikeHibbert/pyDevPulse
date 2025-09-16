#!/usr/bin/env python3
"""Test script to create sample events in DevPulse database."""

import sys
import os
import json
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from devpulse import init
from devpulse.database import init_database, save_event

def create_test_events():
    """Create some test events in the database."""
    # Initialize DevPulse with database configuration
    db_url = os.getenv('DEVPULSE_DB_URL')
    init(
        websocket_url='ws://localhost:8008',
        enable_db_logging=True,
        db_url=db_url,
        environment='production'
    )
    
    print("Initializing database...")
    init_database()
    
    # Create test events
    test_events = [
        {
            "traceId": "test-trace-001",
            "timestamp": datetime.now().isoformat() + "Z",
            "severity": "info",
            "system": "api",
            "file": "test.py",
            "line": 10,
            "source": "test_function()",
            "locals": {"user_id": 123, "action": "login"},
            "stacktrace": [],
            "response": "success",
            "details": "User login successful",
            "environment": "development"
        },
        {
            "traceId": "test-trace-001",
            "timestamp": datetime.now().isoformat() + "Z",
            "severity": "warning",
            "system": "database",
            "file": "db.py",
            "line": 25,
            "source": "query_user()",
            "locals": {"query": "SELECT * FROM users", "duration": 150},
            "stacktrace": [],
            "response": "success",
            "details": "Slow database query detected",
            "environment": "development"
        },
        {
            "traceId": "test-trace-002",
            "timestamp": datetime.now().isoformat() + "Z",
            "severity": "error",
            "system": "worker",
            "file": "worker.py",
            "line": 42,
            "source": "process_task()",
            "locals": {"task_id": "task-456", "error": "Connection timeout"},
            "stacktrace": ["File worker.py, line 42", "Connection timeout occurred"],
            "response": "fail",
            "details": "Task processing failed due to connection timeout",
            "environment": "development"
        },
        {
            "traceId": "test-trace-003",
            "timestamp": datetime.now().isoformat() + "Z",
            "severity": "info",
            "system": "api",
            "file": "api.py",
            "line": 15,
            "source": "health_check()",
            "locals": {"status": "healthy", "uptime": 3600},
            "stacktrace": [],
            "response": "success",
            "details": "Health check passed",
            "environment": "development"
        }
    ]
    
    print(f"Creating {len(test_events)} test events...")
    for i, event in enumerate(test_events, 1):
        try:
            save_event(event)
            print(f"✓ Created event {i}: {event['details']}")
        except Exception as e:
            print(f"✗ Failed to create event {i}: {str(e)}")
    
    print("Test events created successfully!")

if __name__ == "__main__":
    create_test_events()