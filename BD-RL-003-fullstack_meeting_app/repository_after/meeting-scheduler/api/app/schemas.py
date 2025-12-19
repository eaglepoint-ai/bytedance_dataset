from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class UserOut(BaseModel):
    id: str
    email: str
    role: str


class SlotOut(BaseModel):
    id: UUID
    start_at: datetime
    end_at: datetime


class CreateMeetingIn(BaseModel):
    slot_id: UUID
    description: str = Field(min_length=1, max_length=2000)


class MeetingOut(BaseModel):
    id: UUID
    slot_id: UUID
    start_at: datetime
    end_at: datetime
    user_email: str
    description: str
    status: str
    google_meet_link: str | None = None
    meet_status: str | None = None  # "OK" | "NOT_CONFIGURED" | "ERROR"


class AdminMeetingOut(BaseModel):
    id: UUID
    start_at: datetime
    end_at: datetime
    user_email: str
    description: str
    status: str
    google_meet_link: str | None


class CreateSlotsIn(BaseModel):
    start_date: str  # ISO date string (YYYY-MM-DD)
    end_date: str  # ISO date string (YYYY-MM-DD)
    start_time: str = "09:00"  # HH:MM format
    end_time: str = "17:00"  # HH:MM format
    skip_weekends: bool = True


class ConsultantOut(BaseModel):
    id: str
    email: str
