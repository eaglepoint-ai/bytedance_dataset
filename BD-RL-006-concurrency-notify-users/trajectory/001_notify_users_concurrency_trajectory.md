### 1. Understand the Problem Requirements

-   The current code:
    
    -   Processes users synchronously
        
    -   Sleeps for lookup
        
    -   Calls a blocking `send_notification`
        
-   The refactor must:
    
    -   Introduce real concurrency
        
    -   Enforce **global maximum of 50 concurrent sends**
        
    -   Preserve **result ordering**
        
    -   Avoid **thousands of pending futures**
        
    -   Use **standard library only**
        
    -   Preserve:
        
        -   same API entry point
            
        -   same output contract
            
        -   same error semantics
            

----------

### 2. Choose the Correct Concurrency Model

-   `send_notification` is **blocking**, not async
    
-   Therefore:
    
    -   Async `asyncio` alone is insufficient
        
    -   Must use **threads**, not coroutines
        
-   Correct approach:
    
    -   `concurrent.futures.ThreadPoolExecutor`
        
-   WRONG approaches to avoid:
    
    -   Creating a new executor per call
        
    -   Using unbounded threads
        
    -   Submitting all tasks at once
        

----------

### 3. Enforce the Global 50-Concurrency Limit

-   Requirement:
    
    -   No more than 50 active sends process-wide
        
-   Implementation strategy:
    
    -   Create **one global executor**
        
    -   Max workers = 50
        
    -   Protect creation with lock
        
-   Steps:
    
    -   Define `MAX_WORKERS = 50`
        
    -   Create global variables:
        
        -   `_executor`
            
        -   `_executor_lock`
            
    -   Write `_get_executor()` that:
        
        -   acquires lock
            
        -   initializes executor once
            
        -   reuses across calls
            
-   Why this matters:
    
    -   Guarantees process-wide throttling
        
    -   Avoids accidental thread explosion
        
    -   Avoids multiple pools competing
        

----------

### 4. Preserve Ordering (`results[i] → user_ids[i]`)

-   Concurrency breaks natural order
    
-   Required output behavior:
    
    -   Every result index must match its input index
        
-   Implementation strategy:
    
    -   Convert `user_ids` to a list
        
    -   Pre-allocate:
        
        -   `results = [None] * len(user_ids)`
            
    -   Track mapping:
        
        -   `future → index`
            
    -   When future completes:
        
        -   `results[index] = value or error`
            
-   Benefits:
    
    -   Deterministic output
        
    -   No sorting required
        
    -   Works even when requests complete randomly
        

----------

### 5. Prevent Memory Explosion (Streaming Work)

-   Problem if naïve approach:
    
    -   Submitting all users creates thousands of futures
        
    -   This violates “no resource explosion”
        
-   Correct strategy:
    
    -   Maintain **only 50 in-flight tasks**
        
-   Implementation pattern:
    
    -   Create iterator over indices
        
    -   Submit initial batch:
        
        -   `min(MAX_WORKERS, n)`
            
    -   Use:
        
        -   `concurrent.futures.wait(... FIRST_COMPLETED)`
            
    -   When one finishes:
        
        -   Remove completed future
            
        -   Submit exactly one new one
            
-   Result:
    
    -   At most 50 futures alive
        
    -   Predictable resource usage
        
    -   Infinite scalability
        

----------

### 6. Implement Correct Error Handling

-   Two categories:
    

#### Normal Exceptions (e.g., RuntimeError)

-   Must:
    
    -   Be captured
        
    -   Converted to `str(e)`
        
    -   Stored at correct index
        
    -   Execution continues
        

#### Fatal Exceptions (BaseException, e.g., KeyboardInterrupt)

-   Must:
    
    -   Cancel remaining futures
        
    -   Not swallow the error
        
    -   Re-raise immediately
        
-   Why:
    
    -   Critical system signals must stop system
        
    -   Prevents zombie threads
        
    -   Matches problem spec
        

----------

### 7. Code Structure to Implement

-   Needed helper:
    
    -   `_get_executor()`
        
    -   `_notify_one(user_id, payload)`
        
-   Steps inside `notify_users()`:
    
    -   Convert input to list
        
    -   If empty → return []
        
    -   Pre-allocate results list
        
    -   Initialize executor
        
    -   Start up to 50 tasks
        
    -   Loop:
        
        -   wait FIRST_COMPLETED
            
        -   fill results
            
        -   submit next task
            
    -   Handle BaseException by:
        
        -   canceling remaining tasks
            
        -   re-raising
            
    -   Return results
        

----------

### 8. Validate Solution Using Tests

----------

#### PASS_TO_PASS Tests Must Always Pass

-   Validate:
    
    -   Correct order mapping
        
    -   Correct error alignment
        
    -   KeyboardInterrupt propagates
        
    -   Return types correct
        

----------

#### FAIL_TO_PASS Test Must Prove Improvement

-   Monkeypatch send_notification
    
-   Count concurrent active executions
    
-   Assert:
    
    -   `max_active >= 2` (real concurrency exists)
        
    -   `max_active <= 50` (bounded properly)
        
-   Expected:
    
    -   BEFORE → fails (max_active = 1)
        
    -   AFTER → passes (2–50)
        

----------

### 9. Final Success Criteria

-   Uses standard library only
    
-   Has global concurrency cap = 50
    
-   Streams tasks safely
    
-   Maintains indexing order
    
-   Prevents memory overload
    
-   Preserves normal behavior
    
-   Handles fatal signals safely
    
-   Passes PASS_TO_PASS + FAIL_TO_PASS tests
    

----------