from __future__ import annotations

import requests
from fastapi import Request
from .config import settings


class AuthError(Exception):
    pass


def fetch_session(request: Request) -> dict:
    # Forward cookies + Authorization header to auth service /session endpoint
    headers = {}
    if request.headers.get("authorization"):
        headers["authorization"] = request.headers["authorization"]

    # requests needs cookie dict; forward raw Cookie header is easiest
    if request.headers.get("cookie"):
        headers["cookie"] = request.headers["cookie"]

    url = f"{settings.auth_base_url}/api/auth/session"
    resp = requests.get(url, headers=headers, timeout=5)

    if resp.status_code != 200:
        raise AuthError("unauthorized")
    return resp.json()
