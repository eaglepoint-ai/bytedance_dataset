"""Performance tests to demonstrate speed improvements after refactoring."""
import time
import pytest
from format_ids import format_ids


class TestPerformanceImprovements:
    """Validate that refactored code maintains or improves performance."""
    
    def test_basic_performance(self):
        """Measure execution time for basic formatting."""
        test_ids = ['user123', 'admin456', 'guest789'] * 100
        
        start = time.perf_counter()
        result = format_ids(test_ids)
        duration = time.perf_counter() - start
        
        print(f"\n300 ID formatting completed in {duration:.4f}s")
        print(f"Average per ID: {(duration / 300) * 1000:.3f}ms")
        
        # Should be very fast
        assert duration < 0.1, f"Performance issue: {duration}s for 300 IDs"
        assert len(result) == 300
    
    def test_large_batch_performance(self):
        """Test performance with larger batches."""
        test_ids = [f'id_{i}_test' for i in range(1000)]
        
        start = time.perf_counter()
        result = format_ids(test_ids)
        duration = time.perf_counter() - start
        
        print(f"\n1000 IDs formatted in {duration:.4f}s")
        print(f"Throughput: {1000 / duration:.0f} IDs/second")
        
        assert duration < 0.5, f"Large batch too slow: {duration}s"
        assert len(result) == 1000
    
    def test_repeated_calls_performance(self):
        """Test performance with repeated function calls.
        
        FAIL_TO_PASS: This test has a stricter threshold that fails in 'before' 
        (slower due to regex recompilation) but passes in 'after' (optimized).
        """
        test_ids = ['test_id_123', 'user_456', 'admin_789']
        iterations = 1000
        
        start = time.perf_counter()
        for _ in range(iterations):
            result = format_ids(test_ids)
        duration = time.perf_counter() - start
        
        per_call_us = (duration / iterations) * 1_000_000
        print(f"\n{iterations} calls completed in {duration:.4f}s")
        print(f"Average per call: {per_call_us:.2f} μs")
        
        # Stricter threshold: will FAIL in 'before' (typically ~150-200μs) 
        # but PASS in 'after' (typically ~80-100μs)
        assert per_call_us < 120, f"Per-call performance too slow: {per_call_us:.2f} μs (threshold: 120μs)"
    
    def test_special_chars_performance(self):
        """Test performance with many special characters."""
        test_ids = ['id!!!test___value---123'] * 500
        
        start = time.perf_counter()
        result = format_ids(test_ids)
        duration = time.perf_counter() - start
        
        print(f"\n500 IDs with special chars formatted in {duration:.4f}s")
        
        assert duration < 0.2, f"Special char handling too slow: {duration}s"
        assert all(r == 'ID-TEST-VALUE-123' for r in result)
    
    def test_mixed_workload_performance(self):
        """Test performance with mixed realistic workload."""
        test_ids = [
            'user_123',
            'admin@example.com',
            'temp!!!test',
            None,
            '  spaces  ',
            'ALREADY-UPPER',
            'unicode_café'
        ] * 200
        
        start = time.perf_counter()
        result = format_ids(test_ids)
        duration = time.perf_counter() - start
        
        print(f"\n1400 mixed IDs formatted in {duration:.4f}s")
        print(f"Average per ID: {(duration / 1400) * 1000:.3f}ms")
        
        # None values are filtered out, so result is smaller
        assert len(result) == 1200  # 200 * 6 (excluding None)
        assert duration < 0.3, f"Mixed workload too slow: {duration}s"
    
    def test_memory_efficiency(self):
        """Test that function doesn't create excessive temporary objects."""
        # This is more of a sanity check - the function should be efficient
        import sys
        
        test_ids = [f'id_{i}' for i in range(10000)]
        
        # Rough estimate of memory usage
        start_size = sys.getsizeof(test_ids)
        result = format_ids(test_ids)
        result_size = sys.getsizeof(result)
        
        print(f"\nInput size: {start_size:,} bytes")
        print(f"Output size: {result_size:,} bytes")
        
        # Result should be similar size to input (not dramatically larger)
        assert result_size < start_size * 2, "Excessive memory usage"
    
    def test_scalability(self):
        """Test that performance scales linearly."""
        sizes = [100, 500, 1000]
        times = []
        
        for size in sizes:
            test_ids = [f'id_{i}' for i in range(size)]
            
            start = time.perf_counter()
            result = format_ids(test_ids)
            duration = time.perf_counter() - start
            times.append(duration)
            
            print(f"\n{size} IDs: {duration:.4f}s ({size/duration:.0f} IDs/sec)")
        
        # Check that time increases roughly linearly (within 3x tolerance)
        # Time for 1000 should be ~10x time for 100
        ratio = times[2] / times[0]
        print(f"\nScaling ratio (1000/100): {ratio:.2f}x")
        
        # Should scale linearly, allow some variance
        assert ratio < 15, f"Poor scalability: {ratio:.2f}x slowdown for 10x data"
    
    def test_regex_compilation_overhead(self):
        """Measure if regex compilation overhead is avoided."""
        # This test highlights the performance difference between versions
        # The 'after' version pre-compiles the regex, 'before' does not
        
        test_ids = ['test_id_123'] * 1000
        
        start = time.perf_counter()
        result = format_ids(test_ids)
        duration = time.perf_counter() - start
        
        per_id_us = (duration / 1000) * 1_000_000
        print(f"\nPer-ID processing time: {per_id_us:.2f} μs")
        
        # In optimized version, this should be very fast
        # In non-optimized version with regex recompilation, it will be slower
        assert per_id_us < 100, f"Regex overhead too high: {per_id_us:.2f} μs per ID"
