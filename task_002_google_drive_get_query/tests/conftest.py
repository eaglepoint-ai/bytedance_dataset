"""
Pytest fixtures for repository_before tests.

These fixtures provide test clients with seeded databases
for both unit tests and performance tests.
"""
import os
import pytest
from repository_before.app import create_app
from repository_before import db
from tests.utils import clear_database, seed_test_data, seed_heavy_user_data


@pytest.fixture
def client(tmp_path):
    """Fixture for unit tests with basic test data."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        db_path = tmp_path / "test.db"
        db_url = f"sqlite:///{db_path}"

    app = create_app(db_url)
    app.config["TESTING"] = True
    
    # Clear and seed test data
    session = db.SessionLocal()
    try:
        clear_database(session)
        seed_test_data(session)
    finally:
        session.close()

    with app.test_client() as test_client:
        yield test_client
    
    # Cleanup after test
    session = db.SessionLocal()
    try:
        clear_database(session)
    finally:
        session.close()


@pytest.fixture
def perf_client(tmp_path):
    """Fixture for performance tests with large dataset."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        db_path = tmp_path / "perf_test.db"
        db_url = f"sqlite:///{db_path}"

    app = create_app(db_url)
    app.config["TESTING"] = True
    
    # Clear and seed heavy test data
    session = db.SessionLocal()
    try:
        clear_database(session)
        stats = seed_heavy_user_data(session, num_folders=100, num_files_per_folder=50)
        print(f"\nSeeded performance test data: {stats}")
    finally:
        session.close()

    with app.test_client() as test_client:
        yield test_client
    
    # Cleanup after test
    session = db.SessionLocal()
    try:
        clear_database(session)
    finally:
        session.close()
