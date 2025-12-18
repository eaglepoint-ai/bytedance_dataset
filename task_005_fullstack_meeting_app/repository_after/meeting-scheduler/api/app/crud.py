from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID
from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import TimeSlot, Meeting, MeetingStatus

# Optional Google Calendar integration
try:
    from .google_calendar import create_calendar_event_with_meet, is_configured
    GOOGLE_CALENDAR_AVAILABLE = True
except ImportError:
    GOOGLE_CALENDAR_AVAILABLE = False
    create_calendar_event_with_meet = None
    is_configured = lambda: False


def list_available_slots(db: Session, from_dt: datetime, to_dt: datetime, consultant_id: str | None = None) -> list[TimeSlot]:
    # active slots with no BOOKED meeting
    subq = (
        select(Meeting.slot_id)
        .where(Meeting.status == MeetingStatus.BOOKED)
        .subquery()
    )
    conditions = [
        TimeSlot.is_active.is_(True),
        TimeSlot.start_at >= from_dt,
        TimeSlot.end_at <= to_dt,
        TimeSlot.id.not_in(select(subq.c.slot_id)),
    ]
    if consultant_id:
        conditions.append(TimeSlot.consultant_id == consultant_id)
    
    q = (
        select(TimeSlot)
        .where(and_(*conditions))
        .order_by(TimeSlot.start_at.asc())
    )
    return list(db.execute(q).scalars().all())


def seed_slots_next_14_days(db: Session) -> int:
    # Weekdays only, 09:00–17:00, 30-minute intervals
    now = datetime.now(timezone.utc)
    start_day = now.date()
    total = 0

    for day_offset in range(0, 14):
        d = start_day + timedelta(days=day_offset)
        # weekday: Mon=0..Sun=6; keep Mon-Fri
        if d.weekday() >= 5:
            continue
        # Build intervals
        # 09:00 to 17:00 (end exclusive)
        for minutes in range(9 * 60, 17 * 60, 30):
            start_at = datetime(d.year, d.month, d.day, 0, 0, tzinfo=timezone.utc) + timedelta(minutes=minutes)
            end_at = start_at + timedelta(minutes=30)

            exists = db.execute(
                select(TimeSlot.id).where(TimeSlot.start_at == start_at, TimeSlot.end_at == end_at)
            ).first()
            if exists:
                continue

            slot = TimeSlot(start_at=start_at, end_at=end_at, is_active=True)
            db.add(slot)
            total += 1

    db.commit()
    return total


def create_slots(
    db: Session,
    start_date: str,
    end_date: str,
    consultant_id: str,
    start_time: str = "09:00",
    end_time: str = "17:00",
    skip_weekends: bool = True,
) -> int:
    """Create 30-minute slots for the specified date range and time range."""
    from datetime import date
    
    # Parse dates (YYYY-MM-DD format)
    start_dt = date.fromisoformat(start_date)
    end_dt = date.fromisoformat(end_date)
    
    if end_dt < start_dt:
        raise ValueError("End date must be after or equal to start date")
    
    # Parse times (HH:MM format)
    start_hour, start_min = map(int, start_time.split(":"))
    end_hour, end_min = map(int, end_time.split(":"))
    
    start_minutes = start_hour * 60 + start_min
    end_minutes = end_hour * 60 + end_min
    
    if end_minutes <= start_minutes:
        raise ValueError("End time must be after start time")
    
    total = 0
    current_date = start_dt
    
    while current_date <= end_dt:
        # Skip weekends if requested
        if skip_weekends and current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            continue
        
        # Create 30-minute slots for this day
        for minutes in range(start_minutes, end_minutes, 30):
            start_at = datetime(
                current_date.year,
                current_date.month,
                current_date.day,
                0,
                0,
                tzinfo=timezone.utc
            ) + timedelta(minutes=minutes)
            end_at = start_at + timedelta(minutes=30)
            
            # Check if slot already exists for this consultant
            exists = db.execute(
                select(TimeSlot.id).where(
                    TimeSlot.start_at == start_at,
                    TimeSlot.end_at == end_at,
                    TimeSlot.consultant_id == consultant_id
                )
            ).first()
            if exists:
                continue
            
            slot = TimeSlot(start_at=start_at, end_at=end_at, is_active=True, consultant_id=consultant_id)
            db.add(slot)
            total += 1
        
        current_date += timedelta(days=1)
    
    db.commit()
    return total


def create_meeting_booked(
    db: Session,
    *,
    slot_id: UUID,
    user_id: str,
    user_email: str,
    description: str,
) -> tuple[Meeting, str | None]:
    # Validate slot exists and active
    slot = db.get(TimeSlot, slot_id)
    if not slot or not slot.is_active:
        raise ValueError("slot_not_found_or_inactive")

    meeting = Meeting(
        slot_id=slot_id,
        user_id=user_id,
        user_email=user_email,
        description=description,
        status=MeetingStatus.BOOKED,
    )
    db.add(meeting)

    try:
        db.flush()  # triggers partial unique index enforcement
    except IntegrityError:
        db.rollback()
        raise RuntimeError("slot_already_booked")

    meet_status: str | None = None

    # Google Calendar integration (best-effort)
    try:
        if is_configured():
            event_id, meet_link = create_calendar_event_with_meet(
                start_at=slot.start_at,
                end_at=slot.end_at,
                user_email=user_email,
                description=description,
            )
            meeting.google_calendar_event_id = event_id
            meeting.google_meet_link = meet_link
            meet_status = "OK" if meet_link else "ERROR"
        else:
            meet_status = "NOT_CONFIGURED"
    except Exception:
        meet_status = "ERROR"

    db.commit()
    db.refresh(meeting)
    return meeting, meet_status


def list_my_meetings(db: Session, user_id: str) -> list[tuple[Meeting, TimeSlot]]:
    q = (
        select(Meeting, TimeSlot)
        .join(TimeSlot, TimeSlot.id == Meeting.slot_id)
        .where(Meeting.user_id == user_id)
        .order_by(TimeSlot.start_at.desc())
    )
    return list(db.execute(q).all())


def cancel_meeting(db: Session, meeting_id: UUID, user_id: str) -> Meeting:
    meeting = db.get(Meeting, meeting_id)
    if not meeting or meeting.user_id != user_id:
        raise ValueError("meeting_not_found")
    if meeting.status == MeetingStatus.CANCELED:
        return meeting

    meeting.status = MeetingStatus.CANCELED
    db.commit()
    db.refresh(meeting)
    return meeting


def list_admin_meetings(db: Session) -> list[tuple[Meeting, TimeSlot]]:
    q = (
        select(Meeting, TimeSlot)
        .join(TimeSlot, TimeSlot.id == Meeting.slot_id)
        .order_by(TimeSlot.start_at.desc())
    )
    return list(db.execute(q).all())


def reset_all(db: Session) -> None:
    db.query(Meeting).delete()
    db.query(TimeSlot).delete()
    db.commit()
