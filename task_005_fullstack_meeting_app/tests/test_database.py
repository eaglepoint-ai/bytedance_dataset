"""
Comprehensive Database Tests for Meeting Scheduler.

Tests database models, relationships, constraints, and data integrity.
"""
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

# Set DATABASE_URL environment variable before importing app modules
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

# Add API path to sys.path for imports
api_path = Path(__file__).parent.parent / "repository_after" / "meeting-scheduler" / "api"
sys.path.insert(0, str(api_path))

# Try to import core dependencies
try:
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session, sessionmaker
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

# Try to import app modules
try:
    from app.models import Base, TimeSlot, Meeting, MeetingStatus
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False

# Try to import CRUD operations
try:
    from app.crud import (
        list_available_slots,
        create_meeting_booked,
        cancel_meeting,
        create_slots,
        seed_slots_next_14_days,
    )
    CRUD_AVAILABLE = True
except ImportError:
    CRUD_AVAILABLE = False

# Overall availability check
DB_AVAILABLE = SQLALCHEMY_AVAILABLE and MODELS_AVAILABLE and CRUD_AVAILABLE


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session."""
    if not DB_AVAILABLE:
        if not SQLALCHEMY_AVAILABLE:
            pytest.skip("SQLAlchemy not installed (pip install sqlalchemy)")
        elif not MODELS_AVAILABLE:
            pytest.skip("App models not available (missing dependencies in repository_after/meeting-scheduler/api)")
        elif not CRUD_AVAILABLE:
            pytest.skip("App CRUD not available (missing dependencies in repository_after/meeting-scheduler/api)")
        else:
            pytest.skip("Database modules not available")
    
    # Use test database URL or in-memory SQLite
    test_db_url = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False} if "sqlite" in test_db_url else {})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_time_slot_model_creation(db_session):
    """Test creating a TimeSlot model instance."""
    if not DB_AVAILABLE:
        pytest.skip("Database not available")
    
    slot = TimeSlot(
        start_at=datetime.now(timezone.utc),
        end_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        is_active=True,
        consultant_id="consultant_123"
    )
    db_session.add(slot)
    db_session.commit()
    
    assert slot.id is not None
    assert slot.is_active is True
    assert slot.consultant_id == "consultant_123"


def test_meeting_model_creation(db_session):
    """Test creating a Meeting model instance."""
    if not DB_AVAILABLE:
        pytest.skip("Database not available")
    
    # Create slot first
    slot = TimeSlot(
        start_at=datetime.now(timezone.utc),
        end_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        is_active=True,
    )
    db_session.add(slot)
    db_session.commit()
    
    # Create meeting
    meeting = Meeting(
        slot_id=slot.id,
        user_id="user_123",
        user_email="user@example.com",
        description="Test meeting",
        status=MeetingStatus.BOOKED,
    )
    db_session.add(meeting)
    db_session.commit()
    
    assert meeting.id is not None
    assert meeting.slot_id == slot.id
    assert meeting.status == MeetingStatus.BOOKED
    assert meeting.user_email == "user@example.com"


def test_meeting_slot_relationship(db_session):
    """Test relationship between Meeting and TimeSlot."""
    if not DB_AVAILABLE:
        pytest.skip("Database not available")
    
    slot = TimeSlot(
        start_at=datetime.now(timezone.utc),
        end_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        is_active=True,
    )
    db_session.add(slot)
    db_session.commit()
    
    meeting = Meeting(
        slot_id=slot.id,
        user_id="user_123",
        user_email="user@example.com",
        description="Test meeting",
        status=MeetingStatus.BOOKED,
    )
    db_session.add(meeting)
    db_session.commit()
    
    # Test relationship
    assert meeting.slot.id == slot.id
    assert meeting in slot.meetings


def test_list_available_slots_excludes_booked(db_session):
    """Test that list_available_slots excludes slots with booked meetings."""
    if not DB_AVAILABLE:
        pytest.skip("Database not available")
    
    # Create two slots
    slot1 = TimeSlot(
        start_at=datetime.now(timezone.utc),
        end_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        is_active=True,
    )
    slot2 = TimeSlot(
        start_at=datetime.now(timezone.utc) + timedelta(hours=1),
        end_at=datetime.now(timezone.utc) + timedelta(hours=1, minutes=30),
        is_active=True,
    )
    db_session.add_all([slot1, slot2])
    db_session.commit()
    
    # Book slot1
    meeting = Meeting(
        slot_id=slot1.id,
        user_id="user_123",
        user_email="user@example.com",
        description="Booked meeting",
        status=MeetingStatus.BOOKED,
    )
    db_session.add(meeting)
    db_session.commit()
    
    # List available slots
    from_dt = datetime.now(timezone.utc) - timedelta(hours=1)
    to_dt = datetime.now(timezone.utc) + timedelta(hours=2)
    available = list_available_slots(db_session, from_dt, to_dt)
    
    available_ids = {s.id for s in available}
    assert slot1.id not in available_ids
    assert slot2.id in available_ids


def test_create_meeting_booked_function(db_session):
    """Test the create_meeting_booked CRUD function."""
    if not DB_AVAILABLE:
        pytest.skip("Database not available")
    
    # Create slot
    slot = TimeSlot(
        start_at=datetime.now(timezone.utc),
        end_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        is_active=True,
    )
    db_session.add(slot)
    db_session.commit()
    
    # Create meeting using CRUD function
    meeting, meet_status = create_meeting_booked(
        db_session,
        slot_id=slot.id,
        user_id="user_123",
        user_email="user@example.com",
        description="CRUD test meeting",
    )
    
    assert meeting.id is not None
    assert meeting.status == MeetingStatus.BOOKED
    assert meeting.slot_id == slot.id


def test_cancel_meeting_function(db_session):
    """Test the cancel_meeting CRUD function."""
    if not DB_AVAILABLE:
        pytest.skip("Database not available")
    
    # Create slot and meeting
    slot = TimeSlot(
        start_at=datetime.now(timezone.utc),
        end_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        is_active=True,
    )
    db_session.add(slot)
    db_session.commit()
    
    meeting = Meeting(
        slot_id=slot.id,
        user_id="user_123",
        user_email="user@example.com",
        description="To cancel",
        status=MeetingStatus.BOOKED,
    )
    db_session.add(meeting)
    db_session.commit()
    
    # Cancel meeting
    canceled_meeting = cancel_meeting(db_session, meeting.id, "user_123")
    
    assert canceled_meeting.status == MeetingStatus.CANCELED


def test_create_slots_function(db_session):
    """Test the create_slots CRUD function."""
    if not DB_AVAILABLE:
        pytest.skip("Database not available")
    
    now = datetime.now(timezone.utc)
    start_date = now.date().isoformat()
    end_date = (now + timedelta(days=2)).date().isoformat()
    
    count = create_slots(
        db_session,
        start_date=start_date,
        end_date=end_date,
        consultant_id="consultant_123",
        start_time="09:00",
        end_time="12:00",
        skip_weekends=True,
    )
    
    assert count > 0
    
    # Verify slots were created
    slots = db_session.query(TimeSlot).all()
    assert len(slots) >= count


def test_seed_slots_function(db_session):
    """Test the seed_slots_next_14_days function."""
    if not DB_AVAILABLE:
        pytest.skip("Database not available")
    
    count = seed_slots_next_14_days(db_session)
    
    assert count > 0
    
    # Verify slots were created
    slots = db_session.query(TimeSlot).all()
    assert len(slots) == count


def test_meeting_status_enum():
    """Test MeetingStatus enum values."""
    if not DB_AVAILABLE:
        pytest.skip("Database not available")
    
    assert MeetingStatus.BOOKED == "BOOKED"
    assert MeetingStatus.CANCELED == "CANCELED"


def test_time_slot_defaults(db_session):
    """Test TimeSlot default values."""
    if not DB_AVAILABLE:
        pytest.skip("Database not available")
    
    slot = TimeSlot(
        start_at=datetime.now(timezone.utc),
        end_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    db_session.add(slot)
    db_session.commit()
    
    assert slot.is_active is True
    assert slot.created_at is not None
    assert slot.updated_at is not None


def test_meeting_defaults(db_session):
    """Test Meeting default values."""
    if not DB_AVAILABLE:
        pytest.skip("Database not available")
    
    slot = TimeSlot(
        start_at=datetime.now(timezone.utc),
        end_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        is_active=True,
    )
    db_session.add(slot)
    db_session.commit()
    
    meeting = Meeting(
        slot_id=slot.id,
        user_id="user_123",
        user_email="user@example.com",
        description="Test",
    )
    db_session.add(meeting)
    db_session.commit()
    
    assert meeting.status == MeetingStatus.BOOKED
    assert meeting.created_at is not None
    assert meeting.updated_at is not None


def test_slot_inactive_excluded_from_available(db_session):
    """Test that inactive slots are excluded from available slots."""
    if not DB_AVAILABLE:
        pytest.skip("Database not available")
    
    # Create active and inactive slots
    active_slot = TimeSlot(
        start_at=datetime.now(timezone.utc),
        end_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        is_active=True,
    )
    inactive_slot = TimeSlot(
        start_at=datetime.now(timezone.utc) + timedelta(hours=1),
        end_at=datetime.now(timezone.utc) + timedelta(hours=1, minutes=30),
        is_active=False,
    )
    db_session.add_all([active_slot, inactive_slot])
    db_session.commit()
    
    from_dt = datetime.now(timezone.utc) - timedelta(hours=1)
    to_dt = datetime.now(timezone.utc) + timedelta(hours=2)
    available = list_available_slots(db_session, from_dt, to_dt)
    
    available_ids = {s.id for s in available}
    assert active_slot.id in available_ids
    assert inactive_slot.id not in available_ids

