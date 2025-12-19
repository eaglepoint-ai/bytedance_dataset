from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user
from ..schemas import CreateMeetingIn, MeetingOut, UserOut
from ..crud import create_meeting_booked, list_my_meetings, cancel_meeting

router = APIRouter(prefix="/api/meetings", tags=["meetings"])


@router.post("", response_model=MeetingOut)
def create_meeting(
    body: CreateMeetingIn,
    user: UserOut = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        meeting, meet_status = create_meeting_booked(
            db,
            slot_id=body.slot_id,
            user_id=user.id,
            user_email=user.email,
            description=body.description,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError:
        raise HTTPException(status_code=409, detail="Slot already booked")

    slot = meeting.slot
    return MeetingOut(
        id=meeting.id,
        slot_id=meeting.slot_id,
        start_at=slot.start_at,
        end_at=slot.end_at,
        user_email=meeting.user_email,
        description=meeting.description,
        status=meeting.status.value,
        google_meet_link=meeting.google_meet_link,
        meet_status=meet_status,
    )


@router.get("/me", response_model=list[MeetingOut])
def my_meetings(
    user: UserOut = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = list_my_meetings(db, user_id=user.id)
    out: list[MeetingOut] = []
    for meeting, slot in rows:
        out.append(
            MeetingOut(
                id=meeting.id,
                slot_id=meeting.slot_id,
                start_at=slot.start_at,
                end_at=slot.end_at,
                user_email=meeting.user_email,
                description=meeting.description,
                status=meeting.status.value,
                google_meet_link=meeting.google_meet_link,
                meet_status=None,
            )
        )
    return out


@router.post("/{meeting_id}/cancel")
def cancel(
    meeting_id: UUID,
    user: UserOut = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        meeting = cancel_meeting(db, meeting_id=meeting_id, user_id=user.id)
        return {"ok": True, "status": meeting.status.value}
    except ValueError:
        raise HTTPException(status_code=404, detail="Not found")
