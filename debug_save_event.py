#!/usr/bin/env python3
"""
Debug script to test event saving with detailed logging
"""

import sys
import os
import logging
import json
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from devpulse import init
from devpulse.database import save_event, get_events, init_database, Event, _Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def debug_save_event():
    """Debug event saving process"""
    print("=== DevPulse Event Saving Debug ===")
    
    # Initialize DevPulse
    print("1. Initializing DevPulse...")
    init(
        websocket_url="ws://localhost:8008",
        enable_db_logging=True,
        db_url="postgresql://devpulse:devpulse123@localhost:5432/devpulse",
        environment="test"
    )
    
    # Initialize database
    print("2. Initializing database...")
    init_database()
    
    # Check if _Session is initialized
    print(f"3. Session factory initialized: {_Session is not None}")
    
    # Test direct database connection
    print("4. Testing direct database connection...")
    try:
        engine = create_engine("postgresql://devpulse:devpulse123@localhost:5432/devpulse")
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Test connection
        result = session.execute(text("SELECT 1"))
        print(f"   Direct connection test: {result.scalar()}")
        
        # Check if events table exists
        result = session.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'events'"))
        table_exists = result.scalar()
        print(f"   Events table exists: {table_exists > 0}")
        
        session.close()
    except Exception as e:
        print(f"   Direct connection error: {e}")
    
    # Create a test event
    print("5. Creating test event...")
    test_event = {
        "traceId": "debug-trace-001",
        "system": "debug",
        "severity": "info",
        "message": "Debug test event",
        "metadata": {"test": True, "timestamp": datetime.utcnow().isoformat()}
    }
    
    print(f"   Event data: {json.dumps(test_event, indent=2)}")
    
    # Save the event
    print("6. Saving event...")
    try:
        save_event(test_event)
        print("   Event save completed (no exception)")
    except Exception as e:
        print(f"   Event save error: {e}")
        import traceback
        traceback.print_exc()
    
    # Check if event was saved using direct query
    print("7. Checking if event was saved (direct query)...")
    try:
        engine = create_engine("postgresql://devpulse:devpulse123@localhost:5432/devpulse")
        Session = sessionmaker(bind=engine)
        session = Session()
        
        result = session.execute(text("SELECT COUNT(*) FROM events"))
        count = result.scalar()
        print(f"   Total events in database: {count}")
        
        if count > 0:
            result = session.execute(text("SELECT * FROM events ORDER BY timestamp DESC LIMIT 1"))
            row = result.fetchone()
            if row:
                print(f"   Latest event: {dict(row._mapping)}")
        
        session.close()
    except Exception as e:
        print(f"   Direct query error: {e}")
    
    # Check using get_events function
    print("8. Checking using get_events function...")
    try:
        events = get_events()
        print(f"   Events from get_events: {len(events)}")
        if events:
            print(f"   First event: {events[0]}")
    except Exception as e:
        print(f"   get_events error: {e}")
    
    print("=== Debug Complete ===")

if __name__ == "__main__":
    debug_save_event()