# Approach

## Workflow

1. **Explore.** Two agents read the codebase cold: one mapped the optimization code (routing, matching, scheduler, models), the other catalogued every test file with its assertions and time constraints.

2. **Plan.** A Plan agent designed the algorithm choices (NN + 2-opt for routing, exclusivity sort for matching) and traced them against each benchmark trap to verify correctness on paper. The initial plan assumed a brute-force threshold of 8 and symmetric 2-opt; both were revised during implementation.

3. **Use-case tests first.** A separate agent, given only the problem description and test gaps, proposed three tests covering routing quality at 12 destinations, matching order-independence, and workload balance. These were written before the fix, establishing pass/fail criteria independent of implementation details.

4. **Implement.** Routing and matching changes applied to two files. Scheduler received a one-line change.

5. **Verify incrementally.** Tests ran in dependency order: routing correctness, checkpoint performance, matching correctness, benchmarks, integration, scalability. Failures were diagnosed and fixed before advancing.

6. **Critical review.** A fresh agent reviewed the final code cold, looking only for severe issues. One finding (duplicate destinations dropped by `set()` in nearest-neighbor) was accepted and fixed. The rest of the code was confirmed correct.

7. **Final verification.** Full 80-test suite: all optimization-related tests pass, 9 pre-existing failures in unrelated modules unchanged.

## Testing and Verification

- **Baseline snapshot.** The full suite ran before any changes to record which tests failed and why. This made it possible to distinguish regressions from pre-existing issues.
- **Use-case tests written before implementation.** They describe desired behavior (fast routes, order-independent matching, balanced workload), not implementation mechanics.
- **Incremental test runs.** After each change, the narrowest relevant test group ran first. Scalability tests (up to 50s total) ran last to avoid wasting time on slow feedback when a correctness bug existed.
- **Independent code review.** A separate agent read the code without implementation context and reported only severe findings. This caught the duplicate-destination bug that no existing test exercised.

## Pitfalls

- **Stale bytecode cache.** Python caches compiled modules in `__pycache__/`. After editing source files, interactive scripts that had already imported the module continued using the old version. This caused confusing timing results where direct calls appeared fast but the full scheduler was slow. Fix: clear `__pycache__` or run tests as fresh `python -m unittest` processes.

- **Asymmetric travel matrices break standard 2-opt.** The boundary-edge-only check assumes `cost(A,B) == cost(B,A)`. With random per-direction costs, reversing a route segment changes intermediate edge costs unpredictably. The result was an infinite loop in 2-opt during final route computation. This only surfaced at scale (8+ destinations with random asymmetric costs) and was invisible on small symmetric test fixtures.

- **Brute-force threshold too high for aggregate cost.** The initial plan set the threshold at 8 (8! = 40,320 permutations, fast per call). But matching calls `find_optimal_route` hundreds of times during assignment. The cumulative cost of many 6!-8! calls exceeded time limits. Lowering the threshold to 4 moved those calls to the O(n^2) nearest-neighbor path.

- **2-opt cost in the matching hot path.** Even with NN + 2-opt being fast per call, running 2-opt inside the matching loop (called thousands of times) was too slow. The fix was to split the quality concern: NN-only during matching for fast estimation, NN + 2-opt only for the scheduler's final routes via the `optimize` parameter.

- **Greedy traps require processing order, not algorithm change.** Benchmarks 4 and 5 fail not because the greedy assignment logic is wrong, but because it processes jobs in the wrong order. Sorting by skill exclusivity (fewest candidates first) was sufficient; no backtracking or global optimization was needed.
