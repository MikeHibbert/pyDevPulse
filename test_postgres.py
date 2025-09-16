#!/usr/bin/env python3
"""Test script to verify PostgreSQL database functionality."""

import os
import sys
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from devpulse import init
from devpulse.database import save_event, get_events, init_database
from devpulse.core import _config

def test_postgres_database():
    """Test PostgreSQL database functionality."""
    print("Testing PostgreSQL database functionality...")
    
    # Initialize DevPulse with PostgreSQL
    db_url = "postgresql://devpulse:devpulse123@localhost:5432/devpulse"
    print(f"Connecting to: {db_url}")
    
    try:
        # Initialize DevPulse configuration
        init(
            websocket_url="ws://localhost:8088",
            enable_db_logging=True,
            db_url=db_url
        )
        print("✓ DevPulse initialized successfully")
        
        # Initialize the database
        init_database()
        print("✓ Database initialized successfully")
        
        # Test saving an event
        test_event = {
            "traceId": "test-postgres-123",
            "system": "test_system",
            "severity": "info",
            "message": "Testing PostgreSQL connection",
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "test": True,
                "database": "postgresql"
            }
        }
        
        save_event(test_event)
        print("✓ Event saved successfully")
        
        # Test retrieving events
        events = get_events(limit=10)
        print(f"✓ Retrieved {len(events)} events from database")
        
        # Display the events
        for i, event in enumerate(events, 1):
            print(f"  Event {i}: {event.get('severity', 'unknown')} - {event.get('message', 'no message')}")
            print(f"    Trace ID: {event.get('traceId', 'no trace id')}")
            print(f"    System: {event.get('system', 'unknown')}")
            print(f"    Timestamp: {event.get('timestamp', 'no timestamp')}")
            print()
        
        print("✓ PostgreSQL database test completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_postgres_database()
    sys.exit(0 if success else 1)