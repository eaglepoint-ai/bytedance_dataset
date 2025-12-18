from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..deps import get_db, require_consultant
from ..schemas import AdminMeetingOut, UserOut
from ..crud import list_admin_meetings

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/meetings", response_model=list[AdminMeetingOut])
def meetings(
    _consultant: UserOut = Depends(require_consultant),
    db: Session = Depends(get_db),
):
    rows = list_admin_meetings(db)
    out: list[AdminMeetingOut] = []
    for meeting, slot in rows:
        out.append(
            AdminMeetingOut(
                id=meeting.id,
                start_at=slot.start_at,
                end_at=slot.end_at,
                user_email=meeting.user_email,
                description=meeting.description,
                status=meeting.status.value,
                google_meet_link=meeting.google_meet_link,
            )
        )
    return out
