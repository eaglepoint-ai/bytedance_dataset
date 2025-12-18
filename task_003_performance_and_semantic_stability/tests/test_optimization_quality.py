"""
Optimization quality tests that fail in 'before' but pass in 'after'.

These tests specifically validate the performance optimizations made
during refactoring, ensuring the improvements are measurable.
"""
import re
import inspect
import pytest
from format_ids import format_ids
import format_ids as format_ids_module


class TestOptimizationQuality:
    """Tests that validate optimization improvements (FAIL_TO_PASS)."""
    
    def test_no_inline_regex_compilation(self):
        """Verify regex pattern is not compiled inline within the loop.
        
        FAIL_TO_PASS: Before version has re.sub() inside loop, after has pre-compiled pattern.
        """
        source = inspect.getsource(format_ids)
        
        # Check if re.sub or re.compile is called inside the function
        has_inline_re_sub = 're.sub(' in source and 'for ' in source
        has_inline_re_compile = 're.compile(' in source and 'for ' in source
        
        print(f"\nHas inline re.sub in loop: {has_inline_re_sub}")
        print(f"Has inline re.compile in loop: {has_inline_re_compile}")
        
        # After optimization, there should be NO inline regex compilation
        assert not has_inline_re_sub, "Regex should not be compiled inline (use pre-compiled pattern)"
        assert not has_inline_re_compile, "Regex pattern should be pre-compiled at module level"
    
    def test_has_module_level_compiled_pattern(self):
        """Verify a pre-compiled regex pattern exists at module level.
        
        FAIL_TO_PASS: Before has no module-level pattern, after has _NON_ALNUM_PATTERN.
        """
        # Check for compiled regex pattern at module level
        import re
        
        compiled_patterns = [
            name for name in dir(format_ids_module)
            if not name.startswith('__') and isinstance(getattr(format_ids_module, name), type(re.compile('')))
        ]
        
        print(f"\nCompiled patterns at module level: {compiled_patterns}")
        
        # Should have at least one pre-compiled pattern
        assert len(compiled_patterns) > 0, "Should have pre-compiled regex pattern at module level"
        
        # Check if the pattern is the expected one
        has_non_alnum_pattern = any('NON_ALNUM' in name.upper() or 'PATTERN' in name.upper() 
                                     for name in compiled_patterns)
        assert has_non_alnum_pattern, "Should have pattern for non-alphanumeric substitution"
    
    def test_documentation_mentions_optimization(self):
        """Verify function documentation mentions performance optimizations.
        
        FAIL_TO_PASS: Before has minimal docs, after has detailed optimization notes.
        """
        docstring = format_ids.__doc__ or ""
        
        print(f"\nDocstring length: {len(docstring)} chars")
        
        # Check for optimization-related keywords in documentation
        has_performance_docs = any(keyword in docstring.lower() for keyword in [
            'performance', 'optimization', 'optimiz', 'pre-compile', 'efficient'
        ])
        
        print(f"Has performance documentation: {has_performance_docs}")
        
        # After version should document the optimizations
        assert len(docstring) > 100, "Function should have comprehensive documentation"
        assert has_performance_docs, "Documentation should mention performance optimizations"
