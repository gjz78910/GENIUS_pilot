# Technical Changes

## Routing (`routing.py`)

Replaced the single-strategy brute-force TSP with a hybrid dispatcher in `find_optimal_route`:

- **<=4 destinations**: existing `brute_force_tsp` (O(n!), optimal, fast at this scale).
- **>4 destinations**: `_nearest_neighbor_tsp` (O(n^2)) greedily visits the closest unvisited location. Optionally refined by `_two_opt_improve`, which iteratively reverses route segments that reduce total distance.

The `optimize` keyword parameter controls whether 2-opt runs. The scheduler passes `optimize=True` for final routes; matching uses the default (`False`) for fast capacity estimation.

**2-opt and asymmetric matrices.** The travel matrix is not symmetric (A-to-B cost differs from B-to-A). Standard 2-opt checks only the two boundary edges of a reversal, which assumes symmetry. With asymmetric costs, intermediate edges change direction and cost after reversal, so the boundary-only check can accept swaps that increase total distance, creating an infinite loop. The fix computes the full segment cost for both the old and reversed configurations before accepting a swap.

## Matching (`matching.py`)

Two changes to `assign_jobs`:

1. **Skill-exclusivity sort.** Before the assignment loop, jobs are sorted by how many engineers are qualified (ascending). Jobs with fewer candidates are processed first. This prevents the greedy algorithm from consuming capacity needed for exclusive-skill jobs. A stable tiebreaker (original index) preserves input order among equally-constrained jobs.

2. **Load-aware distance tiebreaker.** The candidate sort key changed from `distance` to `(distance, current_load)`. When engineers are equidistant, the one with fewer assigned jobs is preferred. This distributes work among interchangeable engineers instead of piling it onto the first one.

## Scheduler (`scheduler.py`)

One-line change: final route computation passes `optimize=True` to enable 2-opt refinement on completed routes.

## Public API

No signature changes to `assign_jobs`. `find_optimal_route` gained one keyword-only parameter (`optimize`, default `False`). All existing callers are unaffected.
