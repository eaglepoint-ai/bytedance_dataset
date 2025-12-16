"""
Comparison tests between repository_before and repository_after.

This test file runs both implementations against the same dataset and
compares their performance and correctness.

Run with:
    docker compose run --rm app pytest -v tests/test_comparison.py -s
"""
import os
import pytest
from repository_before.app import create_app as create_app_before
from repository_after.app import create_app as create_app_after
from repository_before import db as db_before
from tests.utils import (
    clear_database,
    seed_heavy_user_data,
    measure_performance,
    print_comparison_results,
    print_multi_user_comparison
)


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
            stats = seed_heavy_user_data(session, num_folders=100, num_files_per_folder=50)
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
    
    def test_correctness(self):
        """
        Verify that both implementations return the same results.
        This ensures the optimized version is functionally correct.
        """
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
    
    def test_performance_comparison(self):
        """
        Compare performance between before and after implementations.
        Measures the speedup achieved by the optimization.
        """
        # Measure BEFORE performance
        with self.before_app.test_client() as client:
            before_results = measure_performance(client, "heavy_user", num_iterations=5)
        
        # Measure AFTER performance
        with self.after_app.test_client() as client:
            after_results = measure_performance(client, "heavy_user", num_iterations=5)
        
        # Print comparison
        comparison = print_comparison_results(
            before_results, 
            after_results, 
            "PERFORMANCE COMPARISON (heavy_user)"
        )
        
        # Assert optimization provides improvement
        assert comparison["speedup"] >= 1.0, \
            "Optimized version should not be slower than naive version"
    
    def test_scaling_comparison(self):
        """
        Test how each implementation scales with different users.
        Shows performance across users with varying resource access.
        """
        users = ["heavy_user", "other_user_0", "other_user_5", "other_user_10"]
        
        before_results = {}
        after_results = {}
        
        for user_id in users:
            # Before
            with self.before_app.test_client() as client:
                before_results[user_id] = measure_performance(client, user_id, num_iterations=1, warmup=False)
            
            # After
            with self.after_app.test_client() as client:
                after_results[user_id] = measure_performance(client, user_id, num_iterations=1, warmup=False)
        
        # Print comparison table
        print_multi_user_comparison(
            before_results, 
            after_results, 
            "SCALING COMPARISON ACROSS USERS"
        )
