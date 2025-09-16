#!/usr/bin/env python3
"""Debug script to investigate PostgreSQL event retrieval."""

import os
import sys
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from devpulse import init
from devpulse.database import save_event, get_events, init_database, _Session, Event

def debug_postgres_database():
    """Debug PostgreSQL database functionality."""
    print("Debugging PostgreSQL database functionality...")
    
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
        
        # Save multiple test events
        for i in range(3):
            test_event = {
                "traceId": f"debug-postgres-{i}",
                "system": "debug_system",
                "severity": "info",
                "message": f"Debug event {i}",
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "test": True,
                    "database": "postgresql",
                    "event_number": i
                }
            }
            
            save_event(test_event)
            print(f"✓ Event {i} saved successfully")
        
        # Direct database query to check if events exist
        print("\nDirect database query:")
        session = _Session()
        try:
            count = session.query(Event).count()
            print(f"Total events in database: {count}")
            
            # Get all events directly
            all_events = session.query(Event).all()
            print(f"Direct query returned {len(all_events)} events:")
            for event in all_events:
                print(f"  ID: {event.id}, Trace: {event.trace_id}, Type: {event.event_type}")
                print(f"  Payload: {event.payload[:100]}...")
                print()
        finally:
            session.close()
        
        # Test retrieving events using get_events function
        print("Using get_events function:")
        events = get_events(limit=10)
        print(f"get_events() returned {len(events)} events")
        
        # Display the events
        for i, event in enumerate(events, 1):
            print(f"  Event {i}: {event.get('severity', 'unknown')} - {event.get('message', 'no message')}")
            print(f"    Trace ID: {event.get('traceId', 'no trace id')}")
            print(f"    System: {event.get('system', 'unknown')}")
            print()
        
        print("✓ PostgreSQL database debug completed!")
        return True
        
    except Exception as e:
        print(f"✗ Database debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_postgres_database()
    sys.exit(0 if success else 1)