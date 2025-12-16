"""
Shared test utilities for seeding data and running performance benchmarks.

This module provides reusable functions for:
- Database seeding (test data and large datasets)
- Performance measurement
- Result comparison
"""
import time
from datetime import datetime
from repository_before.models import User, Folder, File, Permission


def clear_database(session):
    """Clear all data from the database (respecting FK constraints)."""
    session.query(Permission).delete()
    session.query(File).delete()
    session.query(Folder).delete()
    session.query(User).delete()
    session.commit()


def seed_test_data(session):
    """Seed the database with basic test data for unit tests."""
    now = datetime.now()
    
    # Create test users
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
    
    # Create files
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
    """
    Seed a heavy user with lots of folders and files for performance testing.
    
    Returns stats about the seeded data.
    """
    now = datetime.now()
    
    # Create heavy user and other users
    heavy_user = User(id="heavy_user", email="heavy@test.com", createdAt=now)
    session.add(heavy_user)
    
    other_users = []
    for i in range(20):
        user = User(id=f"other_user_{i}", email=f"other{i}@test.com", createdAt=now)
        other_users.append(user)
    session.add_all(other_users)
    session.commit()
    
    # Create root folders
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
    
    # Create nested folders
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


def measure_performance(client, user_id, num_iterations=5, warmup=True):
    """
    Measure performance of the dashboard endpoint.
    
    Returns dict with timing stats and response data.
    """
    # Warm up
    if warmup:
        client.get(f"/dashboard/{user_id}")
    
    times = []
    data = None
    
    for _ in range(num_iterations):
        start = time.time()
        response = client.get(f"/dashboard/{user_id}")
        duration = time.time() - start
        times.append(duration)
        
        if response.status_code == 200:
            data = response.json
    
    return {
        "times": times,
        "min_ms": min(times) * 1000,
        "max_ms": max(times) * 1000,
        "avg_ms": (sum(times) / len(times)) * 1000,
        "folders": len(data["folders"]) if data else 0,
        "files": len(data["files"]) if data else 0,
        "data": data
    }


def print_performance_results(results, title="Performance Results"):
    """Print formatted performance results."""
    print(f"\n{'='*50}")
    print(f"{title} ({len(results['times'])} iterations):")
    print(f"{'='*50}")
    print(f"  Min time:  {results['min_ms']:.2f} ms")
    print(f"  Max time:  {results['max_ms']:.2f} ms")
    print(f"  Avg time:  {results['avg_ms']:.2f} ms")
    print(f"  Folders:   {results['folders']}")
    print(f"  Files:     {results['files']}")
    print(f"{'='*50}")


def print_comparison_results(before_results, after_results, title="PERFORMANCE COMPARISON"):
    """Print formatted comparison between before and after results."""
    before_avg = before_results["avg_ms"]
    after_avg = after_results["avg_ms"]
    improvement = ((before_avg - after_avg) / before_avg) * 100 if before_avg > 0 else 0
    speedup = before_avg / after_avg if after_avg > 0 else float('inf')
    
    print(f"\n{'='*60}")
    print(title)
    print(f"{'='*60}")
    print(f"BEFORE (naive):     {before_avg:.2f} ms avg")
    print(f"AFTER (optimized):  {after_avg:.2f} ms avg")
    print(f"{'='*60}")
    print(f"Improvement:        {improvement:.1f}%")
    print(f"Speedup:            {speedup:.2f}x faster")
    print(f"Folders returned:   {after_results['folders']}")
    print(f"Files returned:     {after_results['files']}")
    print(f"{'='*60}")
    
    return {
        "improvement_pct": improvement,
        "speedup": speedup
    }


def print_multi_user_comparison(before_results_dict, after_results_dict, title="SCALING COMPARISON"):
    """Print formatted multi-user comparison table."""
    print(f"\n{'='*80}")
    print(title)
    print(f"{'='*80}")
    print(f"{'User':<15} {'Before (ms)':<12} {'After (ms)':<12} {'Speedup':<10} {'Folders':<10} {'Files':<10}")
    print(f"{'-'*80}")
    
    for user_id in before_results_dict:
        if user_id in after_results_dict:
            b = before_results_dict[user_id]
            a = after_results_dict[user_id]
            speedup = b["avg_ms"] / a["avg_ms"] if a["avg_ms"] > 0 else 0
            print(f"{user_id:<15} {b['avg_ms']:<12.2f} {a['avg_ms']:<12.2f} {speedup:<10.2f}x {a['folders']:<10} {a['files']:<10}")
    
    print(f"{'='*80}")

