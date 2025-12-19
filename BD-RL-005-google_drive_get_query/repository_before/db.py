# db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from repository_before.models import Base

engine = None
SessionLocal = None

def get_database_url():
    """Get database URL from environment or use default PostgreSQL."""
    return os.environ.get("DATABASE_URL", "postgresql://appuser:apppass@localhost:5432/appdb")

def init_db(db_url=None):
    global engine, SessionLocal
    if db_url is None:
        db_url = get_database_url()
    engine = create_engine(db_url, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
