#!/usr/bin/env python3
"""Simple script to check database contents."""

import sqlite3
import os

def check_database():
    db_path = '/app/data/devpulse.db'
    print(f'Database file exists: {os.path.exists(db_path)}')
    print(f'Database file size: {os.path.getsize(db_path)} bytes')

    try:
        conn = sqlite3.connect(db_path, timeout=30)
        cursor = conn.cursor()
        
        # Check if events table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
        table_exists = cursor.fetchone()
        print(f'Events table exists: {table_exists is not None}')
        
        if table_exists:
            cursor.execute('SELECT COUNT(*) FROM events')
            count = cursor.fetchone()[0]
            print(f'Total events in database: {count}')
            
            if count > 0:
                cursor.execute('SELECT trace_id, system, event_type, timestamp FROM events ORDER BY timestamp DESC LIMIT 3')
                events = cursor.fetchall()
                print('Recent events:')
                for event in events:
                    print(f'  {event}')
        
        conn.close()
        print('Database check completed successfully')
    except Exception as e:
        print(f'Database error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database()