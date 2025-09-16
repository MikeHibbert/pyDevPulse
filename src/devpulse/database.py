"""Database functionality for DevPulse."""

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

from .core import get_config

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
    """Initialize the database connection."""
    global _engine, _Session

    db_url = get_config().get("db_url")
    if not db_url:
        logger.warning("Database URL not configured, using SQLite in-memory database")
        db_url = "sqlite:///:memory:"

    try:
        # Create engine
        _engine = create_engine(db_url)

        # Create tables
        _Base.metadata.create_all(_engine)

        # Create session factory
        _Session = sessionmaker(bind=_engine)

        logger.info(f"Database initialized with URL: {db_url}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")


def save_event(event: Dict[str, Any]) -> None:
    """Save an event to the database.

    Args:
        event: The event to save
    """
    global _Session

    # Initialize database if not already initialized
    if _Session is None:
        init_database()
        if _Session is None:
            logger.error("Failed to initialize database, cannot save event")
            return

    try:
        # Create session
        session = _Session()

        # Create event
        db_event = Event(
            trace_id=event.get("traceId", ""),
            system=event.get("system", "backend"),
            event_type=event.get("severity", "info"),
            payload=json.dumps(event),
            timestamp=datetime.utcnow(),
        )

        # Add event to session
        session.add(db_event)

        # Commit session
        session.commit()

        logger.debug(f"Event saved to database: {event.get('traceId')}")
    except Exception as e:
        logger.error(f"Failed to save event to database: {str(e)}")
    finally:
        # Close session
        session.close()


def get_events(
    trace_id: Optional[str] = None,
    system: Optional[str] = None,
    event_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """Get events from the database.

    Args:
        trace_id: Filter by trace ID
        system: Filter by system
        event_type: Filter by event type
        start_time: Filter by start time
        end_time: Filter by end time
        limit: Maximum number of events to return
        offset: Offset for pagination

    Returns:
        A list of events
    """
    global _Session

    # Initialize database if not already initialized
    if _Session is None:
        init_database()
        if _Session is None:
            logger.error("Failed to initialize database, cannot get events")
            return []

    try:
        # Create session
        session = _Session()

        # Create query
        query = session.query(Event)

        # Apply filters
        if trace_id:
            query = query.filter(Event.trace_id == trace_id)
        if system:
            query = query.filter(Event.system == system)
        if event_type:
            query = query.filter(Event.event_type == event_type)
        if start_time:
            query = query.filter(Event.timestamp >= start_time)
        if end_time:
            query = query.filter(Event.timestamp <= end_time)

        # Apply limit and offset
        query = query.order_by(Event.timestamp.desc()).limit(limit).offset(offset)

        # Execute query
        events = query.all()

        # Convert to dictionaries
        result = []
        for event in events:
            try:
                payload = json.loads(event.payload)
                result.append(payload)
            except json.JSONDecodeError:
                logger.warning(f"Failed to decode event payload: {event.id}")

        return result
    except Exception as e:
        logger.error(f"Failed to get events from database: {str(e)}")
        return []
    finally:
        # Close session
        session.close()


def clear_events(
    trace_id: Optional[str] = None,
    system: Optional[str] = None,
    event_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> int:
    """Clear events from the database.

    Args:
        trace_id: Filter by trace ID
        system: Filter by system
        event_type: Filter by event type
        start_time: Filter by start time
        end_time: Filter by end time

    Returns:
        The number of events cleared
    """
    global _Session

    # Initialize database if not already initialized
    if _Session is None:
        init_database()
        if _Session is None:
            logger.error("Failed to initialize database, cannot clear events")
            return 0

    try:
        # Create session
        session = _Session()

        # Create query
        query = session.query(Event)

        # Apply filters
        if trace_id:
            query = query.filter(Event.trace_id == trace_id)
        if system:
            query = query.filter(Event.system == system)
        if event_type:
            query = query.filter(Event.event_type == event_type)
        if start_time:
            query = query.filter(Event.timestamp >= start_time)
        if end_time:
            query = query.filter(Event.timestamp <= end_time)

        # Get count
        count = query.count()

        # Delete events
        query.delete()

        # Commit session
        session.commit()

        logger.info(f"Cleared {count} events from database")
        return count
    except Exception as e:
        logger.error(f"Failed to clear events from database: {str(e)}")
        return 0
    finally:
        # Close session
        session.close()