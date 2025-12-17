Trajectory: LRU Cache Implementation (Chain-of-Thought)

Step 1: Understand the Problem

Objective: Design and implement a Least Recently Used (LRU) cache with fixed capacity.
Key operations: get(key) and set(key, value) must both run in O(1) average time complexity.
When capacity is reached, evict the least recently used item.
get returns the value if key exists (and marks it as most recent), else -1 (or None in some variants).
set inserts or updates the value and marks the key as most recent.
Source: LeetCode - https://leetcode.com/problems/lru-cache/description/

Step 2: Choose Data Structures

Need O(1) lookup → hash map (dictionary).
Need O(1) ordering and eviction → doubly linked list to track usage order and move nodes quickly.
Combine them: hash map stores key → node reference; linked list maintains recency order.
Alternative: Use Python's OrderedDict for simplicity, but custom doubly linked list gives full control and better learning.
Source: GeeksforGeeks -https://www.npmjs.com/package/lru-cache https://www.geeksforgeeks.org/system-design/lru-cache-implementation

Step 3: Design the Logic

Use sentinel nodes (dummy head and tail) to avoid edge-case checks when list is empty.
On get(key):
Look up in hash map → if exists, move node to tail (most recent) → return value.
Else → return -1.

On set(key, value):
If key exists → update value, move node to tail.
If new and full → remove head.next (LRU), delete from hash map, add new node to tail.

All operations O(1) thanks to direct node access.
Source: YouTube - https://www.youtube.com/watch?v=H24WXxTbEXU
Step 4: Implementation Details

Create Node class with key, value, prev, next pointers.
Initialize cache with dummy head/tail connected.
Helper methods: _remove(node) and _add_to_tail(node) for O(1) reordering.
Handle capacity overflow by evicting from head.

Step 5: Verify and Edge Cases

Test with capacity 1, overwrites, missing keys, long sequences.
Ensure recency updates on both get and set.
Reference implementation patterns seen in production libraries.
Source: https://www.npmjs.com/package/lru-cache https://www.geeksforgeeks.org/system-design/lru-cache-implementation
Summary

Key insight: Hash map + doubly linked list = O(1) LRU operations.
Real-world application: Used in Redis, browsers, CDNs, and many production systems for efficient caching.
This approach is clean, efficient, and scalable.