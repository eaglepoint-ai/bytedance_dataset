import time
import pytest


def test_dashboard_performance(perf_client):
    """
    Test that the dashboard endpoint responds within acceptable time.
    
    This test uses a 'heavy_user' with many accessible resources
    to measure real-world performance.
    """
    # Warm up request
    perf_client.get("/dashboard/heavy_user")
    
    # Measure multiple requests for consistency
    times = []
    num_iterations = 5
    
    for _ in range(num_iterations):
        start = time.time()
        response = perf_client.get("/dashboard/heavy_user")
        duration = time.time() - start
        times.append(duration)
        
        # Verify response is valid
        assert response.status_code == 200
        data = response.json
        assert "folders" in data
        assert "files" in data
    
    avg_time = sum(times) / len(times)
    max_time = max(times)
    min_time = min(times)
    
    print(f"\n{'='*50}")
    print(f"Performance Results ({num_iterations} iterations):")
    print(f"{'='*50}")
    print(f"  Min time:  {min_time*1000:.2f} ms")
    print(f"  Max time:  {max_time*1000:.2f} ms")
    print(f"  Avg time:  {avg_time*1000:.2f} ms")
    print(f"  Folders:   {len(data['folders'])}")
    print(f"  Files:     {len(data['files'])}")
    print(f"{'='*50}")
    
    # Assert reasonable performance (adjust based on optimization goals)
    assert avg_time < 5.0, f"Average response time {avg_time:.2f}s exceeds 5s threshold"


def test_multiple_users_performance(perf_client):
    """
    Test performance across multiple different users.
    """
    users_to_test = ["heavy_user", "user_0", "user_1", "user_2"]
    results = {}
    
    for user_id in users_to_test:
        start = time.time()
        response = perf_client.get(f"/dashboard/{user_id}")
        duration = time.time() - start
        
        if response.status_code == 200:
            data = response.json
            results[user_id] = {
                "time_ms": duration * 1000,
                "folders": len(data["folders"]),
                "files": len(data["files"])
            }
    
    print(f"\n{'='*60}")
    print("Multi-user Performance Results:")
    print(f"{'='*60}")
    print(f"{'User':<15} {'Time (ms)':<12} {'Folders':<10} {'Files':<10}")
    print(f"{'-'*60}")
    for user_id, stats in results.items():
        print(f"{user_id:<15} {stats['time_ms']:<12.2f} {stats['folders']:<10} {stats['files']:<10}")
    print(f"{'='*60}")
    
    # All users should respond within reasonable time
    for user_id, stats in results.items():
        assert stats["time_ms"] < 5000, f"User {user_id} took {stats['time_ms']:.2f}ms"
