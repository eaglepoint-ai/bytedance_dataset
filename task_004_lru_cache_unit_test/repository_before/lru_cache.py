class _Node:
    """Doubly-linked list node for LRU tracking."""

    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None


class LRUCache:
    """
    LRU cache without using OrderedDict or other helper libraries.
    Uses a hash map for O(1) lookup and a doubly-linked list to track recency.
    Most recent is at the tail; least recent just after the head sentinel.
    """

    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self.map = {}
        self.head = _Node(None, None)  # LRU sentinel
        self.tail = _Node(None, None)  # MRU sentinel
        self.head.next = self.tail
        self.tail.prev = self.head

    # --- internal helpers ---
    def _add_to_tail(self, node: _Node):
        """Insert node right before tail (mark as most recent)."""
        node.prev = self.tail.prev
        node.next = self.tail
        self.tail.prev.next = node
        self.tail.prev = node

    def _remove(self, node: _Node):
        """Detach node from the list."""
        node.prev.next = node.next
        node.next.prev = node.prev
        node.prev = node.next = None

    def _move_to_tail(self, node: _Node):
        """Move existing node to most-recent position."""
        self._remove(node)
        self._add_to_tail(node)

    def _pop_lru(self):
        """Remove and return the least-recently-used node."""
        lru = self.head.next
        if lru is self.tail:
            return None
        self._remove(lru)
        return lru

    # --- public API ---
    def get(self, key):
        node = self.map.get(key)
        if not node:
            return None
        self._move_to_tail(node)
        return node.value

    def set(self, key, value):
        node = self.map.get(key)
        if node:
            node.value = value
            self._move_to_tail(node)
            return

        new_node = _Node(key, value)
        self.map[key] = new_node
        self._add_to_tail(new_node)

        if len(self.map) > self.capacity:
            evicted = self._pop_lru()
            if evicted:
                self.map.pop(evicted.key, None)