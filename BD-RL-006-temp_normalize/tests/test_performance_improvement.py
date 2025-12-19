"""Performance tests to demonstrate speed improvements after refactoring."""
import time
import pytest
from ids import normalize_id


class TestPerformanceImprovements:
    """Validate that refactored code maintains or improves performance."""
    
    def test_basic_performance(self):
        """Measure execution time for basic normalization."""
        test_cases = [
            "ABC_123",
            " Abc 123 ",
            "temp_user_1",
            " TEMP__a b!!c ",
            "!!!abc!!!",
            "",
        ]
        
        start = time.perf_counter()
        for test_input in test_cases * 100:  # Run 100 times each
            normalize_id(test_input)
        duration = time.perf_counter() - start
        
        print(f"\n600 normalizations completed in {duration:.4f}s")
        print(f"Average per call: {(duration / 600) * 1000:.3f}ms")
        
        # Should be very fast for simple string operations
        assert duration < 0.1, f"Performance issue: {duration}s for 600 calls"
    
    def test_temp_prefix_detection_performance(self):
        """Ensure TEMP prefix detection doesn't significantly slow down processing."""
        temp_ids = [f"temp_user_{i}" for i in range(100)]
        non_temp_ids = [f"user_{i}" for i in range(100)]
        
        # Test TEMP IDs
        start = time.perf_counter()
        for tid in temp_ids:
            normalize_id(tid)
        temp_duration = time.perf_counter() - start
        
        # Test non-TEMP IDs
        start = time.perf_counter()
        for tid in non_temp_ids:
            normalize_id(tid)
        non_temp_duration = time.perf_counter() - start
        
        print(f"\nTEMP IDs: {temp_duration:.4f}s")
        print(f"Non-TEMP IDs: {non_temp_duration:.4f}s")
        
        # Both should be fast
        assert temp_duration < 0.05, f"TEMP processing too slow: {temp_duration}s"
        assert non_temp_duration < 0.05, f"Non-TEMP processing too slow: {non_temp_duration}s"
    
    def test_long_string_performance(self):
        """Test performance with longer strings."""
        long_strings = [
            "temp_" + "_".join([f"segment{i}" for i in range(20)]),
            "_".join([f"segment{i}" for i in range(20)]),
            "TEMP_" + "!" * 100 + "test",
        ]
        
        start = time.perf_counter()
        for s in long_strings * 50:
            normalize_id(s)
        duration = time.perf_counter() - start
        
        print(f"\n150 long string normalizations in {duration:.4f}s")
        assert duration < 0.1, f"Long string performance issue: {duration}s"
    
    def test_regex_vs_loop_performance(self):
        """Compare performance characteristics of different approaches."""
        # This test documents performance, doesn't assert specific values
        test_input = "user_id_123_test"
        iterations = 1000
        
        start = time.perf_counter()
        for _ in range(iterations):
            normalize_id(test_input)
        duration = time.perf_counter() - start
        
        per_call_us = (duration / iterations) * 1_000_000
        print(f"\nNon-TEMP ID normalization: {per_call_us:.2f} μs per call")
        
        # Test TEMP version
        test_input_temp = "temp_user_id_123"
        start = time.perf_counter()
        for _ in range(iterations):
            normalize_id(test_input_temp)
        duration_temp = time.perf_counter() - start
        
        per_call_temp_us = (duration_temp / iterations) * 1_000_000
        print(f"TEMP ID normalization: {per_call_temp_us:.2f} μs per call")
        
        # Both should be under 100 microseconds per call
        assert per_call_us < 100, f"Non-TEMP too slow: {per_call_us:.2f} μs"
        assert per_call_temp_us < 100, f"TEMP too slow: {per_call_temp_us:.2f} μs"
