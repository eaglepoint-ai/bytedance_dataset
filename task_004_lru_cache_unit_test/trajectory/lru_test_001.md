# Trajectory: Adding Comprehensive Tests for LRUCache (Chain-of-Thought)

**Step 1: Understand the problem**  
- LRU Cache: fixed capacity, set/get operations  
- Evict least recently used on overflow  
- get/set both update recency  
- Invalid capacity (<=0) → ValueError  
- get missing key → None  
- Must handle overwrites, long sequences, edge values  

**Step 2: Identify all use cases to cover**  
- Constructor: capacity 0, negative, 1 (minimal)  
- Basic: set then get, overwrite same key  
- Recency: get moves key to most recent, set updates existing  
- Missing key: get returns None, no side effects  
- Eviction: correct LRU removed when full  
- Stress: 50–100 mixed operations, order preserved  
- Value types: None, lists, dicts allowed  

**Step 3: Plan test structure**  
- Use plain pytest (no plugins)  
- One file: test_lru_cache.py  
- Group tests by category with comments  
- Parametrize for multiple inputs  
- Assert recency indirectly via eviction behavior  

**Step 4: Write tests section by section**  
- Start with constructor errors  
- Basic set/get  
- Recency update rules  
- Eviction patterns  
- Stress/long sequence  
- Ordering integrity  

**Step 5: Verify quality**  
- Run pytest → all pass  
- Coverage >95%  
- Manually break code → tests fail appropriately  
- Keep tests simple and readable  

**Step 6: Final result**  
- Patch adds only the tests/ folder  
- Before: 0 tests  
- After: 20+ robust tests, high coverage  
- Model must output similar comprehensive suite

This is how a senior engineer approaches writing strong tests.
