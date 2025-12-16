import pytest
from ids import normalize_id

def test_old_behavior_unchanged_abc_underscore_123():
    assert normalize_id("ABC_123") == "ABC-123"

def test_old_behavior_unchanged_spaces_collapse():
    assert normalize_id(" Abc 123 ") == "ABC-123"

def test_temp_preserves_underscores():
    assert normalize_id("temp_user_1") == "TEMP_USER_1"

def test_temp_mixed_symbols_example():
    # Expected output is defined by the prompt's required example.
    assert normalize_id(" TEMP__a b!!c ") == "TEMP__A-B--C"

@pytest.mark.parametrize(
    "raw, expected",
    [
        (None, ""),
        ("", ""),
        ("   ", ""),
        ("!!!", "-"),
        ("___", "-"),
        ("---", "-"),
        ("!!!   ---", "-"),
    ],
)
def test_edge_cases(raw, expected):
    assert normalize_id(raw) == expected
