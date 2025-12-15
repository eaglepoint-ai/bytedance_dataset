"""
Performance comparison tests between repository_before and repository_after.

This test file runs both implementations against the same dataset and
compares their performance and correctness.
"""
import os
import time
import pytest
from datetime import datetime

# Import both implementations
from repository_before.app import create_app as create_app_before
from repository_after.app import create_app as create_app_after
from repository_before import db as db_before
from repository_before.models import User, Folder, File, Permission


def clear_database(session):
    """Clear all data from the database."""
    session.query(Permission).delete()
    session.query(File).delete()
    session.query(Folder).delete()
    session.query(User).delete()
    session.commit()


def seed_comparison_data(session, num_folders=100, num_files_per_folder=50):
    """Seed data for comparison tests."""
    now = datetime.now()
    
    # Create users
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


class TestPerformanceComparison:
    """Compare performance between before and after implementations."""
    
    @pytest.fixture(autouse=True)
    def setup_database(self, tmp_path):
        """Setup database once for all comparison tests."""
        self.db_url = os.environ.get("DATABASE_URL")
        if not self.db_url:
            db_path = tmp_path / "comparison_test.db"
            self.db_url = f"sqlite:///{db_path}"
        
        # Initialize before app (creates tables)
        self.before_app = create_app_before(self.db_url)
        self.before_app.config["TESTING"] = True
        
        # Seed data
        session = db_before.SessionLocal()
        try:
            clear_database(session)
            stats = seed_comparison_data(session, num_folders=100, num_files_per_folder=50)
            print(f"\nSeeded comparison test data: {stats}")
        finally:
            session.close()
        
        # Initialize after app (same database)
        self.after_app = create_app_after(self.db_url)
        self.after_app.config["TESTING"] = True
        
        yield
        
        # Cleanup
        session = db_before.SessionLocal()
        try:
            clear_database(session)
        finally:
            session.close()
    
    def test_before_vs_after_correctness(self):
        """Verify that both implementations return the same results."""
        users_to_test = ["heavy_user", "other_user_0", "other_user_1"]
        
        for user_id in users_to_test:
            # Test before implementation
            with self.before_app.test_client() as client:
                before_res = client.get(f"/dashboard/{user_id}").json
            
            # Test after implementation  
            with self.after_app.test_client() as client:
                after_res = client.get(f"/dashboard/{user_id}").json
            
            # Sort for comparison
            before_folders = sorted(before_res["folders"])
            after_folders = sorted(after_res["folders"])
            before_files = sorted(before_res["files"])
            after_files = sorted(after_res["files"])
            
            assert before_folders == after_folders, \
                f"Folder mismatch for {user_id}: before={len(before_folders)}, after={len(after_folders)}"
            assert before_files == after_files, \
                f"File mismatch for {user_id}: before={len(before_files)}, after={len(after_files)}"
        
        print("\n✅ Both implementations return identical results!")
    
    def test_before_vs_after_performance(self):
        """Compare performance between before and after implementations."""
        num_iterations = 5
        
        # Warm up
        with self.before_app.test_client() as client:
            client.get("/dashboard/heavy_user")
        with self.after_app.test_client() as client:
            client.get("/dashboard/heavy_user")
        
        # Measure BEFORE performance
        before_times = []
        with self.before_app.test_client() as client:
            for _ in range(num_iterations):
                start = time.time()
                client.get("/dashboard/heavy_user")
                before_times.append(time.time() - start)
        
        # Measure AFTER performance
        after_times = []
        with self.after_app.test_client() as client:
            for _ in range(num_iterations):
                start = time.time()
                res = client.get("/dashboard/heavy_user")
                after_times.append(time.time() - start)
                data = res.json
        
        before_avg = sum(before_times) / len(before_times)
        after_avg = sum(after_times) / len(after_times)
        improvement = ((before_avg - after_avg) / before_avg) * 100 if before_avg > 0 else 0
        speedup = before_avg / after_avg if after_avg > 0 else float('inf')
        
        print(f"\n{'='*60}")
        print("PERFORMANCE COMPARISON (heavy_user)")
        print(f"{'='*60}")
        print(f"BEFORE (naive):     {before_avg*1000:.2f} ms avg")
        print(f"AFTER (optimized):  {after_avg*1000:.2f} ms avg")
        print(f"{'='*60}")
        print(f"Improvement:        {improvement:.1f}%")
        print(f"Speedup:            {speedup:.2f}x faster")
        print(f"Folders returned:   {len(data['folders'])}")
        print(f"Files returned:     {len(data['files'])}")
        print(f"{'='*60}")
    
    def test_scaling_comparison(self):
        """Test how each implementation scales with different users."""
        users = ["heavy_user", "other_user_0", "other_user_5", "other_user_10"]
        
        before_results = {}
        after_results = {}
        
        for user_id in users:
            # Before
            with self.before_app.test_client() as client:
                start = time.time()
                res = client.get(f"/dashboard/{user_id}")
                before_time = time.time() - start
                if res.status_code == 200:
                    data = res.json
                    before_results[user_id] = {
                        "time_ms": before_time * 1000,
                        "folders": len(data["folders"]),
                        "files": len(data["files"])
                    }
            
            # After
            with self.after_app.test_client() as client:
                start = time.time()
                res = client.get(f"/dashboard/{user_id}")
                after_time = time.time() - start
                if res.status_code == 200:
                    data = res.json
                    after_results[user_id] = {
                        "time_ms": after_time * 1000,
                        "folders": len(data["folders"]),
                        "files": len(data["files"])
                    }
        
        print(f"\n{'='*80}")
        print("SCALING COMPARISON ACROSS USERS")
        print(f"{'='*80}")
        print(f"{'User':<15} {'Before (ms)':<12} {'After (ms)':<12} {'Speedup':<10} {'Folders':<10} {'Files':<10}")
        print(f"{'-'*80}")
        
        for user_id in users:
            if user_id in before_results and user_id in after_results:
                b = before_results[user_id]
                a = after_results[user_id]
                speedup = b["time_ms"] / a["time_ms"] if a["time_ms"] > 0 else 0
                print(f"{user_id:<15} {b['time_ms']:<12.2f} {a['time_ms']:<12.2f} {speedup:<10.2f}x {a['folders']:<10} {a['files']:<10}")
        
        print(f"{'='*80}")
