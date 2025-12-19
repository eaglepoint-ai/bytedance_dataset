import enum
import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class MeetingStatus(str, enum.Enum):
    BOOKED = "BOOKED"
    CANCELED = "CANCELED"


class TimeSlot(Base):
    __tablename__ = "time_slots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    consultant_id: Mapped[str | None] = mapped_column(String, nullable=True)  # User ID of the consultant who created this slot

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    meetings: Mapped[list["Meeting"]] = relationship("Meeting", back_populates="slot")


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    slot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("time_slots.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    user_email: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[MeetingStatus] = mapped_column(Enum(MeetingStatus, name="meeting_status"), nullable=False, default=MeetingStatus.BOOKED)

    google_calendar_event_id: Mapped[str | None] = mapped_column(String, nullable=True)
    google_meet_link: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    slot: Mapped[TimeSlot] = relationship("TimeSlot", back_populates="meetings")

    __table_args__ = (
        # Partial unique index is created in init SQL (Postgres-specific) for status='BOOKED'
        Index(
            "ix_meetings_slot_booked_unique",
            "slot_id",
            unique=True,
            postgresql_where=(status == MeetingStatus.BOOKED),
        ),
    )
