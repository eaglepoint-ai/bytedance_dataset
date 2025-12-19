from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from .db import SessionLocal
from .auth_client import fetch_session, AuthError
from .schemas import UserOut


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(request: Request) -> UserOut:
    try:
        payload = fetch_session(request)
        user = payload.get("user")
        if not user:
            raise AuthError("unauthorized")
        return UserOut(**user)
    except AuthError:
        raise HTTPException(status_code=401, detail="Unauthorized")


def require_consultant(user: UserOut = Depends(get_current_user)) -> UserOut:
    if user.role != "consultant":
        raise HTTPException(status_code=403, detail="Consultant only")
    return user
