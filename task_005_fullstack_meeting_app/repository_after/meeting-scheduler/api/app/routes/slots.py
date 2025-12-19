from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from dateutil import parser as dtparser

from ..deps import get_db, require_consultant
from ..schemas import SlotOut, UserOut, CreateSlotsIn, ConsultantOut
from ..crud import list_available_slots, seed_slots_next_14_days, create_slots
from fastapi import Request

router = APIRouter(prefix="/api/slots", tags=["slots"])


@router.get("", response_model=list[SlotOut])
def get_slots(
    from_: str = Query(alias="from"),
    to: str = Query(),
    consultant_id: str | None = Query(None),
    db: Session = Depends(get_db),
):
    try:
        from_dt = dtparser.isoparse(from_).astimezone(timezone.utc)
        to_dt = dtparser.isoparse(to).astimezone(timezone.utc)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid datetime range")

    if to_dt <= from_dt:
        raise HTTPException(status_code=400, detail="Invalid datetime range")

    slots = list_available_slots(db, from_dt=from_dt, to_dt=to_dt, consultant_id=consultant_id)
    return [SlotOut(id=s.id, start_at=s.start_at, end_at=s.end_at) for s in slots]


@router.post("/seed")
def seed_slots(
    _consultant: UserOut = Depends(require_consultant),
    db: Session = Depends(get_db),
):
    count = seed_slots_next_14_days(db)
    return {"ok": True, "created": count}


@router.post("/create")
def create_slots_endpoint(
    body: CreateSlotsIn,
    consultant: UserOut = Depends(require_consultant),
    db: Session = Depends(get_db),
):
    try:
        count = create_slots(
            db,
            start_date=body.start_date,
            end_date=body.end_date,
            consultant_id=consultant.id,
            start_time=body.start_time,
            end_time=body.end_time,
            skip_weekends=body.skip_weekends,
        )
        return {"ok": True, "created": count}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create slots: {str(e)}")


@router.get("/consultants", response_model=list[ConsultantOut])
def get_consultants(
    request: Request,
):
    """Get list of all consultants."""
    try:
        import requests
        from ..config import settings
        
        # Query auth service for consultants (no auth required for this endpoint)
        auth_url = f"{settings.auth_base_url}/api/auth/consultants"
        resp = requests.get(auth_url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                return data
            return []
        return []
    except Exception as e:
        # Log error but return empty list to prevent breaking the UI
        import logging
        logging.error(f"Failed to fetch consultants: {e}")
        return []
