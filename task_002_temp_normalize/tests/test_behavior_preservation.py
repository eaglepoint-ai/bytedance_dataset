"""Behavior preservation tests for normalize_id function.

These tests ensure that the refactored code maintains exact behavioral 
compatibility with the original implementation for all edge cases.
"""
import pytest
from ids import normalize_id


class TestOriginalBehavior:
    """Test cases that verify backward compatibility with original behavior."""
    
    def test_old_behavior_unchanged_abc_underscore_123(self):
        """Non-TEMP IDs: underscores should be converted to hyphens."""
        assert normalize_id("ABC_123") == "ABC-123"
    
    def test_old_behavior_unchanged_spaces_collapse(self):
        """Non-TEMP IDs: spaces collapse to single hyphen."""
        assert normalize_id(" Abc 123 ") == "ABC-123"
    
    def test_case_insensitive_conversion(self):
        """All input is uppercased."""
        assert normalize_id("lowercase") == "LOWERCASE"
        assert normalize_id("MixedCase") == "MIXEDCASE"
    
    def test_multiple_consecutive_non_alnum(self):
        """Multiple consecutive non-alphanumeric chars collapse to one hyphen."""
        assert normalize_id("abc!!!def") == "ABC-DEF"
        assert normalize_id("abc   def") == "ABC-DEF"
        assert normalize_id("abc---def") == "ABC-DEF"
    
    def test_leading_trailing_hyphens_preserved(self):
        """Leading/trailing hyphens from special chars are kept."""
        assert normalize_id("!!!abc") == "-ABC"
        assert normalize_id("abc!!!") == "ABC-"
        assert normalize_id("!!!abc!!!") == "-ABC-"


class TestTempBehavior:
    """Test cases for new TEMP-prefixed ID behavior."""
    
    def test_temp_preserves_underscores(self):
        """TEMP IDs: underscores are preserved."""
        assert normalize_id("temp_user_1") == "TEMP_USER_1"
    
    def test_temp_mixed_symbols_example(self):
        """TEMP IDs: underscores preserved, other non-alnum become hyphens."""
        assert normalize_id(" TEMP__a b!!c ") == "TEMP__A-B--C"
    
    def test_temp_lowercase_becomes_uppercase(self):
        """TEMP IDs: still uppercased."""
        assert normalize_id("temp_id") == "TEMP_ID"
    
    def test_temp_only_underscores(self):
        """TEMP IDs: all underscores preserved."""
        assert normalize_id("TEMP___") == "TEMP___"
    
    def test_temp_with_numbers(self):
        """TEMP IDs: numbers are preserved."""
        assert normalize_id("temp_123_456") == "TEMP_123_456"
    
    def test_temp_mixed_special_chars(self):
        """TEMP IDs: each non-alnum (except underscore) becomes one hyphen."""
        assert normalize_id("temp@user#123") == "TEMP-USER-123"
        assert normalize_id("temp_user@123") == "TEMP_USER-123"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.mark.parametrize(
        "raw, expected",
        [
            (None, ""),
            ("", ""),
            ("   ", ""),
            ("!!!", "-"),
            ("___", "-"),  # Non-TEMP: underscores become hyphen
            ("---", "-"),
            ("!!!   ---", "-"),
        ],
    )
    def test_edge_cases(self, raw, expected):
        """Various edge cases with empty/special-only inputs."""
        assert normalize_id(raw) == expected
    
    def test_none_input(self):
        """None input returns empty string."""
        assert normalize_id(None) == ""
    
    def test_whitespace_only(self):
        """Whitespace-only input returns empty string."""
        assert normalize_id("   ") == ""
        assert normalize_id("\t\n") == ""
    
    def test_alphanumeric_only(self):
        """Pure alphanumeric input unchanged (except uppercase)."""
        assert normalize_id("abc123") == "ABC123"
        assert normalize_id("ABC123") == "ABC123"


class TestTempPrefix:
    """Test the TEMP prefix detection logic."""
    
    def test_temp_prefix_case_insensitive(self):
        """TEMP prefix detection works after uppercasing."""
        assert normalize_id("temp_id") == "TEMP_ID"
        assert normalize_id("TEMP_id") == "TEMP_ID"
        assert normalize_id("Temp_id") == "TEMP_ID"
    
    def test_temp_substring_not_prefix(self):
        """TEMP in middle/end doesn't trigger special behavior."""
        assert normalize_id("my_temp_id") == "MY-TEMP-ID"
        assert normalize_id("id_temp") == "ID-TEMP"
    
    def test_temp_with_leading_spaces(self):
        """Leading spaces stripped before TEMP check."""
        assert normalize_id("  temp_id") == "TEMP_ID"
    
    def test_temp_with_leading_special_chars(self):
        """Leading special chars prevent TEMP detection."""
        result = normalize_id("!!!temp_id")
        # After strip, starts with "!!!", not "TEMP", so uses old behavior
        assert result == "-TEMP-ID"
