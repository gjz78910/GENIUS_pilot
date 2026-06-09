# Implementation Plan: Nearest Neighbor + 2-opt Routing

## Overview

Implement a hybrid routing strategy in `src/optimization/routing.py` that preserves the existing brute-force solver for small inputs (≤8 destinations) and adds a nearest-neighbor + 2-opt heuristic pipeline for larger inputs. All changes are confined to the routing module with no new dependencies.

## Tasks

- [x] 1. Add the `_calculate_route_distance` helper function
  - [x] 1.1 Implement `_calculate_route_distance` in `src/optimization/routing.py`
    - Add a private helper that sums `travel_matrix[route[i]][route[i+1]]` for all consecutive pairs
    - Return a float representing total route distance
    - Handle the edge case where route is `(start, start)` returning `0.0`
    - _Requirements: 5.1, 5.2, 5.3_

  - [x]* 1.2 Write unit tests for `_calculate_route_distance`
    - Test with known routes and verify exact distance sums
    - Test trivial route `(start, start)` returns `0.0`
    - Test with asymmetric travel matrix
    - _Requirements: 5.1, 5.2, 5.3_

- [x] 2. Implement the `nearest_neighbor_tsp` function
  - [x] 2.1 Implement `nearest_neighbor_tsp` in `src/optimization/routing.py`
    - Construct a route by greedily selecting the closest unvisited destination at each step
    - Start from `start`, visit all destinations, return to `start`
    - Return `(route_tuple, total_distance)` matching the existing return format
    - Use `_calculate_route_distance` or accumulate distance during construction
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x]* 2.2 Write property test for nearest neighbor route completeness
    - **Property 1: Route Completeness**
    - Generate random travel matrices and destination sets
    - Verify every destination appears exactly once in `route[1:-1]`
    - **Validates: Requirements 2.1, 4.3**

  - [x]* 2.3 Write property test for nearest neighbor greedy selection
    - **Property 7: Nearest Neighbor Greedy Selection**
    - Verify each successive destination is the closest unvisited from the previous position at time of selection
    - **Validates: Requirement 2.2**

- [ ] 3. Implement the `two_opt_improve` function
  - [ ] 3.1 Implement `two_opt_improve` in `src/optimization/routing.py`
    - Accept a valid route tuple and travel matrix
    - Iteratively test all (i, j) segment reversals for improvement
    - Apply reversal when `new_dist < old_dist` and restart the scan
    - Terminate when a full pass finds no improvement
    - Return `(improved_route_tuple, improved_distance)`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [ ]* 3.2 Write property test for 2-opt non-degradation
    - **Property 4: 2-opt Non-degradation**
    - Generate random valid routes, apply `two_opt_improve`
    - Verify `improved_distance <= initial_distance`
    - **Validates: Requirement 3.1**

  - [ ]* 3.3 Write property test for 2-opt local optimality
    - **Property 5: 2-opt Local Optimality**
    - For the returned route, verify no single 2-opt swap produces a shorter route
    - **Validates: Requirement 3.2**

  - [ ]* 3.4 Write property test for 2-opt destination preservation
    - **Property 2: Route Circularity** and **Property 1: Route Completeness**
    - Verify `improved_route[0] == improved_route[-1] == start`
    - Verify the set of destinations is unchanged after improvement
    - **Validates: Requirements 3.3, 3.4**

- [ ] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Update `find_optimal_route` with hybrid dispatch logic
  - [ ] 5.1 Add `BRUTE_FORCE_THRESHOLD` constant and update `find_optimal_route`
    - Define `BRUTE_FORCE_THRESHOLD = 8` at module level
    - Keep the empty destinations early return `(start, start), 0.0`
    - Dispatch to `brute_force_tsp` when `len(destinations) <= BRUTE_FORCE_THRESHOLD`
    - Dispatch to `nearest_neighbor_tsp` then `two_opt_improve` when `len(destinations) > BRUTE_FORCE_THRESHOLD`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 7.1, 7.2, 7.3, 7.4_

  - [ ]* 5.2 Write property test for route validity across dispatch boundary
    - **Property 3: Distance Accuracy**
    - Test with inputs both below and above the threshold
    - Verify returned distance equals recomputed sum of edge weights
    - **Validates: Requirements 4.5, 5.1**

  - [ ]* 5.3 Write property test for optimality guarantee on small inputs
    - **Property 6: Optimality for Small Inputs**
    - For inputs with `len(destinations) <= 8`, verify returned distance equals brute-force optimal
    - **Validates: Requirements 1.2, 6.3**

- [ ] 6. Verify backward compatibility and performance
  - [ ] 6.1 Run existing test suites to confirm backward compatibility
    - Run `tests/test_routing.py` — all tests must pass unchanged
    - Run `tests/test_routing_checkpoint_a.py` — must pass the <0.25s performance gate for 10 destinations
    - Run `tests/test_matching.py` and `tests/test_scheduler_integration.py` to confirm integration
    - _Requirements: 6.1, 6.2, 7.4, 8.1, 8.2, 8.3_

- [ ] 7. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests use Python `unittest` with randomized inputs (no external PBT library, per project policy)
- The implementation is confined to `src/optimization/routing.py` with tests in `tests/`
- All existing tests must continue to pass without modification (backward compatibility)
