"""
Comprehensive Backend API Tests for Meeting Scheduler.

Tests moved from meeting-scheduler/api/tests and enhanced with additional coverage.
"""
import os
import uuid
from datetime import datetime, timedelta, timezone

import httpx
import pytest

# Default URLs for Docker environment (auth and api are container hostnames)
API_BASE = os.getenv("API_BASE_URL", "http://api:8000")
AUTH_BASE = os.getenv("AUTH_BASE_URL", "http://auth:3001")

# Cookie name used by auth service
AUTH_COOKIE_NAME = "ms_session"


def extract_cookie_header(response: httpx.Response) -> dict:
    """
    Extract cookie from response and return as a header dict.
    This bypasses httpx's domain-scoped cookie jar to allow cross-domain auth.
    """
    cookie_value = response.cookies.get(AUTH_COOKIE_NAME)
    if cookie_value:
        return {"Cookie": f"{AUTH_COOKIE_NAME}={cookie_value}"}
    return {}


@pytest.fixture
def anyio_backend():
    """Override anyio backend to only use asyncio."""
    return 'asyncio'


@pytest.fixture
async def auth_client():
    """Create authenticated user client."""
    async with httpx.AsyncClient(base_url=AUTH_BASE) as auth:
        email = f"user_{uuid.uuid4().hex[:8]}@example.com"
        password = "password123"
        await auth.post("/api/auth/register", json={"email": email, "password": password, "role": "user"})
        r = await auth.post("/api/auth/login", json={"email": email, "password": password})
        assert r.status_code == 200
        cookie_header = extract_cookie_header(r)
    # Use headers instead of cookies to bypass domain restrictions
    async with httpx.AsyncClient(base_url=API_BASE, headers=cookie_header) as api:
        yield api, email


@pytest.fixture
async def consultant_client():
    """Create authenticated consultant client."""
    async with httpx.AsyncClient(base_url=AUTH_BASE) as auth:
        email = f"consultant_{uuid.uuid4().hex[:8]}@example.com"
        password = "password123"
        await auth.post("/api/auth/register", json={"email": email, "password": password, "role": "consultant"})
        r = await auth.post("/api/auth/login", json={"email": email, "password": password})
        assert r.status_code == 200
        cookie_header = extract_cookie_header(r)
    # Use headers instead of cookies to bypass domain restrictions
    async with httpx.AsyncClient(base_url=API_BASE, headers=cookie_header) as api:
        yield api, email


# Meeting Tests
@pytest.mark.anyio
async def test_create_meeting_requires_authentication():
    """Test that creating a meeting requires authentication."""
    async with httpx.AsyncClient(base_url=API_BASE) as api:
        r = await api.post("/api/meetings", json={"slot_id": str(uuid.uuid4()), "description": "Test"})
        assert r.status_code == 401


@pytest.mark.anyio
async def test_create_meeting_invalid_slot(auth_client):
    """Test creating a meeting with invalid slot_id."""
    api, _ = auth_client
    invalid_slot_id = str(uuid.uuid4())
    r = await api.post("/api/meetings", json={"slot_id": invalid_slot_id, "description": "Test"})
    assert r.status_code == 404


@pytest.mark.anyio
async def test_create_meeting_success(auth_client):
    """Test successfully creating a meeting."""
    api, email = auth_client
    await api.post("/api/test/reset")
    
    async with httpx.AsyncClient(base_url=AUTH_BASE) as auth:
        consultant_email = f"consultant_{uuid.uuid4().hex[:8]}@example.com"
        await auth.post("/api/auth/register", json={"email": consultant_email, "password": "pass123", "role": "consultant"})
        consultant_login = await auth.post("/api/auth/login", json={"email": consultant_email, "password": "pass123"})
        consultant_cookie_header = extract_cookie_header(consultant_login)
        
    async with httpx.AsyncClient(base_url=API_BASE, headers=consultant_cookie_header) as consultant_api:
        await consultant_api.post("/api/test/reset")
        await consultant_api.post("/api/slots/seed")
    
    now = datetime.now(timezone.utc)
    from_ = now.isoformat()
    to = (now + timedelta(days=14)).isoformat()
    slots_r = await api.get("/api/slots", params={"from": from_, "to": to})
    assert slots_r.status_code == 200
    slots = slots_r.json()
    assert len(slots) > 0
    
    slot_id = slots[0]["id"]
    r = await api.post("/api/meetings", json={"slot_id": slot_id, "description": "Test meeting"})
    assert r.status_code == 200
    data = r.json()
    assert data["slot_id"] == slot_id
    assert data["description"] == "Test meeting"
    assert data["user_email"] == email
    assert data["status"] == "BOOKED"


@pytest.mark.anyio
async def test_list_my_meetings(auth_client):
    """Test listing user's meetings."""
    api, email = auth_client
    await api.post("/api/test/reset")
    
    async with httpx.AsyncClient(base_url=AUTH_BASE) as auth:
        consultant_email = f"consultant_{uuid.uuid4().hex[:8]}@example.com"
        await auth.post("/api/auth/register", json={"email": consultant_email, "password": "pass123", "role": "consultant"})
        consultant_login = await auth.post("/api/auth/login", json={"email": consultant_email, "password": "pass123"})
        consultant_cookie_header = extract_cookie_header(consultant_login)
        
    async with httpx.AsyncClient(base_url=API_BASE, headers=consultant_cookie_header) as consultant_api:
        await consultant_api.post("/api/test/reset")
        await consultant_api.post("/api/slots/seed")
    
    r = await api.get("/api/meetings/me")
    assert r.status_code == 200
    assert r.json() == []
    
    now = datetime.now(timezone.utc)
    from_ = now.isoformat()
    to = (now + timedelta(days=14)).isoformat()
    slots_r = await api.get("/api/slots", params={"from": from_, "to": to})
    slot_id = slots_r.json()[0]["id"]
    
    await api.post("/api/meetings", json={"slot_id": slot_id, "description": "My meeting"})
    
    r = await api.get("/api/meetings/me")
    assert r.status_code == 200
    meetings = r.json()
    assert len(meetings) == 1
    assert meetings[0]["description"] == "My meeting"
    assert meetings[0]["user_email"] == email


@pytest.mark.anyio
async def test_cancel_meeting_success(auth_client):
    """Test successfully canceling a meeting."""
    api, email = auth_client
    await api.post("/api/test/reset")
    
    async with httpx.AsyncClient(base_url=AUTH_BASE) as auth:
        consultant_email = f"consultant_{uuid.uuid4().hex[:8]}@example.com"
        await auth.post("/api/auth/register", json={"email": consultant_email, "password": "pass123", "role": "consultant"})
        consultant_login = await auth.post("/api/auth/login", json={"email": consultant_email, "password": "pass123"})
        consultant_cookie_header = extract_cookie_header(consultant_login)
        
    async with httpx.AsyncClient(base_url=API_BASE, headers=consultant_cookie_header) as consultant_api:
        await consultant_api.post("/api/test/reset")
        await consultant_api.post("/api/slots/seed")
    
    now = datetime.now(timezone.utc)
    from_ = now.isoformat()
    to = (now + timedelta(days=14)).isoformat()
    slots_r = await api.get("/api/slots", params={"from": from_, "to": to})
    slot_id = slots_r.json()[0]["id"]
    
    meeting_r = await api.post("/api/meetings", json={"slot_id": slot_id, "description": "To cancel"})
    meeting_id = meeting_r.json()["id"]
    
    cancel_r = await api.post(f"/api/meetings/{meeting_id}/cancel")
    assert cancel_r.status_code == 200
    assert cancel_r.json()["status"] == "CANCELED"
    
    slots_after = await api.get("/api/slots", params={"from": from_, "to": to})
    available_slot_ids = {s["id"] for s in slots_after.json()}
    assert slot_id in available_slot_ids


@pytest.mark.anyio
async def test_booking_same_slot_twice_returns_409():
    """Test that booking the same slot twice returns 409 conflict."""
    async with httpx.AsyncClient(base_url=AUTH_BASE) as auth:
        email = f"user_{uuid.uuid4().hex[:8]}@example.com"
        password = "password123"
        await auth.post("/api/auth/register", json={"email": email, "password": password})
        r = await auth.post("/api/auth/login", json={"email": email, "password": password})
        assert r.status_code == 200
        cookie_header = extract_cookie_header(r)

    async with httpx.AsyncClient(base_url=API_BASE, headers=cookie_header) as api:
        await api.post("/api/test/reset")
        
        now = datetime.now(timezone.utc)
        from_ = now.isoformat()
        to = (now + timedelta(days=14)).isoformat()
        slots = await api.get("/api/slots", params={"from": from_, "to": to})
        assert slots.status_code == 200
        data = slots.json()
        assert len(data) > 0
        slot_id = data[0]["id"]

        r1 = await api.post("/api/meetings", json={"slot_id": slot_id, "description": "Test booking"})
        assert r1.status_code == 200

        r2 = await api.post("/api/meetings", json={"slot_id": slot_id, "description": "Should conflict"})
        assert r2.status_code == 409


@pytest.mark.anyio
async def test_cancel_reopens_slot():
    """Test that canceling a meeting reopens the slot."""
    async with httpx.AsyncClient(base_url=AUTH_BASE) as auth:
        email = f"user_{uuid.uuid4().hex[:8]}@example.com"
        password = "password123"
        await auth.post("/api/auth/register", json={"email": email, "password": password})
        r = await auth.post("/api/auth/login", json={"email": email, "password": password})
        assert r.status_code == 200
        cookie_header = extract_cookie_header(r)

    async with httpx.AsyncClient(base_url=API_BASE, headers=cookie_header) as api:
        await api.post("/api/test/reset")

        now = datetime.now(timezone.utc)
        from_ = now.isoformat()
        to = (now + timedelta(days=14)).isoformat()

        slots_before = (await api.get("/api/slots", params={"from": from_, "to": to})).json()
        assert len(slots_before) > 0
        slot_id = slots_before[0]["id"]

        meeting = await api.post("/api/meetings", json={"slot_id": slot_id, "description": "Cancelable"})
        assert meeting.status_code == 200
        meeting_id = meeting.json()["id"]

        slots_after_booking = (await api.get("/api/slots", params={"from": from_, "to": to})).json()
        assert slot_id not in {s["id"] for s in slots_after_booking}

        cancel = await api.post(f"/api/meetings/{meeting_id}/cancel")
        assert cancel.status_code == 200

        slots_after_cancel = (await api.get("/api/slots", params={"from": from_, "to": to})).json()
        assert slot_id in {s["id"] for s in slots_after_cancel}


# Slot Tests
@pytest.mark.anyio
async def test_get_slots_requires_date_range(auth_client):
    """Test that getting slots requires from and to parameters."""
    api, _ = auth_client
    r = await api.get("/api/slots")
    assert r.status_code == 422


@pytest.mark.anyio
async def test_get_slots_invalid_date_range(auth_client):
    """Test that invalid date ranges return 400."""
    api, _ = auth_client
    now = datetime.now(timezone.utc)
    from_ = now.isoformat()
    to = (now - timedelta(days=1)).isoformat()
    r = await api.get("/api/slots", params={"from": from_, "to": to})
    assert r.status_code == 400


@pytest.mark.anyio
async def test_seed_slots_requires_consultant_role(auth_client):
    """Test that seeding slots requires consultant role."""
    api, _ = auth_client
    r = await api.post("/api/slots/seed")
    assert r.status_code == 403


@pytest.mark.anyio
async def test_seed_slots_as_consultant(consultant_client):
    """Test that consultants can seed slots."""
    api, _ = consultant_client
    # Don't call reset first, as reset already seeds slots
    # Just verify the seed endpoint works and returns proper structure
    r = await api.post("/api/slots/seed")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    # Note: created may be 0 if slots already exist (idempotent operation)
    assert "created" in data
    assert isinstance(data["created"], int)
    assert data["created"] >= 0


@pytest.mark.anyio
async def test_create_slots_endpoint(consultant_client):
    """Test the create slots endpoint."""
    api, email = consultant_client
    await api.post("/api/test/reset")
    
    now = datetime.now(timezone.utc)
    start_date = now.date().isoformat()
    end_date = (now + timedelta(days=2)).date().isoformat()
    
    r = await api.post(
        "/api/slots/create",
        json={
            "start_date": start_date,
            "end_date": end_date,
            "start_time": "09:00",
            "end_time": "12:00",
            "skip_weekends": True,
        }
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["created"] > 0


@pytest.mark.anyio
async def test_admin_meetings_endpoint(consultant_client):
    """Test that consultants can view all meetings via admin endpoint."""
    api, _ = consultant_client
    await api.post("/api/test/reset")
    
    r = await api.get("/api/admin/meetings")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.anyio
async def test_admin_meetings_requires_consultant(auth_client):
    """Test that admin meetings endpoint requires consultant role."""
    api, _ = auth_client
    r = await api.get("/api/admin/meetings")
    assert r.status_code == 403

