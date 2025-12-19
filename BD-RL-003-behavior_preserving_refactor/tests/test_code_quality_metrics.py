"""Tests that validate code quality metrics."""
import ast
import inspect
import pytest
import sys
import os

# Import the actual module
import calc_total


class TestCodeQualityMetrics:
    """Validate that refactored code meets quality standards."""
    
    def test_module_imports(self):
        """Verify the module can be imported and has expected functions."""
        # Get all callable functions from the module
        functions = [name for name in dir(calc_total) 
                    if callable(getattr(calc_total, name)) and not name.startswith('_')]
        
        print(f"\nAvailable functions in calc_total: {functions}")
        assert len(functions) > 0, "No public functions found in calc_total module"
    
    def test_function_complexity(self):
        """Ensure cyclomatic complexity is acceptable."""
        # Get the main function (assume it's the first public function)
        functions = [getattr(calc_total, name) for name in dir(calc_total) 
                    if callable(getattr(calc_total, name)) and not name.startswith('_')]
        
        if not functions:
            pytest.skip("No functions found to test")
        
        main_func = functions[0]
        source = inspect.getsource(main_func)
        tree = ast.parse(source)
        
        # Count decision points (if, for, while, and, or, except)
        complexity = self._calculate_complexity(tree)
        
        print(f"\nCyclomatic complexity: {complexity}")
        assert complexity <= 15, f"Complexity too high: {complexity}"
    
    def test_function_length(self):
        """Ensure function is not too long."""
        functions = [getattr(calc_total, name) for name in dir(calc_total) 
                    if callable(getattr(calc_total, name)) and not name.startswith('_')]
        
        if not functions:
            pytest.skip("No functions found to test")
            
        main_func = functions[0]
        source_lines = inspect.getsource(main_func).split('\n')
        non_empty_lines = [l for l in source_lines if l.strip() and not l.strip().startswith('#')]
        
        print(f"\nFunction length: {len(non_empty_lines)} lines")
        assert len(non_empty_lines) <= 100, f"Function too long: {len(non_empty_lines)} lines"
    
    def test_no_deeply_nested_try_except(self):
        """Ensure no deeply nested exception handling."""
        functions = [getattr(calc_total, name) for name in dir(calc_total) 
                    if callable(getattr(calc_total, name)) and not name.startswith('_')]
        
        if not functions:
            pytest.skip("No functions found to test")
            
        main_func = functions[0]
        source = inspect.getsource(main_func)
        tree = ast.parse(source)
        
        max_nesting = self._get_max_try_nesting(tree)
        print(f"\nMax try-except nesting: {max_nesting}")
        assert max_nesting <= 3, f"Too much nesting: {max_nesting}"
    
    @staticmethod
    def _calculate_complexity(tree):
        """Calculate cyclomatic complexity."""
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        return complexity
    
    @staticmethod
    def _get_max_try_nesting(tree, current_depth=0):
        """Get maximum try-except nesting depth."""
        max_depth = current_depth
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Try):
                depth = TestCodeQualityMetrics._get_max_try_nesting(node, current_depth + 1)
                max_depth = max(max_depth, depth)
            else:
                depth = TestCodeQualityMetrics._get_max_try_nesting(node, current_depth)
                max_depth = max(max_depth, depth)
        return max_depth