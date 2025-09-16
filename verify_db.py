#!/usr/bin/env python3
"""Script to verify database file creation and event persistence."""

import os
import sqlite3
import sys
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from devpulse import init
from devpulse.database import init_database, save_event

def verify_database():
    """Verify database file creation and event persistence."""
    print("=== Database Verification ===")
    
    # Initialize DevPulse
    db_url = os.getenv('DEVPULSE_DB_URL', 'sqlite:///app/data/devpulse.db')
    print(f"Database URL: {db_url}")
    
    init(
        websocket_url='ws://localhost:8008',
        enable_db_logging=True,
        db_url=db_url,
        environment='production'
    )
    
    print("Initializing database...")
    init_database()
    
    # Check if database file exists
    if db_url.startswith('sqlite:///'):
        db_path = db_url.replace('sqlite:///', '')
        print(f"Checking database file: {db_path}")
        if os.path.exists(db_path):
            print(f"✓ Database file exists: {os.path.getsize(db_path)} bytes")
        else:
            print(f"✗ Database file does not exist: {db_path}")
    
    # Create a test event
    test_event = {
        "traceId": "verify-trace-001",
        "timestamp": datetime.now().isoformat() + "Z",
        "severity": "info",
        "system": "verification",
        "file": "verify.py",
        "line": 1,
        "source": "verify_function()",
        "locals": {"test": True},
        "stacktrace": [],
        "response": "success",
        "details": "Database verification test event",
        "environment": "test"
    }
    
    print("Creating test event...")
    save_event(test_event)
    print("✓ Test event created")
    
    # Check database directly with SQLite
    if db_url.startswith('sqlite:///'):
        db_path = db_url.replace('sqlite:///', '')
        if os.path.exists(db_path):
            print("\nChecking database contents directly...")
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                print(f"Tables: {[table[0] for table in tables]}")
                
                # Check events table
                cursor.execute("SELECT COUNT(*) FROM events")
                count = cursor.fetchone()[0]
                print(f"Total events in database: {count}")
                
                # Get recent events
                cursor.execute("SELECT trace_id, system, event_type, timestamp FROM events ORDER BY timestamp DESC LIMIT 5")
                events = cursor.fetchall()
                print("Recent events:")
                for event in events:
                    print(f"  - {event[0]} | {event[1]} | {event[2]} | {event[3]}")
                
                conn.close()
                print("✓ Database verification completed")
                
            except Exception as e:
                print(f"✗ Error checking database: {e}")
    
    print("\n=== Verification Complete ===")

if __name__ == "__main__":
    verify_database()