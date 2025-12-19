"""Tests that validate code quality metrics."""
import ast
import inspect
import pytest
import format_ids


class TestCodeQualityMetrics:
    """Validate that refactored code meets quality standards."""
    
    def test_module_imports(self):
        """Verify the module can be imported and has expected functions."""
        functions = [name for name in dir(format_ids) 
                    if callable(getattr(format_ids, name)) and not name.startswith('_')]
        
        print(f"\nPublic functions in format_ids module: {functions}")
        assert 'format_ids' in functions, "format_ids function should be public"
    
    def test_format_ids_complexity(self):
        """Ensure format_ids cyclomatic complexity is acceptable."""
        source = inspect.getsource(format_ids.format_ids)
        tree = ast.parse(source)
        
        complexity = self._calculate_complexity(tree)
        
        print(f"\nformat_ids cyclomatic complexity: {complexity}")
        assert complexity <= 5, f"Complexity too high: {complexity}"
    
    def test_format_ids_length(self):
        """Ensure format_ids function is not too long."""
        source_lines = inspect.getsource(format_ids.format_ids).split('\n')
        non_empty_lines = [l for l in source_lines if l.strip() and not l.strip().startswith('#')]
        
        print(f"\nformat_ids length: {len(non_empty_lines)} lines")
        assert len(non_empty_lines) <= 30, f"Function too long: {len(non_empty_lines)} lines"
    
    def test_no_deeply_nested_code(self):
        """Ensure no deeply nested control structures."""
        source = inspect.getsource(format_ids.format_ids)
        tree = ast.parse(source)
        
        max_nesting = self._get_max_nesting_depth(tree)
        print(f"\nMax nesting depth: {max_nesting}")
        assert max_nesting <= 3, f"Too much nesting: {max_nesting}"
    
    def test_regex_precompilation(self):
        """Check if regex pattern is pre-compiled (performance optimization).
        
        FAIL_TO_PASS: This test fails in 'before' (no pre-compilation) 
        but passes in 'after' (pre-compiled pattern exists).
        """
        # In the 'after' version, we expect a module-level compiled pattern
        module_vars = dir(format_ids)
        
        # Look for compiled pattern or evidence of optimization
        has_compiled_pattern = any('PATTERN' in name.upper() or 
                                   '_NON_ALNUM' in name.upper() 
                                   for name in module_vars)
        
        print(f"\nModule-level variables: {[v for v in module_vars if not v.startswith('__')]}")
        print(f"Has pre-compiled pattern: {has_compiled_pattern}")
        
        # This assertion will FAIL in 'before' (no pattern) and PASS in 'after'
        assert has_compiled_pattern, "Regex pattern should be pre-compiled at module level for performance"
    
    def test_function_signature_unchanged(self):
        """Ensure function signature hasn't changed."""
        import inspect
        sig = inspect.signature(format_ids.format_ids)
        params = list(sig.parameters.keys())
        
        print(f"\nFunction signature: {sig}")
        assert params == ['ids'], f"Function signature changed: {params}"
        assert len(params) == 1, "Function should have exactly one parameter"
    
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
