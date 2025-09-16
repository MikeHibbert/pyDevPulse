#!/usr/bin/env python3
"""Debug script to test database functions used by web UI."""

import sys
import os
sys.path.insert(0, '/app/src')

from devpulse import init
from devpulse.database import init_database, get_recent_trace_ids, get_events

def debug_database():
    """Debug the database functions."""
    # Initialize DevPulse with database configuration
    db_url = os.getenv('DEVPULSE_DB_URL')
    print(f"Database URL: {db_url}")
    
    init(
        websocket_url='ws://localhost:8008',
        enable_db_logging=True,
        db_url=db_url,
        environment='production'
    )
    
    print("Initializing database...")
    init_database()
    
    print("Testing get_recent_trace_ids...")
    try:
        recent_traces = get_recent_trace_ids()
        print(f"Recent traces: {recent_traces}")
        print(f"Number of recent traces: {len(recent_traces)}")
    except Exception as e:
        print(f"Error getting recent traces: {e}")
    
    print("Testing get_events for trace-001...")
    try:
        events = get_events(trace_id="trace-001")
        print(f"Events for trace-001: {events}")
        print(f"Number of events: {len(events)}")
    except Exception as e:
        print(f"Error getting events: {e}")
    
    print("Testing get_events for all traces...")
    try:
        all_events = get_events()
        print(f"All events count: {len(all_events)}")
        if all_events:
            print(f"First event: {all_events[0]}")
    except Exception as e:
        print(f"Error getting all events: {e}")

if __name__ == "__main__":
    debug_database()