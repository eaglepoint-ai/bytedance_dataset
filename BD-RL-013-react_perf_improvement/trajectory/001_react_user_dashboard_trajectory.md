# Trajectory – React UserAnalyticsDashboard Optimization (Jest Dataset)

1. Start from the original React component where:
   - `visibleUsers` derives `label` and `lastSeenText` inside `.map()` and
     returns new objects.
   - `UserItem` takes `{ user, selectedUserId, onSelect }` and compares
     `user.id === selectedUserId`.
   - `React.memo(UserItem)` is not very effective because the `user` prop is a
     fresh object on each render.

2. Design an optimized version that:
   - Leaves overall behavior/props shape the same at the top level.
   - Changes `visibleUsers` to only filter + sort, returning the original
     `user` objects.
   - Moves `label` and `lastSeenText` computation into `UserItem`.
   - Changes `UserItem` props to `{ user, isSelected, onSelect, formatLastActive }`,
     using `isSelected` for background styling.

3. Encode expectations in Jest tests:
   - `tests/structure.test.js` is **env-aware** via `process.env.PYTHONPATH` and
     checks for the correct structure depending on whether the target path
     includes `repository_before` or `repository_after`.
   - `tests/equivalence.test.js` checks that both versions still share the
     checksum loop and export `UserAnalyticsDashboard` as the default export.

4. Expose everything through Docker:
   - Before-run:

     ```bash
     docker compose run --rm -e PYTHONPATH=/app/repository_before app npm test
     ```

   - After-run:

     ```bash
     docker compose run --rm -e PYTHONPATH=/app/repository_after app npm test
     ```

   The command shape matches the strict pattern you requested, but the tests
   are implemented in Jest/JavaScript.
