from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from typing import Optional, Tuple

from google.oauth2 import service_account
from googleapiclient.discovery import build

from .config import settings


def _load_service_account_info() -> Optional[dict]:
    if settings.google_service_account_json:
        try:
            return json.loads(settings.google_service_account_json)
        except json.JSONDecodeError:
            return None
    if settings.google_service_account_file:
        path = settings.google_service_account_file
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return None
    return None


def is_configured() -> bool:
    return _load_service_account_info() is not None and bool(settings.google_calendar_id)


def create_calendar_event_with_meet(
    *,
    start_at: datetime,
    end_at: datetime,
    user_email: str,
    description: str,
) -> Tuple[Optional[str], Optional[str]]:
    """Returns (event_id, meet_link). If not configured, returns (None, None)."""
    info = _load_service_account_info()
    if not info:
        return None, None

    creds = service_account.Credentials.from_service_account_info(
        info,
        scopes=["https://www.googleapis.com/auth/calendar"],
    )

    service = build("calendar", "v3", credentials=creds, cache_discovery=False)

    request_id = uuid.uuid4().hex
    event = {
        "summary": "Consultation",
        "description": description,
        "start": {"dateTime": start_at.isoformat()},
        "end": {"dateTime": end_at.isoformat()},
        "attendees": [{"email": user_email}],
        "conferenceData": {
            "createRequest": {
                "requestId": request_id,
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }

    created = (
        service.events()
        .insert(
            calendarId=settings.google_calendar_id,
            body=event,
            conferenceDataVersion=1,
            sendUpdates="none",
        )
        .execute()
    )

    event_id = created.get("id")

    # Prefer hangoutLink, fallback to conferenceData entryPoints
    meet_link = created.get("hangoutLink")
    if not meet_link:
        conf = created.get("conferenceData") or {}
        entry_points = conf.get("entryPoints") or []
        for ep in entry_points:
            if ep.get("entryPointType") == "video" and ep.get("uri"):
                meet_link = ep["uri"]
                break

    return event_id, meet_link
