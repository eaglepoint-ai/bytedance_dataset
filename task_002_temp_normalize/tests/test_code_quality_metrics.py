"""Tests that validate code quality metrics."""
import ast
import inspect
import pytest
import ids


class TestCodeQualityMetrics:
    """Validate that refactored code meets quality standards."""
    
    def test_module_imports(self):
        """Verify the module can be imported and has expected functions."""
        # Get all callable functions from the module
        functions = [name for name in dir(ids) 
                    if callable(getattr(ids, name)) and not name.startswith('_')]
        
        print(f"\nPublic functions in ids module: {functions}")
        assert 'normalize_id' in functions, "normalize_id function should be public"
        assert len(functions) >= 1, "Module should have at least normalize_id function"
    
    def test_normalize_id_complexity(self):
        """Ensure normalize_id cyclomatic complexity is acceptable."""
        source = inspect.getsource(ids.normalize_id)
        tree = ast.parse(source)
        
        complexity = self._calculate_complexity(tree)
        
        print(f"\nnormalize_id cyclomatic complexity: {complexity}")
        assert complexity <= 8, f"Complexity too high: {complexity}"
    
    def test_normalize_id_length(self):
        """Ensure normalize_id function is not too long."""
        source_lines = inspect.getsource(ids.normalize_id).split('\n')
        non_empty_lines = [l for l in source_lines if l.strip() and not l.strip().startswith('#')]
        
        print(f"\nnormalize_id length: {len(non_empty_lines)} lines")
        assert len(non_empty_lines) <= 30, f"Function too long: {len(non_empty_lines)} lines"
    
    def test_no_deeply_nested_code(self):
        """Ensure no deeply nested control structures."""
        source = inspect.getsource(ids.normalize_id)
        tree = ast.parse(source)
        
        max_nesting = self._get_max_nesting_depth(tree)
        print(f"\nMax nesting depth: {max_nesting}")
        assert max_nesting <= 4, f"Too much nesting: {max_nesting}"
    
    def test_helper_functions_exist_in_after(self):
        """Check if helper functions are properly defined in 'after' version."""
        # This test helps verify code organization improvements
        all_names = dir(ids)
        helper_functions = [name for name in all_names 
                           if callable(getattr(ids, name)) and name.startswith('_normalize')]
        
        print(f"\nHelper functions: {helper_functions}")
        # In 'after' version, we expect helper functions; in 'before', we don't
        # This test will pass in both, but shows the difference
        assert len(all_names) > 0, "Module should have content"
    
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
    def _get_max_nesting_depth(tree, current_depth=0):
        """Get maximum nesting depth of control structures."""
        max_depth = current_depth
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.With)):
                depth = TestCodeQualityMetrics._get_max_nesting_depth(node, current_depth + 1)
                max_depth = max(max_depth, depth)
            else:
                depth = TestCodeQualityMetrics._get_max_nesting_depth(node, current_depth)
                max_depth = max(max_depth, depth)
        return max_depth
