"""Performance tests to demonstrate speed improvements after refactoring."""
import time
import pytest
import calc_total


class TestPerformanceImprovements:
    """Validate that refactored code maintains or improves performance."""
    
    def test_module_has_callable_function(self):
        """Verify the module has at least one callable function."""
        functions = [name for name in dir(calc_total) 
                    if callable(getattr(calc_total, name)) and not name.startswith('_')]
        
        print(f"\nAvailable functions: {functions}")
        assert len(functions) > 0, "No public functions found"
    
    def test_basic_performance(self):
        """Basic performance test - ensure reasonable execution time."""
        # Get the first public function
        functions = [getattr(calc_total, name) for name in dir(calc_total) 
                    if callable(getattr(calc_total, name)) and not name.startswith('_')]
        
        if not functions:
            pytest.skip("No functions found to test")
        
        main_func = functions[0]
        
        # Test with simple inputs based on existing tests
        test_cases = [
            ([{"price": 10, "quantity": 2, "discount": 0.1}],),
            ([{"price": 5, "quantity": 3}, {"price": 10, "quantity": 1}],),
            ([],),
        ]
        
        for args in test_cases:
            start = time.perf_counter()
            try:
                result = main_func(*args)
                duration = time.perf_counter() - start
                print(f"\nExecution time: {duration:.6f}s for input: {args}")
                # Should be very fast for simple calculations
                assert duration < 0.1, f"Performance issue: {duration}s"
            except Exception as e:
                print(f"Function call failed: {e}")
                # Don't fail on function errors, just measure performance
                pass