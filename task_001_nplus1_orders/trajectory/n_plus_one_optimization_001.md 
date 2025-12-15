### Trajectory (Thinking Process for N+1 Optimization Task)
1. Analyze the “before” implementation

1.1 Reviewed repository_before/service.py to understand control flow.
1.2 Identified N+1 query pattern: one query to load active users, then one query per user via lazy-loaded u.orders.
1.3 Confirmed scalability issue: total queries scale linearly with number of active users.

2. Define and lock the functional contract

2.1 Output must be {user_id: [Order, ...]} for active users only.
2.2 Active users with zero orders must still appear with empty lists.
2.3 Ordering per user must be deterministic: created_at DESC, then id DESC.
2.4 Edge case defined: n <= 0 returns empty lists for all active users.

3. Prove the N+1 problem using tests

3.1 Wrote deterministic seed data with fixed timestamps and IDs.
3.2 Added a tie case on created_at to force explicit tie-breaking.
3.3 Implemented a query-count guard using SQLAlchemy before_cursor_execute.
3.4 Verified that tests fail on repository_before due to excessive SQL queries.

4. Design the optimization strategy

4.1 Chose a database-level solution instead of Python-side slicing.
4.2 Used ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC, id DESC) to rank orders per user.
4.3 Ensured the approach is SQLite-compatible and deterministic.

5. Implement the optimized solution (“after”)

5.1 First query retrieves all active user IDs (ensures users with zero orders appear).
5.2 Second query computes row numbers in a subquery and filters to row_number <= n.
5.3 Used aliased(Order, subquery) to safely map subquery rows back to ORM objects.
5.4 Added explicit ORDER BY user_id, created_at DESC, id DESC to guarantee list ordering.

6. Validate correctness and determinism

6.1 Ran tests against repository_after and verified all correctness assertions.
6.2 Confirmed deterministic tie-breaking behavior across repeated runs.
6.3 Verified edge case behavior for n = 0 and n < 0.

7. Enforce performance regression protection

7.1 Re-ran tests against repository_before and confirmed regression test failure.
7.2 Verified that optimized version executes ≤ 3 SQL statements.
7.3 Ensured no lazy relationship access remains in the optimized code path.