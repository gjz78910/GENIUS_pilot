# Development Log

## 2026-06-09 — Routing Performance Analysis & Optimization

### Context

Investigated why `src/optimization/routing.py` and `src/optimization/matching.py` were slow and produced suboptimal results.

### Analysis Findings

**routing.py:**
- Used brute-force TSP (O(n!) complexity) for all inputs
- Unusable beyond ~10 destinations (10! = 3.6M permutations, ~2.7s on this machine)

**matching.py:**
- Calls `find_optimal_route` repeatedly for every candidate engineer on every job — compounding the factorial cost
- Greedy, input-order-dependent assignment: first jobs grab the closest engineer, starving later jobs
- Candidate ranking uses direct distance only, ignoring route context
- No workload balancing across engineers

### Decision

Chose a **hybrid approach** for routing:
- Keep exact brute-force for small inputs (≤ 8 destinations) to preserve correctness for tests/benchmarks
- Switch to **nearest-neighbour + 2-opt improvement** heuristic for larger inputs

Rationale: This gives optimal solutions where they're cheap, graceful degradation for larger instances, no external dependencies, and minimal code complexity.

### Implementation — `src/optimization/routing.py`

1. Added `_nearest_neighbour_tsp()` — builds an initial tour by always visiting the nearest unvisited destination. O(n²).
2. Added `_route_distance()` — utility to calculate total tour distance.
3. Added `_two_opt_improve()` — iteratively reverses route subsections to reduce total distance until no improvement found. Typically converges in a few passes.
4. Added `nearest_neighbour_2opt_tsp()` — combines the above two phases.
5. Modified `find_optimal_route()` — dispatches to brute-force if `len(destinations) <= 8`, otherwise uses the heuristic.
6. Set `BRUTE_FORCE_THRESHOLD = 8` after testing showed 10 destinations still exceeded the 0.25s performance gate.

### Test Results

- All 9 routing tests pass (including the Checkpoint A performance gate at 0.04s total)
- No regressions in matching, scheduler, or integration tests
- 13 pre-existing failures in other modules (data_loader validation, report formatting, scalability in matching, benchmark assignment quality) are unrelated to this change

## 2026-06-09 — Matching Quality Improvement (Most-Constrained-First)

### Problem

Benchmarks 4 and 5 failed because the greedy algorithm assigned jobs in input order. Jobs with exclusive skill requirements (only one qualified engineer) got starved when shared-skill jobs consumed that engineer's capacity first.

### Implementation — `src/optimization/matching.py`

Added most-constrained-first job sorting before the assignment loop:
- Count the number of qualified engineers for each job
- Sort jobs ascending by that count (fewest options first)
- Process the sorted list through the existing greedy assignment logic

This ensures jobs that can only be done by one engineer are assigned before jobs with multiple candidates.

### Test Results

- All 6 benchmark tests pass (including benchmarks 4 and 5 which previously failed)
- All 9 matching tests pass
- All 9 routing tests pass
- All 11 scheduler/integration tests pass
- 29 total related tests pass, 0 regressions

## 2026-06-09 — Report Generation Fixes (`src/features/report.py`)

### Problem

4 of 10 report correctness tests were failing:
1. `test_jobs_ordered_by_time` — jobs were output in TSP route order instead of chronological (`job.time`) order
2. `test_travel_time_between_jobs` — `travel_time_minutes` was always 0.0
3. `test_total_time_is_duration_plus_travel` — `total_time_minutes` was always 0.0 instead of `duration + travel`
4. `test_summary_row` — no TOTAL summary row at the end of each CSV

### Implementation

Rewrote `_calculate_job_timings()` and the report writer:
- Sort jobs by `job.time` (chronological) instead of following TSP route order
- Calculate travel time sequentially: engineer home → first job → second job → …
- Set `total_time_minutes = job_duration_minutes + travel_time_minutes` per row
- Append a TOTAL summary row at the end of each CSV with aggregated duration, travel, and total

### Test Results

- All 10 report correctness tests pass
- No regressions in other test suites

### Current Overall Status

| Test Suite | Passed | Failed | Notes |
|---|---|---|---|
| test_routing (8) + checkpoint_a (1) | 9/9 | 0 | |
| test_matching | 9/9 | 0 | |
| test_benchmarks | 6/6 | 0 | Including benchmarks 4 & 5 |
| test_scheduler + integration | 11/11 | 0 | |
| test_report_correctness | 10/10 | 0 | |
| test_scalability | 3/5 | 2 | test_1_easy (3s timeout), test_5_extremely_hard (30s timeout) |

### Remaining Work

- `matching.py` still re-solves full TSP for each candidate (performance issue for scalability tests 1 and 5). Switching to insertion-cost feasibility would fix the timeouts.
- `data_loader.py` is missing validation (asymmetric matrix, invalid times, bad locations, working hours)
