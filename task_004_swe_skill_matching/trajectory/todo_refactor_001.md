# Trajectory (Thinking Process for Refactoring)
1. I audited the original matcher. It loaded every employee with skills and availability into memory, scored everyone with nested loops, then sorted all matches. This guaranteed high fixed cost and poor scaling.

2. I set a performance contract using the same tests. Warm-run latency must stay under budget, scaling must not blow up when requirements grow, and allocation volume must stay low when many employees qualify.

3. I changed the flow to two phases. Phase 1 finds top candidates using minimal data. Phase 2 materializes full details only for the top results. This avoids building full entity graphs for 10,000 employees.

4. I cut hot-path work per employee. I precomputed required-skill counts for fast lookups and replaced brute-force availability checks with sorted-interval scanning. This reduces comparisons as requirements increase.

5. I removed the full sort. I kept only the top 20 while iterating, then sorted at most 20 items at the end. This lowers CPU and memory cost without changing the returned behavior.
