"""Meta tests to validate coverage of repository_after/tests/test_sequence_generator.py.

Goals:
- The real suite should fail on buggy implementations (including the shipped reference).
- A fixed implementation should pass cleanly.
"""

from pathlib import Path

import pytest

pytest_plugins = ["pytester"]


ROOT = Path(__file__).resolve().parents[1]
TEST_FILE = ROOT / "repository_after" / "tests" / "test_sequence_generator.py"
IMPL_FILE = ROOT / "repository_after" / "gms_sequence_generator.py"


def _load_source(path: Path) -> str:
    with path.open("r", encoding="utf-8") as f:
        return f.read()


def _run_suite(pytester, impl_source: str, expect_failures: bool):
    # Arrange a fresh temp workspace that mirrors the expected layout
    repo_dir = pytester.path / "repository_after"
    repo_dir.mkdir()
    (repo_dir / "gms_sequence_generator.py").write_text(impl_source, encoding="utf-8")

    # Provide pytest configuration (register stress marker)
    pytester.path.joinpath("pytest.ini").write_text(
        """[pytest]
markers =
    stress: long-running workload tests
""",
        encoding="utf-8",
    )

    tests_dir = pytester.path / "repository_after" / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    test_src = _load_source(TEST_FILE).replace(
        "sys.path.append(str(AFTER_DIR))", "sys.path.insert(0, str(AFTER_DIR))"
    )
    tests_dir.joinpath("test_sequence_generator.py").write_text(test_src, encoding="utf-8")

    result = pytester.runpytest("-q", str(tests_dir / "test_sequence_generator.py"))
    outcomes = result.parseoutcomes()
    failed = outcomes.get("failed", 0)
    passed = outcomes.get("passed", 0)
    if expect_failures:
        assert failed >= 1, f"Expected failures but got outcomes={outcomes}"
    else:
        assert failed == 0, f"Expected all tests to pass but got outcomes={outcomes}"
        assert passed >= 1, "Suite should have passing tests"


def test_reference_impl_trips_known_failures(pytester):
    """Current reference implementation is intentionally buggy; suite should fail on it."""

    impl_source = _load_source(IMPL_FILE)
    _run_suite(pytester, impl_source, expect_failures=True)


def test_fixed_impl_passes(pytester):
    """A correct, thread-safe implementation should satisfy the suite."""

    impl_source = r'''
import threading


class SequenceGenerator:
    def __init__(self, db_connection):
        self.db = db_connection
        self.current_id = 0
        self.max_id_in_lease = 0
        self._lock = threading.Lock()

    def get_next_id(self):
        with self._lock:
            if self.current_id >= self.max_id_in_lease:
                    start = self.db.get_next_block_start(block_size=100)
                    if not isinstance(start, int):
                        raise TypeError("Lease start must be int")
                    # Clamp to preserve monotonicity and avoid negative IDs
                    start = max(start, self.current_id, 0)
                    self.current_id = start
                    self.max_id_in_lease = start + 100
            self.current_id += 1
            return self.current_id
'''
    _run_suite(pytester, impl_source, expect_failures=False)


def test_duplicate_ids_bug_fails(pytester):
    """A generator that never changes IDs should be rejected (uniqueness)."""

    impl_source = """
class SequenceGenerator:
    def __init__(self, db_connection):
        self.db = db_connection
    def get_next_id(self):
        return 1  # always duplicate
"""
    _run_suite(pytester, impl_source, expect_failures=True)


def test_missing_leases_bug_fails(pytester):
    """A generator that skips DB leasing should fail efficiency checks."""

    impl_source = """
class SequenceGenerator:
    def __init__(self, db_connection):
        self.db = db_connection
        self.current_id = 0
    def get_next_id(self):
        # never calls DB, so lease count stays zero
        self.current_id += 1
        return self.current_id
"""
    _run_suite(pytester, impl_source, expect_failures=True)


def test_bad_boundary_logic_fails(pytester):
    """Off-by-one in lease sizing should be caught at boundaries."""

    impl_source = """
class SequenceGenerator:
    def __init__(self, db_connection):
        self.db = db_connection
        self.current_id = 0
        self.max_id_in_lease = 0
    def get_next_id(self):
        if self.current_id >= self.max_id_in_lease:
            start = self.db.get_next_block_start(block_size=100)
            self.current_id = start
            self.max_id_in_lease = start + 99  # off-by-one (only 99 IDs)
        self.current_id += 1
        return self.current_id
"""
    _run_suite(pytester, impl_source, expect_failures=True)


def test_negative_ids_bug_fails(pytester):
    """Negative lease starts must be rejected by the suite."""

    impl_source = """
class SequenceGenerator:
    def __init__(self, db_connection):
        self.db = db_connection
        self.current_id = 0
        self.max_id_in_lease = 0
    def get_next_id(self):
        if self.current_id >= self.max_id_in_lease:
            start = -100  # bad DB behavior propagated
            self.current_id = start
            self.max_id_in_lease = start + 100
        self.current_id += 1
        return self.current_id
"""
    _run_suite(pytester, impl_source, expect_failures=True)


def test_wrong_block_size_bug_fails(pytester):
    """Using an incorrect lease block size should be caught."""

    impl_source = """
class SequenceGenerator:
    def __init__(self, db_connection):
        self.db = db_connection
        self.current_id = 0
        self.max_id_in_lease = 0
    def get_next_id(self):
        if self.current_id >= self.max_id_in_lease:
            # wrong block size triggers AssertionError in FakeDB
            start = self.db.get_next_block_start(block_size=50)
            self.current_id = start
            self.max_id_in_lease = start + 50
        self.current_id += 1
        return self.current_id
"""
    _run_suite(pytester, impl_source, expect_failures=True)


def test_string_ids_bug_fails(pytester):
    """Returning string IDs should fail type checks."""

    impl_source = """
class SequenceGenerator:
    def __init__(self, db_connection):
        self.db = db_connection
        self.current_id = 0
        self.max_id_in_lease = 0
    def get_next_id(self):
        if self.current_id >= self.max_id_in_lease:
            start = self.db.get_next_block_start(block_size=100)
            self.current_id = start
            self.max_id_in_lease = start + 100
        self.current_id += 1
        return str(self.current_id)
"""
    _run_suite(pytester, impl_source, expect_failures=True)


def test_double_increment_bug_fails(pytester):
    """Incrementing twice per call should be caught by monotonicity / range checks."""

    impl_source = """
class SequenceGenerator:
    def __init__(self, db_connection):
        self.db = db_connection
        self.current_id = 0
        self.max_id_in_lease = 0
    def get_next_id(self):
        if self.current_id >= self.max_id_in_lease:
            start = self.db.get_next_block_start(block_size=100)
            self.current_id = start
            self.max_id_in_lease = start + 100
        self.current_id += 2  # bug: skips values
        return self.current_id
"""
    _run_suite(pytester, impl_source, expect_failures=True)
