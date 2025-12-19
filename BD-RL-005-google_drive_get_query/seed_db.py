#!/usr/bin/env python3
"""
Seed script to populate the database with a large dataset for performance testing.

Usage:
    python seed_db.py [--users N] [--folders N] [--files-per-folder N]

Example:
    python seed_db.py --users 50 --folders 200 --files-per-folder 100
"""
import argparse
import random
from datetime import datetime, timedelta
from repository_before import db
from repository_before.models import User, Folder, File, Permission


def random_date(start_days_ago=365):
    """Generate a random datetime within the last N days."""
    days_ago = random.randint(0, start_days_ago)
    return datetime.now() - timedelta(days=days_ago)


def clear_database(session):
    """Clear all data from the database (respecting FK order)."""
    session.query(Permission).delete()
    session.query(File).delete()
    session.query(Folder).delete()
    session.query(User).delete()
    session.commit()


def seed_database(num_users=50, num_folders=200, num_files_per_folder=50):
    """
    Seed the database with a large dataset.
    
    This creates:
    - Multiple users
    - Nested folder hierarchy
    - Many files in each folder
    - Complex permission relationships
    """
    print(f"Seeding database with:")
    print(f"  - {num_users} users")
    print(f"  - {num_folders} folders")
    print(f"  - ~{num_folders * num_files_per_folder} files")
    print()
    
    session = db.SessionLocal()
    
    try:
        # Clear existing data
        print("Clearing existing data...")
        clear_database(session)
        
        # Create users first (no FK dependencies)
        print("Creating users...")
        users = []
        for i in range(num_users):
            user = User(
                id=f"user_{i}",
                email=f"user{i}@example.com",
                createdAt=random_date()
            )
            users.append(user)
        
        # Add special test users
        special_users = [
            User(id="heavy_user", email="heavy@example.com", createdAt=random_date()),
            User(id="user_1", email="user1@example.com", createdAt=random_date()),
            User(id="user_2", email="user2@example.com", createdAt=random_date()),
            User(id="user_3", email="user3@example.com", createdAt=random_date()),
        ]
        users.extend(special_users)
        session.add_all(users)
        session.commit()  # Commit users first
        print(f"  Created {len(users)} users.")
        
        # Create root folders first (no parent FK)
        print("Creating folders...")
        num_root_folders = max(10, num_folders // 10)
        root_folders = []
        
        for i in range(num_root_folders):
            owner = random.choice(users)
            folder = Folder(
                id=f"folder_{i}",
                name=f"Root Folder {i}",
                ownerId=owner.id,
                parentId=None,
                createdAt=random_date()
            )
            root_folders.append(folder)
        
        # Add special test folders (roots)
        special_roots = [
            Folder(id="folder_1", name="User 1 Folder", ownerId="user_1", parentId=None, createdAt=random_date()),
            Folder(id="parent_folder", name="Parent Folder", ownerId="user_1", parentId=None, createdAt=random_date()),
        ]
        root_folders.extend(special_roots)
        session.add_all(root_folders)
        session.commit()  # Commit root folders
        
        # Create nested folders (with parent FK)
        all_folders = list(root_folders)
        nested_folders = []
        for i in range(num_root_folders, num_folders):
            owner = random.choice(users)
            parent = random.choice(root_folders)  # Only reference root folders
            folder = Folder(
                id=f"folder_{i}",
                name=f"Folder {i}",
                ownerId=owner.id,
                parentId=parent.id,
                createdAt=random_date()
            )
            nested_folders.append(folder)
            all_folders.append(folder)
        
        # Add special child folder
        child_folder = Folder(id="child_folder", name="Child Folder", ownerId="user_1", parentId="parent_folder", createdAt=random_date())
        nested_folders.append(child_folder)
        all_folders.append(child_folder)
        
        session.add_all(nested_folders)
        session.commit()  # Commit nested folders
        print(f"  Created {len(all_folders)} folders.")
        
        # Create files (after folders exist)
        print("Creating files...")
        files = []
        file_id = 0
        
        for folder in all_folders:
            num_files = random.randint(num_files_per_folder // 2, num_files_per_folder)
            for _ in range(num_files):
                owner = random.choice(users)
                file = File(
                    id=f"file_{file_id}",
                    name=f"File {file_id}.txt",
                    folderId=folder.id,
                    ownerId=owner.id,
                    createdAt=random_date()
                )
                files.append(file)
                file_id += 1
        
        # Add special test files
        special_files = [
            File(id="file_1", name="User 1 File", folderId="folder_1", ownerId="user_1", createdAt=random_date()),
            File(id="file_inside_child", name="File Inside Child", folderId="child_folder", ownerId="user_1", createdAt=random_date()),
            File(id="shared_file", name="Shared File", folderId="folder_1", ownerId="user_1", createdAt=random_date()),
        ]
        files.extend(special_files)
        
        # Add files in batches
        batch_size = 500
        for i in range(0, len(files), batch_size):
            session.add_all(files[i:i+batch_size])
            session.commit()
        print(f"  Created {len(files)} files.")
        
        # Create permissions (after users and resources exist)
        print("Creating permissions...")
        permissions = []
        perm_id = 0
        
        # Give heavy_user access to many resources
        for i in range(0, len(all_folders), 3):
            perm = Permission(
                id=f"perm_{perm_id}",
                userId="heavy_user",
                resourceType="folder",
                resourceId=all_folders[i].id,
                level=random.choice(["view", "comment", "edit"]),
                createdAt=random_date()
            )
            permissions.append(perm)
            perm_id += 1
        
        for i in range(0, len(files), 5):
            perm = Permission(
                id=f"perm_{perm_id}",
                userId="heavy_user",
                resourceType="file",
                resourceId=files[i].id,
                level=random.choice(["view", "comment", "edit"]),
                createdAt=random_date()
            )
            permissions.append(perm)
            perm_id += 1
        
        # Create random permissions for other users
        for user in users[:num_users]:
            num_perms = random.randint(5, 20)
            for _ in range(num_perms):
                if random.random() < 0.6:
                    resource_type = "folder"
                    resource_id = random.choice(all_folders).id
                else:
                    resource_type = "file"
                    resource_id = random.choice(files).id
                
                perm = Permission(
                    id=f"perm_{perm_id}",
                    userId=user.id,
                    resourceType=resource_type,
                    resourceId=resource_id,
                    level=random.choice(["view", "comment", "edit"]),
                    createdAt=random_date()
                )
                permissions.append(perm)
                perm_id += 1
        
        # Add special test permissions
        special_permissions = [
            Permission(id="test_perm_1", userId="user_2", resourceType="folder", resourceId="parent_folder", level="view", createdAt=random_date()),
            Permission(id="test_perm_2", userId="user_3", resourceType="file", resourceId="shared_file", level="view", createdAt=random_date()),
        ]
        permissions.extend(special_permissions)
        session.add_all(permissions)
        session.commit()
        print(f"  Created {len(permissions)} permissions.")
        
        print()
        print("=" * 50)
        print("Database seeding complete!")
        print("=" * 50)
        print(f"Total users:       {len(users)}")
        print(f"Total folders:     {len(all_folders)}")
        print(f"Total files:       {len(files)}")
        print(f"Total permissions: {len(permissions)}")
        print()
        print("Special test users: user_1, user_2, user_3, heavy_user")
        
    except Exception as e:
        session.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the database with test data")
    parser.add_argument("--users", type=int, default=50, help="Number of users to create")
    parser.add_argument("--folders", type=int, default=200, help="Number of folders to create")
    parser.add_argument("--files-per-folder", type=int, default=50, help="Average files per folder")
    
    args = parser.parse_args()
    
    # Initialize database
    db.init_db()
    
    seed_database(
        num_users=args.users,
        num_folders=args.folders,
        num_files_per_folder=args.files_per_folder
    )
