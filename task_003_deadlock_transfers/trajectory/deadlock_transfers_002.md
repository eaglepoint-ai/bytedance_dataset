### Trajectory (Thinking Process for Deadlock Transfers Task)

1. Analyze the “before” implementation

1.1 Reviewed `repository_before/app/transfer.py` to understand the transfer control flow.  
1.2 Noted that the function touches **two rows** (`from_id` and `to_id`) and performs a read + two updates.  
1.3 Identified concurrency risk: each transfer can acquire row locks in caller-dependent order, enabling circular waits.

2. Define and lock the functional contract

2.1 A transfer must be **atomic**: debit and credit happen together, or not at all.  
2.2 It must raise `InsufficientFunds` if the source account balance would go negative.  
2.3 It must be safe under **concurrent** transfers involving overlapping accounts.  
2.4 No sleeps or time-based assumptions are allowed; concurrency must be handled via database semantics.

3. Reproduce and characterize the failure

3.1 Used a deterministic thread start (Barrier) to launch conflicting transfers simultaneously.  
3.2 Observed that concurrent opposite-direction transfers can trigger Postgres deadlock detection / lock timeouts.  
3.3 Confirmed the root cause is **conflicting lock acquisition order** across transactions, not business logic.

4. Design the fix strategy

4.1 Choose a database-level concurrency solution (row locking) rather than retries or higher isolation levels.  
4.2 Enforce a **global lock ordering rule**: always lock the lower account id before the higher id.  
4.3 Acquire locks **before** reading balances to avoid read-before-lock race conditions.

5. Implement the optimized “after” solution

5.1 Wrapped the transfer in `with conn.transaction():` so atomicity does not depend on the caller.  
5.2 Locked both account rows using `SELECT ... FOR UPDATE` in sorted id order.  
5.3 After locks are held, re-read the source balance and validate `InsufficientFunds`.  
5.4 Performed the debit + credit updates within the same transaction.

6. Validate correctness and determinism

6.1 Added deterministic tests for multi-thread concurrency (Barrier + no sleeps).  
6.2 Added single-thread “final balance” test to lock the intended arithmetic result.  
6.3 Added an `InsufficientFunds` rollback test to ensure no partial updates occur.

7. Enforce regression protection

7.1 Verified `repository_before` fails the concurrency test frequently under repeated trials.  
7.2 Verified `repository_after` passes consistently because it prevents circular wait via lock ordering.  
7.3 Ensured the fix uses standard Postgres row locking and no new dependencies.
