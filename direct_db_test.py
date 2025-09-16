#!/usr/bin/env python3
"""
Direct database test to check what's actually stored
"""

import sys
import os
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from devpulse.database import Event, _Base

def direct_db_test():
    """Test direct database access"""
    print("Testing direct database access...")
    
    # Create engine
    engine = create_engine("postgresql://devpulse:devpulse123@localhost:5432/devpulse")
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check if table exists
        result = session.execute(text("SELECT COUNT(*) FROM events"))
        count = result.scalar()
        print(f"Total events in database: {count}")
        
        # Get all events
        events = session.query(Event).all()
        print(f"Events retrieved via ORM: {len(events)}")
        
        if events:
            print("\nFirst few events:")
            for i, event in enumerate(events[:3]):
                print(f"Event {i+1}:")
                print(f"  ID: {event.id}")
                print(f"  Trace ID: {event.trace_id}")
                print(f"  System: {event.system}")
                print(f"  Event Type: {event.event_type}")
                print(f"  Timestamp: {event.timestamp}")
                print(f"  Payload: {event.payload[:100]}...")
                print()
        
        # Check raw SQL
        result = session.execute(text("SELECT * FROM events LIMIT 3"))
        rows = result.fetchall()
        print(f"Raw SQL results: {len(rows)} rows")
        
        if rows:
            print("\nRaw SQL data:")
            for i, row in enumerate(rows):
                print(f"Row {i+1}: {dict(row._mapping)}")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    direct_db_test()