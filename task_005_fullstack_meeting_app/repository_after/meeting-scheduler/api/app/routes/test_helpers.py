from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_db
from ..config import settings
from ..crud import reset_all, seed_slots_next_14_days

router = APIRouter(prefix="/api/test", tags=["test"])


@router.post("/reset")
def reset(
    db: Session = Depends(get_db),
):
    if not settings.api_enable_test_reset:
        raise HTTPException(status_code=404, detail="Not found")
    reset_all(db)
    created = seed_slots_next_14_days(db)
    return {"ok": True, "seeded": created}
