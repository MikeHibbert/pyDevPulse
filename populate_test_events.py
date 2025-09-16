#!/usr/bin/env python3
"""
Script to populate the DevPulse PostgreSQL database with test events
"""

import sys
import os
import time
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from devpulse import init
from devpulse.database import save_event, get_events, init_database

def populate_test_events():
    """Populate the database with test events"""
    print("Connecting to PostgreSQL...")
    
    # Initialize DevPulse with PostgreSQL
    init(
        websocket_url="ws://localhost:8008",
        enable_db_logging=True,
        db_url="postgresql://devpulse:devpulse123@localhost:5432/devpulse",
        environment="test"
    )
    
    # Initialize the database
    print("Initializing database...")
    init_database()
    
    # Create test events with different trace IDs
    # Based on the save_event function, it expects events with traceId, system, severity, and other fields
    test_events = [
        {
            "traceId": "trace-001",
            "system": "api",
            "severity": "info",
            "message": "User login request",
            "metadata": {"user_id": "user123", "endpoint": "/api/login"}
        },
        {
            "traceId": "trace-001", 
            "system": "database",
            "severity": "debug",
            "message": "Fetching user profile",
            "metadata": {"query": "SELECT * FROM users WHERE id = ?", "duration_ms": 45}
        },
        {
            "traceId": "trace-001",
            "system": "api",
            "severity": "info",
            "message": "Login successful",
            "metadata": {"status_code": 200, "response_time_ms": 120}
        },
        {
            "traceId": "trace-002",
            "system": "api",
            "severity": "info",
            "message": "Product search request",
            "metadata": {"search_term": "laptop", "filters": {"price_max": 1000}}
        },
        {
            "traceId": "trace-002",
            "system": "cache",
            "severity": "warning",
            "message": "Search results not in cache",
            "metadata": {"cache_key": "search:laptop:price_max_1000"}
        },
        {
            "traceId": "trace-003",
            "system": "database",
            "severity": "error",
            "message": "Database connection timeout",
            "metadata": {"error_code": "DB_TIMEOUT", "retry_count": 3}
        }
    ]
    
    print(f"Saving {len(test_events)} test events...")
    
    for i, event_data in enumerate(test_events):
        try:
            # Add a small delay between events to create realistic timestamps
            if i > 0:
                time.sleep(0.1)
                
            save_event(event_data)
            print(f"✓ Saved event {i+1}: {event_data['severity']} for {event_data['traceId']}")
        except Exception as e:
            print(f"✗ Error saving event {i+1}: {e}")
    
    # Verify events were saved
    print("\nVerifying saved events...")
    try:
        events = get_events()
        print(f"Total events in database: {len(events)}")
        
        if events:
            print("\nSample events:")
            for i, event in enumerate(events[:3]):  # Show first 3 events
                print(f"- Event {i+1}: {event.get('severity', 'unknown')} - {event.get('message', 'no message')} (trace: {event.get('traceId', 'unknown')})")
        
        # Check events by trace ID
        for trace_id in ["trace-001", "trace-002", "trace-003"]:
            trace_events = get_events(trace_id=trace_id)
            print(f"Events for {trace_id}: {len(trace_events)}")
            
    except Exception as e:
        print(f"Error retrieving events: {e}")
    
    print("\nTest event population complete!")

if __name__ == "__main__":
    populate_test_events()