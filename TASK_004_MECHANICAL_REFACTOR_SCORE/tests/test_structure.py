import os


BEFORE_PATH = "repository_before/app/score.py"
AFTER_PATH = "repository_after/app/score.py"


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def test_helper_function_exists():
    """
    Mechanical refactor requirement:
    At least one helper function must exist in repository_after.
    """
    import repository_after.app.score as mod

    helpers = [
        name for name in dir(mod)
        if name.startswith("_") and callable(getattr(mod, name))
    ]

    assert len(helpers) >= 1


def test_parsing_duplication_reduced():
    """
    Structural-only test:
    Ensure repeated parsing patterns were de-duplicated.
    """
    before = _read(BEFORE_PATH)
    after = _read(AFTER_PATH)

    float_before = before.count("float(")
    float_after = after.count("float(")

    int_before = before.count("int(")
    int_after = after.count("int(")

    assert float_after < float_before
    assert int_after <= int_before


def test_line_count_not_excessive():
    """
    Mechanical refactor guard:
    Refactor must not grow more than +5 lines.
    """
    before_lines = _read(BEFORE_PATH).splitlines()
    after_lines = _read(AFTER_PATH).splitlines()

    assert len(after_lines) <= len(before_lines) + 5
