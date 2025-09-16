"""Patch for DevPulse database initialization with read-only connections to avoid locking."""

import os
import json
import logging
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, MetaData, Table
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Setup logger
logger = logging.getLogger("devpulse.database")

# Global variables
_engine = None
_Session = None
_Base = declarative_base()


class Event(_Base):
    """Event model for database storage."""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    trace_id = Column(String(36), index=True)
    system = Column(String(50), index=True)
    event_type = Column(String(50), index=True)
    payload = Column(Text)  # JSON as text for SQLite compatibility
    timestamp = Column(DateTime, index=True)


def init_database() -> None:
    """Initialize the database connection with environment variable support and read-only access."""
    global _engine, _Session

    # Try to get database URL from environment variable first
    db_url = os.getenv('DEVPULSE_DB_URL')
    
    # If not found, try to get from DevPulse config
    if not db_url:
        try:
            from devpulse.core import get_config
            db_url = get_config().get("db_url")
        except:
            pass
    
    # Default fallback
    if not db_url:
        logger.warning("Database URL not configured, using SQLite in-memory database")
        db_url = "sqlite:///:memory:"

    try:
        # For SQLite, add read-only parameters to avoid locking
        if db_url.startswith("sqlite:///"):
            # Extract the file path
            db_file = db_url.replace("sqlite:///", "")
            # Create read-only connection string
            db_url = f"sqlite:///{db_file}?mode=ro"

        # Create engine with read-only settings
        _engine = create_engine(db_url, pool_pre_ping=True)

        # Create session factory
        _Session = sessionmaker(bind=_engine)

        logger.info(f"Database initialized with URL: {db_url}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")


def get_recent_trace_ids_direct(limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent trace IDs using direct SQLite connection to avoid locking issues."""
    
    # Get database file path from environment
    db_url = os.getenv('DEVPULSE_DB_URL', 'sqlite:///app/data/devpulse.db')
    
    if not db_url.startswith("sqlite:///"):
        logger.error("Direct access only supports SQLite databases")
        return []
    
    db_file = db_url.replace("sqlite:///", "")
    
    try:
        # Use direct SQLite connection with read-only mode
        conn = sqlite3.connect(f"file:{db_file}?mode=ro", uri=True)
        cursor = conn.cursor()
        
        # Query to get recent trace IDs with their latest event information
        query = """
        SELECT 
            e1.trace_id,
            e1.system,
            e1.event_type,
            e1.payload,
            e1.timestamp,
            COUNT(e2.id) as event_count
        FROM events e1
        INNER JOIN (
            SELECT trace_id, MAX(timestamp) as latest_timestamp
            FROM events
            GROUP BY trace_id
        ) latest ON e1.trace_id = latest.trace_id AND e1.timestamp = latest.latest_timestamp
        LEFT JOIN events e2 ON e1.trace_id = e2.trace_id
        GROUP BY e1.trace_id, e1.system, e1.event_type, e1.payload, e1.timestamp
        ORDER BY e1.timestamp DESC
        LIMIT ?
        """
        
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            trace_id, system, event_type, payload, timestamp, event_count = row
            
            try:
                # Parse the payload JSON
                payload_data = json.loads(payload) if payload else {}
                
                result.append({
                    'trace_id': trace_id,
                    'latest_timestamp': timestamp,
                    'system': system,
                    'event_type': event_type,
                    'event_count': event_count,
                    'latest_event': payload_data
                })
            except json.JSONDecodeError:
                logger.warning(f"Failed to decode event payload for trace {trace_id}")
                result.append({
                    'trace_id': trace_id,
                    'latest_timestamp': timestamp,
                    'system': system,
                    'event_type': event_type,
                    'event_count': event_count,
                    'latest_event': {}
                })
        
        conn.close()
        return result
        
    except Exception as e:
        logger.error(f"Failed to get recent trace IDs from database: {str(e)}")
        return []


def get_recent_trace_ids(limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent trace IDs with their latest event information."""
    # Use direct SQLite access to avoid locking issues
    return get_recent_trace_ids_direct(limit)


# Test function
if __name__ == "__main__":
    print("Testing patched database module with direct SQLite access...")
    traces = get_recent_trace_ids(5)
    print(f"Found {len(traces)} traces")
    for trace in traces:
        print(f"- {trace['trace_id'][:8]}... ({trace['event_count']} events) - {trace['system']}/{trace['event_type']}")