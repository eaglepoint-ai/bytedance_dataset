from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from .config import settings
from .db import engine
from .models import Base
from .routes.slots import router as slots_router
from .routes.meetings import router as meetings_router
from .routes.admin import router as admin_router
from .routes.test_helpers import router as test_router


app = FastAPI(title="Meeting Scheduler API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.api_cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True}


@app.on_event("startup")
def startup():
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Add consultant_id column to time_slots if it doesn't exist (migration)
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name = 'time_slots'
                        AND column_name = 'consultant_id'
                    ) THEN
                        ALTER TABLE time_slots
                        ADD COLUMN consultant_id VARCHAR;
                    END IF;
                END$$;
            """))
    except Exception:
        # Non-Postgres or already exists
        pass

    # Ensure Postgres partial unique index exists (for slot exclusivity)
    # If using SQLite (tests), Index in models is ignored and this statement will fail; ignore.
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM pg_indexes
                        WHERE schemaname = 'public'
                        AND indexname = 'ux_meetings_slot_booked'
                    ) THEN
                        CREATE UNIQUE INDEX ux_meetings_slot_booked
                        ON meetings (slot_id)
                        WHERE status = 'BOOKED';
                    END IF;
                END$$;
            """))
    except Exception:
        # Non-Postgres or already exists
        pass


app.include_router(slots_router)
app.include_router(meetings_router)
app.include_router(admin_router)
app.include_router(test_router)
