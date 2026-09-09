# Optimization Algorithm Issues

## Routing (`routing.py`)

- **Brute-force TSP**: Uses `itertools.permutations` to try every possible route — O(n!) time complexity. Becomes unusable beyond ~10 destinations.
- **No heuristic fallback**: `find_optimal_route` delegates directly to `brute_force_tsp` with no alternative for larger inputs.
- **Called repeatedly**: The TSP solver is invoked once per candidate engineer per job during matching, compounding the factorial cost.

## Matching (`matching.py`)

- **Greedy nearest-first**: Each job is assigned to the closest skilled engineer with capacity. Engineers near many jobs get overloaded while distant engineers sit idle.
- **Order-dependent results**: Assignment quality depends on the input order of jobs. A different ordering can produce a different (better or worse) result.
- **No global optimization**: Jobs are assigned one-by-one with no consideration of the overall assignment. A globally better distribution of work is never explored.
- **Redundant TSP re-computation**: Every time a job is tentatively added to an engineer, the full route is re-solved from scratch rather than incrementally updated.

## Test Coverage Insights

### Routing tests (`test_routing.py` — 8 tests)

- Covers basic correctness: single/two/three destinations, empty input, route start/end invariant, all-destinations-visited, and optimal-route selection.
- All tests use small matrices (3–4 locations) where brute-force finishes instantly — **no test exposes the O(n!) blowup** on realistic input sizes.
- Missing: no tests for asymmetric matrices, duplicate locations, or large destination counts (10+).

### Routing checkpoint test (`test_routing_checkpoint_a.py` — 1 test)

- Explicitly targets the performance problem: 10 destinations with a 0.25 s time gate.
- The current brute-force implementation is expected to **fail** this test (10! = 3.6M permutations).

### Matching tests (`test_matching.py` — 8 tests)

- Good coverage of core rules: skill filtering, closest-engineer preference, capacity limits, travel-time inclusion, load spillover, and edge cases (empty engineers/jobs).
- **Does not test for workload balance** — no assertion that jobs are distributed evenly when multiple engineers are equally qualified.
- **Does not test order sensitivity** — no test shuffles job input order and checks for equivalent results.
- Scenarios are small (1–2 engineers, 1–2 jobs), so the greedy flaw never surfaces.

### Benchmark tests (`test_benchmarks.py` — 6 tests)

- Compare scheduler output against known optimal solutions on small instances (2–5 jobs).
- Benchmarks 4 and 5 are designed as **traps for the greedy matcher**: they fail when the greedy algorithm assigns a shared-skill job to the wrong engineer, leaving a later exclusive-skill job unassignable.
- These are the only tests that measure **solution quality** (assignment accuracy, travel-time ratio), not just constraint validity.

### Scalability tests (`test_scalability.py` — 5 tests)

- Progressive levels from 25 engineers / 250 jobs up to 350 engineers / 4000 jobs.
- Each level has a hard time limit (3 s–30 s) enforced with SIGALRM.
- Higher levels deliberately create 12–20 jobs per engineer, making brute-force infeasible.
- The current implementation is expected to **fail levels 2+** due to routing blowup.

### Integration tests (`test_scheduler_integration.py` — 7 tests)

- End-to-end tests through the Scheduler: assignment + routing + unassigned tracking.
- Validates route structure (start/end, all locations visited) and capacity constraints.
- Small inputs only — validates correctness, not performance or quality.

### Overall gaps

| Gap | Impact |
|---|---|
| No routing tests at scale (except checkpoint) | Brute-force slowness is untested in unit suite |
| No matching tests for workload fairness | Greedy imbalance goes undetected |
| No matching tests for input-order sensitivity | Order-dependent results are invisible |
| Benchmark traps 4 & 5 are the only quality checks | Greedy matching failures only caught there |
| Scalability tests will fail on unoptimized code | Useful as a gate, but not as a regression suite |
