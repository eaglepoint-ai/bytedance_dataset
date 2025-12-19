import pytest

# These are META-TESTS.
# They verify that the existing LRUCache test suite is strong enough
# by running it against intentionally broken implementations.
#
# If the test suite is correct, it MUST FAIL on broken LRU behavior.
#
# This uses pytester (built-in pytest plugin) to run pytest inside pytest.


# -------------------------------------------------
# Helper: write a broken LRU implementation
# -------------------------------------------------

BROKEN_NO_EVICTION = """
class LRUCache:
    def __init__(self, capacity):
        if capacity <= 0:
            raise ValueError()
        self.capacity = capacity
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        self.data[key] = value
"""

BROKEN_NO_RECENCY_UPDATE = """
class LRUCache:
    def __init__(self, capacity):
        if capacity <= 0:
            raise ValueError()
        self.capacity = capacity
        self.data = {}
        self.order = []

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        if key not in self.data and len(self.data) >= self.capacity:
            old = self.order.pop(0)
            del self.data[old]
        if key not in self.data:
            self.order.append(key)
        self.data[key] = value
"""

BROKEN_WRONG_EVICTION = """
class LRUCache:
    def __init__(self, capacity):
        if capacity <= 0:
            raise ValueError()
        self.capacity = capacity
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        if key not in self.data and len(self.data) >= self.capacity:
            # Evicts MOST recent instead of least
            self.data.pop(next(reversed(self.data)))
        self.data[key] = value
"""


# -------------------------------------------------
# Helper: load the REAL test suite
# -------------------------------------------------

@pytest.fixture
def lru_test_suite():
    return """
import pytest
from lru_cache import LRUCache

def test_capacity_zero_raises_value_error():
    with pytest.raises(ValueError):
        LRUCache(0)

def test_capacity_negative_raises_value_error():
    with pytest.raises(ValueError):
        LRUCache(-1)

def test_basic_set_get():
    c = LRUCache(2)
    c.set("a", 1)
    assert c.get("a") == 1

def test_eviction_lru():
    c = LRUCache(2)
    c.set("a", 1)
    c.set("b", 2)
    c.get("a")
    c.set("c", 3)
    assert c.get("b") is None

def test_eviction_respects_recent_access():
    c = LRUCache(2)
    c.set("a", 1)
    c.set("b", 2)
    c.get("b")  # b should become most recent
    c.set("c", 3)
    assert c.get("a") is None
    assert c.get("b") == 2

def test_long_sequence():
    c = LRUCache(3)
    for i in range(50):
        c.set(str(i), i)
        c.get(str(i))
    assert c.get("49") == 49
"""


# -------------------------------------------------
# META TESTS
# -------------------------------------------------

def test_tests_fail_without_eviction(pytester, lru_test_suite):
    pytester.makepyfile(lru_cache=BROKEN_NO_EVICTION)
    pytester.makepyfile(test_lru=lru_test_suite)

    result = pytester.runpytest()
    result.assert_outcomes(passed=4, failed=2)


def test_tests_fail_without_recency_update(pytester, lru_test_suite):
    pytester.makepyfile(lru_cache=BROKEN_NO_RECENCY_UPDATE)
    pytester.makepyfile(test_lru=lru_test_suite)

    result = pytester.runpytest()
    result.assert_outcomes(passed=5, failed=1)


def test_tests_fail_with_wrong_eviction_policy(pytester, lru_test_suite):
    pytester.makepyfile(lru_cache=BROKEN_WRONG_EVICTION)
    pytester.makepyfile(test_lru=lru_test_suite)

    result = pytester.runpytest()
    result.assert_outcomes(passed=5, failed=1)


def test_tests_pass_with_correct_behavior(pytester, lru_test_suite):
    pytester.makepyfile(
        lru_cache="""
class LRUCache:
    def __init__(self, capacity):
        if capacity <= 0:
            raise ValueError()
        self.capacity = capacity
        self.data = {}
        self.order = []

    def get(self, key):
        if key not in self.data:
            return None
        self.order.remove(key)
        self.order.append(key)
        return self.data[key]

    def set(self, key, value):
        if key in self.data:
            self.order.remove(key)
        elif len(self.data) >= self.capacity:
            old = self.order.pop(0)
            del self.data[old]
        self.data[key] = value
        self.order.append(key)
"""
    )
    pytester.makepyfile(test_lru=lru_test_suite)

    result = pytester.runpytest()
    result.assert_outcomes(passed=6)

