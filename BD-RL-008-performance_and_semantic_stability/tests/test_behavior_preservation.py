"""Behavior preservation tests for format_ids function.

These tests ensure that the refactored code maintains exact behavioral 
compatibility with the original implementation for all edge cases.
"""
import pytest
from format_ids import format_ids


class TestBasicBehavior:
    """Test cases that verify core functionality."""
    
    def test_simple_ids(self):
        """Simple ID formatting."""
        result = format_ids(['abc123', 'def456'])
        assert result == ['ABC123', 'DEF456']
    
    def test_empty_list(self):
        """Empty input returns empty output."""
        result = format_ids([])
        assert result == []
    
    def test_single_id(self):
        """Single ID is formatted correctly."""
        result = format_ids(['test'])
        assert result == ['TEST']
    
    def test_uppercase_conversion(self):
        """All input is converted to uppercase."""
        result = format_ids(['lowercase', 'MixedCase', 'UPPERCASE'])
        assert result == ['LOWERCASE', 'MIXEDCASE', 'UPPERCASE']


class TestNoneHandling:
    """Test cases for None value handling."""
    
    def test_none_values_skipped(self):
        """None values are skipped in output."""
        result = format_ids([None, 'abc', None, 'def', None])
        assert result == ['ABC', 'DEF']
    
    def test_all_none_values(self):
        """All None values returns empty list."""
        result = format_ids([None, None, None])
        assert result == []
    
    def test_none_at_start(self):
        """None at start doesn't affect rest."""
        result = format_ids([None, 'first', 'second'])
        assert result == ['FIRST', 'SECOND']
    
    def test_none_at_end(self):
        """None at end doesn't affect rest."""
        result = format_ids(['first', 'second', None])
        assert result == ['FIRST', 'SECOND']


class TestWhitespaceHandling:
    """Test cases for whitespace handling."""
    
    def test_leading_whitespace(self):
        """Leading whitespace is stripped."""
        result = format_ids(['  abc', '\tabc', '\nabc'])
        assert result == ['ABC', 'ABC', 'ABC']
    
    def test_trailing_whitespace(self):
        """Trailing whitespace is stripped."""
        result = format_ids(['abc  ', 'abc\t', 'abc\n'])
        assert result == ['ABC', 'ABC', 'ABC']
    
    def test_surrounding_whitespace(self):
        """Whitespace on both ends is stripped."""
        result = format_ids(['  abc  ', '\tabc\t', '\nabc\n'])
        assert result == ['ABC', 'ABC', 'ABC']
    
    def test_internal_whitespace(self):
        """Internal whitespace becomes hyphen."""
        result = format_ids(['ab cd', 'ab  cd', 'ab\tcd'])
        assert result == ['AB-CD', 'AB-CD', 'AB-CD']
    
    def test_whitespace_only(self):
        """Whitespace-only string becomes empty string."""
        result = format_ids(['   ', '\t\t', '\n\n'])
        assert result == ['', '', '']


class TestSpecialCharacterHandling:
    """Test cases for special character handling."""
    
    def test_single_special_char(self):
        """Single special character becomes hyphen."""
        result = format_ids(['abc_def', 'abc-def', 'abc.def'])
        assert result == ['ABC-DEF', 'ABC-DEF', 'ABC-DEF']
    
    def test_multiple_consecutive_special_chars(self):
        """Multiple consecutive special chars collapse to single hyphen."""
        result = format_ids(['abc___def', 'abc---def', 'abc...def'])
        assert result == ['ABC-DEF', 'ABC-DEF', 'ABC-DEF']
    
    def test_mixed_special_chars(self):
        """Mixed special characters collapse to single hyphen."""
        result = format_ids(['abc_-_def', 'abc!@#def', 'abc...---def'])
        assert result == ['ABC-DEF', 'ABC-DEF', 'ABC-DEF']
    
    def test_leading_special_chars(self):
        """Leading special chars become leading hyphen."""
        result = format_ids(['___abc', '---abc', '!!!abc'])
        assert result == ['-ABC', '-ABC', '-ABC']
    
    def test_trailing_special_chars(self):
        """Trailing special chars become trailing hyphen."""
        result = format_ids(['abc___', 'abc---', 'abc!!!'])
        assert result == ['ABC-', 'ABC-', 'ABC-']
    
    def test_only_special_chars(self):
        """Only special characters becomes single hyphen."""
        result = format_ids(['___', '---', '!!!'])
        assert result == ['-', '-', '-']


class TestOrderAndDuplicates:
    """Test cases for order and duplicate preservation."""
    
    def test_order_preserved(self):
        """Order of IDs is preserved."""
        result = format_ids(['third', 'first', 'second'])
        assert result == ['THIRD', 'FIRST', 'SECOND']
    
    def test_duplicates_preserved(self):
        """Duplicate IDs are preserved."""
        result = format_ids(['abc', 'def', 'abc', 'def', 'abc'])
        assert result == ['ABC', 'DEF', 'ABC', 'DEF', 'ABC']
    
    def test_duplicates_after_formatting(self):
        """Different input strings that become same after formatting."""
        result = format_ids(['abc', ' abc ', 'ABC', 'a-b-c'])
        assert result == ['ABC', 'ABC', 'ABC', 'A-B-C']
    
    def test_order_with_none(self):
        """Order preserved even with None values."""
        result = format_ids(['c', None, 'a', None, 'b'])
        assert result == ['C', 'A', 'B']


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_strings(self):
        """Empty strings remain empty."""
        result = format_ids(['', 'abc', ''])
        assert result == ['', 'ABC', '']
    
    def test_single_character(self):
        """Single characters are handled correctly."""
        result = format_ids(['a', 'Z', '1'])
        assert result == ['A', 'Z', '1']
    
    def test_numbers_only(self):
        """Numbers are preserved."""
        result = format_ids(['123', '456789'])
        assert result == ['123', '456789']
    
    def test_alphanumeric_mix(self):
        """Alphanumeric characters are preserved."""
        result = format_ids(['abc123', '123abc', 'a1b2c3'])
        assert result == ['ABC123', '123ABC', 'A1B2C3']
    
    def test_unicode_characters(self):
        """Unicode/non-ASCII characters become hyphens."""
        result = format_ids(['café', 'naïve', 'Москва'])
        assert result == ['CAF-', 'NA-VE', '-']
    
    def test_very_long_id(self):
        """Very long IDs are handled correctly."""
        long_id = 'a' * 1000
        result = format_ids([long_id])
        assert result == ['A' * 1000]
    
    def test_many_ids(self):
        """Large number of IDs are handled correctly."""
        ids = [f'id{i}' for i in range(1000)]
        result = format_ids(ids)
        assert len(result) == 1000
        assert result[0] == 'ID0'
        assert result[999] == 'ID999'


class TestComplexScenarios:
    """Test complex real-world scenarios."""
    
    def test_mixed_bag(self):
        """Complex mix of all edge cases."""
        result = format_ids([
            None,
            '  abc  ',
            'ABC',
            None,
            'a_b_c',
            '123',
            '!!!',
            '',
            'test-case',
            None
        ])
        assert result == ['ABC', 'ABC', 'A-B-C', '123', '-', '', 'TEST-CASE']
    
    def test_realistic_ids(self):
        """Realistic ID strings."""
        result = format_ids([
            'user-123',
            'USER_456',
            'org.example.id',
            'temp@email.com',
            'file:///path/to/file'
        ])
        assert result == [
            'USER-123',
            'USER-456',
            'ORG-EXAMPLE-ID',
            'TEMP-EMAIL-COM',
            'FILE-PATH-TO-FILE'
        ]
    
    def test_database_keys(self):
        """Database-style keys."""
        result = format_ids([
            'db_user_001',
            'db_user_002',
            'db_admin_001',
            None,
            'db_guest_001'
        ])
        assert result == [
            'DB-USER-001',
            'DB-USER-002',
            'DB-ADMIN-001',
            'DB-GUEST-001'
        ]
