"""
Performance tests for repository_after (optimized implementation).

Run independently with:
    docker compose run --rm app pytest -v tests/test_performance_after.py -s
"""
import os
import pytest
from repository_after.app import create_app
from repository_after import db
from tests.utils import (
    clear_database, 
    seed_heavy_user_data, 
    measure_performance, 
    print_performance_results
)


@pytest.fixture
def after_perf_client(tmp_path):
    """Fixture for performance tests with repository_after (optimized)."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        db_path = tmp_path / "perf_after_test.db"
        db_url = f"sqlite:///{db_path}"

    app = create_app(db_url)
    app.config["TESTING"] = True
    
    # Clear and seed heavy test data
    session = db.SessionLocal()
    try:
        clear_database(session)
        stats = seed_heavy_user_data(session, num_folders=100, num_files_per_folder=50)
        print(f"\nSeeded performance test data (AFTER): {stats}")
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


class TestAfterPerformance:
    """Performance tests for the optimized (after) implementation."""
    
    def test_dashboard_performance(self, after_perf_client):
        """
        Test that the dashboard endpoint responds within acceptable time.
        Uses heavy_user with many accessible resources.
        """
        results = measure_performance(after_perf_client, "heavy_user", num_iterations=5)
        
        print_performance_results(results, "AFTER Implementation - Performance Results")
        
        # Assert reasonable performance (should be faster than before)
        assert results["avg_ms"] < 1000, \
            f"Average response time {results['avg_ms']:.2f}ms exceeds 1s threshold"
    
    def test_multiple_users_performance(self, after_perf_client):
        """Test performance across multiple different users."""
        users_to_test = ["heavy_user", "other_user_0", "other_user_5", "other_user_10"]
        results = {}
        
        for user_id in users_to_test:
            results[user_id] = measure_performance(after_perf_client, user_id, num_iterations=1, warmup=False)
        
        print(f"\n{'='*60}")
        print("AFTER Implementation - Multi-user Performance")
        print(f"{'='*60}")
        print(f"{'User':<15} {'Time (ms)':<12} {'Folders':<10} {'Files':<10}")
        print(f"{'-'*60}")
        for user_id, stats in results.items():
            print(f"{user_id:<15} {stats['avg_ms']:<12.2f} {stats['folders']:<10} {stats['files']:<10}")
        print(f"{'='*60}")
        
        # All users should respond within reasonable time (faster threshold)
        for user_id, stats in results.items():
            assert stats["avg_ms"] < 1000, f"User {user_id} took {stats['avg_ms']:.2f}ms"

