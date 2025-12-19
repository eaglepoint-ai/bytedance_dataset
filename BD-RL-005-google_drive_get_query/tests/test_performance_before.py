"""
Performance tests for repository_before (naive implementation).

Run independently with:
    docker compose run --rm app pytest -v tests/test_performance_before.py -s
"""
import pytest
from tests.utils import measure_performance, print_performance_results


class TestBeforePerformance:
    """Performance tests for the naive (before) implementation."""
    
    def test_dashboard_performance(self, perf_client):
        """
        Test that the dashboard endpoint responds within acceptable time.
        Uses heavy_user with many accessible resources.
        """
        results = measure_performance(perf_client, "heavy_user", num_iterations=5)
        
        print_performance_results(results, "BEFORE Implementation - Performance Results")
        
        # Assert reasonable performance
        assert results["avg_ms"] < 5000, \
            f"Average response time {results['avg_ms']:.2f}ms exceeds 5s threshold"
    
    def test_multiple_users_performance(self, perf_client):
        """Test performance across multiple different users."""
        users_to_test = ["heavy_user", "other_user_0", "other_user_5", "other_user_10"]
        results = {}
        
        for user_id in users_to_test:
            results[user_id] = measure_performance(perf_client, user_id, num_iterations=1, warmup=False)
        
        print(f"\n{'='*60}")
        print("BEFORE Implementation - Multi-user Performance")
        print(f"{'='*60}")
        print(f"{'User':<15} {'Time (ms)':<12} {'Folders':<10} {'Files':<10}")
        print(f"{'-'*60}")
        for user_id, stats in results.items():
            print(f"{user_id:<15} {stats['avg_ms']:<12.2f} {stats['folders']:<10} {stats['files']:<10}")
        print(f"{'='*60}")
        
        # All users should respond within reasonable time
        for user_id, stats in results.items():
            assert stats["avg_ms"] < 5000, f"User {user_id} took {stats['avg_ms']:.2f}ms"
