import os
import pytest
from datetime import datetime
from repository_before.app import create_app
from repository_before import db
from repository_before.models import User, Folder, File, Permission


def clear_database(session):
    """Clear all data from the database."""
    session.query(Permission).delete()
    session.query(File).delete()
    session.query(Folder).delete()
    session.query(User).delete()
    session.commit()


def seed_test_data(session):
    """Seed the database with test data for unit tests."""
    now = datetime.now()
    
    # Create test users first
    users = [
        User(id="user_1", email="user1@test.com", createdAt=now),
        User(id="user_2", email="user2@test.com", createdAt=now),
        User(id="user_3", email="user3@test.com", createdAt=now),
    ]
    session.add_all(users)
    session.commit()
    
    # Create folders (parent before child due to FK)
    parent_folder = Folder(id="parent_folder", name="Parent Folder", ownerId="user_1", parentId=None, createdAt=now)
    folder_1 = Folder(id="folder_1", name="User 1 Folder", ownerId="user_1", parentId=None, createdAt=now)
    session.add_all([parent_folder, folder_1])
    session.commit()
    
    child_folder = Folder(id="child_folder", name="Child Folder", ownerId="user_1", parentId="parent_folder", createdAt=now)
    session.add(child_folder)
    session.commit()
    
    # Create files (after folders exist)
    files = [
        File(id="file_1", name="User 1 File", folderId="folder_1", ownerId="user_1", createdAt=now),
        File(id="file_inside_child", name="File Inside Child", folderId="child_folder", ownerId="user_1", createdAt=now),
        File(id="shared_file", name="Shared File", folderId="folder_1", ownerId="user_1", createdAt=now),
    ]
    session.add_all(files)
    session.commit()
    
    # Create permissions
    permissions = [
        Permission(id="perm_1", userId="user_2", resourceType="folder", resourceId="parent_folder", level="view", createdAt=now),
        Permission(id="perm_2", userId="user_3", resourceType="file", resourceId="shared_file", level="view", createdAt=now),
    ]
    session.add_all(permissions)
    session.commit()


def seed_heavy_user_data(session, num_folders=100, num_files_per_folder=50):
    """Seed a heavy user with lots of folders and files for performance testing."""
    now = datetime.now()
    
    # Create heavy user and other users first
    heavy_user = User(id="heavy_user", email="heavy@test.com", createdAt=now)
    session.add(heavy_user)
    
    other_users = []
    for i in range(20):
        user = User(id=f"other_user_{i}", email=f"other{i}@test.com", createdAt=now)
        other_users.append(user)
    session.add_all(other_users)
    session.commit()
    
    # Create root folders first (no parent)
    root_folders = []
    for i in range(min(10, num_folders)):
        folder = Folder(
            id=f"folder_{i}",
            name=f"Root Folder {i}",
            ownerId="heavy_user" if i % 3 == 0 else f"other_user_{i % 20}",
            parentId=None,
            createdAt=now
        )
        root_folders.append(folder)
    session.add_all(root_folders)
    session.commit()
    
    # Create nested folders (with parents)
    all_folders = list(root_folders)
    for i in range(10, num_folders):
        parent_idx = i % len(root_folders)
        folder = Folder(
            id=f"folder_{i}",
            name=f"Folder {i}",
            ownerId="heavy_user" if i % 3 == 0 else f"other_user_{i % 20}",
            parentId=root_folders[parent_idx].id,
            createdAt=now
        )
        all_folders.append(folder)
    if len(all_folders) > len(root_folders):
        session.add_all(all_folders[len(root_folders):])
        session.commit()
    
    # Create files in batches
    files = []
    for i, folder in enumerate(all_folders):
        for j in range(num_files_per_folder):
            file = File(
                id=f"file_{i}_{j}",
                name=f"File {i}-{j}",
                folderId=folder.id,
                ownerId="heavy_user" if (i + j) % 4 == 0 else f"other_user_{(i + j) % 20}",
                createdAt=now
            )
            files.append(file)
    
    batch_size = 500
    for i in range(0, len(files), batch_size):
        session.add_all(files[i:i+batch_size])
        session.commit()
    
    # Create permissions for heavy_user
    permissions = []
    perm_id = 0
    
    for i in range(0, num_folders, 3):
        perm = Permission(
            id=f"heavy_perm_{perm_id}",
            userId="heavy_user",
            resourceType="folder",
            resourceId=f"folder_{i}",
            level="view",
            createdAt=now
        )
        permissions.append(perm)
        perm_id += 1
    
    for i in range(0, len(files), 10):
        perm = Permission(
            id=f"heavy_perm_{perm_id}",
            userId="heavy_user",
            resourceType="file",
            resourceId=files[i].id,
            level="edit",
            createdAt=now
        )
        permissions.append(perm)
        perm_id += 1
    
    session.add_all(permissions)
    session.commit()
    
    return {
        "users": len(other_users) + 1,
        "folders": len(all_folders),
        "files": len(files),
        "permissions": len(permissions)
    }


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
