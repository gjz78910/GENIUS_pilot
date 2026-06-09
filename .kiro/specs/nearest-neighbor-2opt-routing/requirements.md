# Requirements Document

## Introduction

This document specifies requirements for replacing the brute-force TSP routing algorithm in the field engineer scheduling system with a hybrid approach. The system uses brute-force for small inputs (≤8 destinations) to guarantee optimality, and switches to a nearest-neighbor construction heuristic followed by 2-opt local search for larger inputs. The implementation uses only Python standard library constructs and preserves full backward compatibility with the existing `find_optimal_route` public API.

## Glossary

- **Router**: The `find_optimal_route` function that serves as the public entry point for route calculation
- **Nearest_Neighbor_Solver**: The `nearest_neighbor_tsp` function that constructs an initial route by greedily selecting the closest unvisited destination
- **Two_Opt_Optimizer**: The `two_opt_improve` function that iteratively improves a route by reversing sub-segments
- **Distance_Calculator**: The `_calculate_route_distance` helper function that computes total travel distance for a route
- **Travel_Matrix**: A nested dictionary mapping location pairs to travel distances
- **Route**: A tuple of location strings starting and ending at the same location, visiting each destination exactly once
- **Brute_Force_Solver**: The existing `brute_force_tsp` function that evaluates all permutations to find the optimal route
- **BRUTE_FORCE_THRESHOLD**: The constant (value 8) that determines the dispatch boundary between exact and heuristic algorithms

## Requirements

### Requirement 1: Hybrid Algorithm Dispatch

**User Story:** As a system integrator, I want the routing function to automatically select the best algorithm based on input size, so that small inputs get optimal results while large inputs get fast results.

#### Acceptance Criteria

1. WHEN the number of destinations is zero, THE Router SHALL return a trivial route of `(start, start)` with distance `0.0`
2. WHEN the number of destinations is less than or equal to BRUTE_FORCE_THRESHOLD, THE Router SHALL delegate to the Brute_Force_Solver
3. WHEN the number of destinations exceeds BRUTE_FORCE_THRESHOLD, THE Router SHALL delegate to the Nearest_Neighbor_Solver followed by the Two_Opt_Optimizer
4. THE Router SHALL preserve the existing function signature accepting `start`, `destinations`, and `travel_matrix` parameters
5. THE Router SHALL return a tuple of `(route, distance)` where route is a tuple of strings and distance is a float

### Requirement 2: Nearest Neighbor Construction

**User Story:** As a scheduling system, I want an initial route constructed quickly using a greedy heuristic, so that the system can produce feasible routes for large destination sets without exhaustive search.

#### Acceptance Criteria

1. WHEN given a start location and a non-empty set of destinations, THE Nearest_Neighbor_Solver SHALL produce a route visiting every destination exactly once
2. THE Nearest_Neighbor_Solver SHALL construct the route by repeatedly selecting the closest unvisited destination from the current position
3. THE Nearest_Neighbor_Solver SHALL produce a route that starts and ends at the start location
4. THE Nearest_Neighbor_Solver SHALL return the total distance equal to the sum of consecutive edge weights in the produced route
5. WHEN constructing the route, THE Nearest_Neighbor_Solver SHALL complete in O(n²) time where n is the number of destinations

### Requirement 3: 2-opt Local Search Improvement

**User Story:** As a scheduling system, I want the initial heuristic route improved via local search, so that route quality approaches optimality without exhaustive computation.

#### Acceptance Criteria

1. WHEN given a valid route, THE Two_Opt_Optimizer SHALL return a route with distance less than or equal to the input route distance
2. THE Two_Opt_Optimizer SHALL terminate when no single 2-opt swap yields a shorter route
3. THE Two_Opt_Optimizer SHALL preserve the set of destinations visited by the input route
4. THE Two_Opt_Optimizer SHALL preserve the start and end location of the input route
5. WHEN a segment reversal reduces total distance, THE Two_Opt_Optimizer SHALL apply the reversal and restart the scan

### Requirement 4: Route Validity

**User Story:** As a field operations manager, I want every computed route to be valid, so that engineers visit all assigned jobs and return to their home location.

#### Acceptance Criteria

1. THE Router SHALL produce a route where the first element equals the start location
2. THE Router SHALL produce a route where the last element equals the start location
3. THE Router SHALL produce a route containing every destination exactly once in positions between first and last
4. THE Router SHALL produce a route with exactly `len(destinations) + 2` elements
5. THE Router SHALL report a distance equal to the sum of `travel_matrix[route[i]][route[i+1]]` for all consecutive pairs in the route

### Requirement 5: Distance Calculation

**User Story:** As a scheduling system, I want accurate distance calculation, so that route comparisons and optimizations are based on correct cost data.

#### Acceptance Criteria

1. THE Distance_Calculator SHALL compute the sum of travel distances for all consecutive location pairs in a route
2. THE Distance_Calculator SHALL return a non-negative value for any valid route
3. WHEN a route contains only start and return (no intermediate destinations), THE Distance_Calculator SHALL return `0.0`

### Requirement 6: Performance

**User Story:** As a system operator, I want the routing algorithm to complete quickly for realistic workloads, so that scheduling does not become a bottleneck.

#### Acceptance Criteria

1. WHEN given 10 destinations, THE Router SHALL produce a valid route in less than 0.25 seconds
2. WHEN given up to 20 destinations, THE Router SHALL produce a valid route in less than 1 second
3. WHILE the number of destinations is less than or equal to 8, THE Router SHALL guarantee an optimal route (minimum possible distance)

### Requirement 7: Backward Compatibility

**User Story:** As a developer maintaining the scheduling system, I want the routing API to remain unchanged, so that all existing callers and tests continue to work without modification.

#### Acceptance Criteria

1. THE Router SHALL maintain the same function name `find_optimal_route`
2. THE Router SHALL accept the same parameter types: `start: str`, `destinations: Sequence[str]`, `travel_matrix: Dict[str, Dict[str, float]]`
3. THE Router SHALL return the same type: `Tuple[Tuple[str, ...], float]`
4. WHEN called with inputs that previously produced a result, THE Router SHALL produce a result satisfying the same correctness invariants (completeness, circularity, accurate distance)

### Requirement 8: Error Handling

**User Story:** As a developer, I want predictable error behavior, so that I can handle exceptional cases appropriately.

#### Acceptance Criteria

1. WHEN destinations is an empty sequence, THE Router SHALL return `(start, start)` with distance `0.0` without raising an exception
2. IF a location key is missing from the Travel_Matrix, THEN THE Router SHALL allow the KeyError to propagate to the caller
3. WHEN given a single destination, THE Router SHALL return a valid round-trip route through that destination

### Requirement 9: Implementation Constraints

**User Story:** As a project maintainer, I want the implementation to use only standard library constructs, so that no new external dependencies are introduced.

#### Acceptance Criteria

1. THE Router SHALL use only Python standard library modules
2. THE Nearest_Neighbor_Solver SHALL use only Python standard library modules
3. THE Two_Opt_Optimizer SHALL use only Python standard library modules
