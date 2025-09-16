"""Tests for DevPulse database functionality."""

import os
import unittest
from unittest.mock import patch, MagicMock

from devpulse.database import (
    init_db, save_event, get_events, clear_events, Event
)


class TestDatabase(unittest.TestCase):
    """Test the database functionality of DevPulse."""

    def setUp(self):
        """Set up the test environment."""
        # Use an in-memory SQLite database for testing
        self.db_url = "sqlite:///:memory:"

    @patch("devpulse.database.create_engine")
    @patch("devpulse.database.sessionmaker")
    @patch("devpulse.database.Base.metadata.create_all")
    def test_init_db(self, mock_create_all, mock_sessionmaker, mock_create_engine):
        """Test initializing the database."""
        # Mock engine
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        # Mock session
        mock_session = MagicMock()
        mock_sessionmaker.return_value = mock_session

        # Initialize database
        init_db(self.db_url)

        # Check that the engine was created
        mock_create_engine.assert_called_once_with(self.db_url)

        # Check that the metadata was created
        mock_create_all.assert_called_once_with(mock_engine)

        # Check that the session was created
        mock_sessionmaker.assert_called_once_with(bind=mock_engine)

    @patch("devpulse.database.Session")
    @patch("devpulse.database.Event")
    @patch("devpulse.database.init_db")
    def test_save_event(self, mock_init_db, mock_event_class, mock_session):
        """Test saving an event."""
        # Mock session
        mock_session_instance = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_session_instance

        # Mock event
        mock_event = MagicMock()
        mock_event_class.return_value = mock_event

        # Create an event
        event = {
            "traceId": "test-trace-id",
            "timestamp": "2023-01-01T00:00:00Z",
            "severity": "error",
            "system": "test",
            "details": "Test event",
            "file": "test.py",
            "line": 42,
            "source": "test_function",
            "locals": {"var": "value"},
            "stacktrace": ["line1", "line2"],
            "response": "fail",
            "environment": "test"
        }

        # Save the event
        save_event(event)

        # Check that the database was initialized
        mock_init_db.assert_called_once()

        # Check that the event was created
        mock_event_class.assert_called_once_with(
            trace_id="test-trace-id",
            timestamp="2023-01-01T00:00:00Z",
            severity="error",
            system="test",
            details="Test event",
            file="test.py",
            line=42,
            source="test_function",
            locals={"var": "value"},
            stacktrace=["line1", "line2"],
            response="fail",
            environment="test"
        )

        # Check that the event was added to the session
        mock_session_instance.add.assert_called_once_with(mock_event)

        # Check that the session was committed
        mock_session_instance.commit.assert_called_once()

    @patch("devpulse.database.Session")
    @patch("devpulse.database.init_db")
    def test_get_events(self, mock_init_db, mock_session):
        """Test getting events."""
        # Mock session
        mock_session_instance = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_session_instance

        # Mock query
        mock_query = MagicMock()
        mock_session_instance.query.return_value = mock_query

        # Mock filter
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter

        # Mock order_by
        mock_order_by = MagicMock()
        mock_filter.order_by.return_value = mock_order_by

        # Mock limit
        mock_limit = MagicMock()
        mock_order_by.limit.return_value = mock_limit

        # Mock all
        mock_event1 = MagicMock()
        mock_event1.to_dict.return_value = {"id": 1, "traceId": "test-trace-id-1"}
        mock_event2 = MagicMock()
        mock_event2.to_dict.return_value = {"id": 2, "traceId": "test-trace-id-2"}
        mock_limit.all.return_value = [mock_event1, mock_event2]

        # Get events
        events = get_events(trace_id="test-trace-id", limit=10)

        # Check that the database was initialized
        mock_init_db.assert_called_once()

        # Check that the query was made
        mock_session_instance.query.assert_called_once_with(Event)

        # Check that the filter was applied
        mock_query.filter.assert_called_once()

        # Check that the order_by was applied
        mock_filter.order_by.assert_called_once()

        # Check that the limit was applied
        mock_order_by.limit.assert_called_once_with(10)

        # Check that the events were returned
        self.assertEqual(events, [{"id": 1, "traceId": "test-trace-id-1"}, {"id": 2, "traceId": "test-trace-id-2"}])

    @patch("devpulse.database.Session")
    @patch("devpulse.database.init_db")
    def test_clear_events(self, mock_init_db, mock_session):
        """Test clearing events."""
        # Mock session
        mock_session_instance = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_session_instance

        # Mock query
        mock_query = MagicMock()
        mock_session_instance.query.return_value = mock_query

        # Mock filter
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter

        # Mock delete
        mock_filter.delete.return_value = 2

        # Clear events
        count = clear_events(trace_id="test-trace-id")

        # Check that the database was initialized
        mock_init_db.assert_called_once()

        # Check that the query was made
        mock_session_instance.query.assert_called_once_with(Event)

        # Check that the filter was applied
        mock_query.filter.assert_called_once()

        # Check that the delete was called
        mock_filter.delete.assert_called_once()

        # Check that the session was committed
        mock_session_instance.commit.assert_called_once()

        # Check that the count was returned
        self.assertEqual(count, 2)


if __name__ == "__main__":
    unittest.main()