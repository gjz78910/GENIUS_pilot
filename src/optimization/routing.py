"""Routing functions for field engineer scheduling.

The main entry point is `find_optimal_route`, which returns a route that:
- starts at `start`
- visits each destination once
- returns to `start`

Algorithms available:
- brute_force_tsp: O(n!) exact solution, practical for ≤12 destinations
- held_karp_tsp: O(n²·2ⁿ) exact solution using dynamic programming, practical for ≤20 destinations
- nearest_neighbor_tsp: O(n²) greedy heuristic, fast for any size
- two_opt_improve: O(n²) local search improvement pass
- find_optimal_route: adaptive dispatcher that picks the best algorithm for the input size
- estimate_route_distance: fast O(n²) estimate for use during matching/capacity checks
"""

from __future__ import annotations

from itertools import permutations
from typing import Sequence, Tuple, Dict, List


def brute_force_tsp(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Solve a travelling‑salesperson problem using brute force.

    Parameters
    ----------
    start : str
        The starting (and ending) location for the route.
    destinations : Sequence[str]
        A sequence of destination locations that must be visited exactly once.
    travel_matrix : Dict[str, Dict[str, float]]
        A dictionary representing the travel distance between locations.

    Returns
    -------
    Tuple[Tuple[str, ...], float]
        A tuple containing the best route (including the start location at
        the beginning and end) and the total distance of that route.
    """
    # If there are no destinations, return a trivial route with zero cost
    if not destinations:
        return (start, start), 0.0

    best_distance: float = float("inf")
    best_route: Tuple[str, ...] | None = None

    # Iterate over all possible permutations of the destinations
    for perm in permutations(destinations):
        distance: float = 0.0
        current = start
        # travel from the start to the first destination
        for loc in perm:
            # accumulate distance from current location to next
            distance += travel_matrix[current][loc]
            current = loc
        # finally return to the start
        distance += travel_matrix[current][start]
        if distance < best_distance:
            best_distance = distance
            # Build the full route including the start and end
            best_route = (start,) + perm + (start,)

    assert best_route is not None  # for type checker
    return best_route, best_distance


def nearest_neighbor_tsp(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Solve TSP using the nearest-neighbor heuristic.

    Greedy algorithm that always visits the closest unvisited destination.
    O(n²) time, produces routes typically within 20-25% of optimal.

    Parameters
    ----------
    start : str
        The starting (and ending) location for the route.
    destinations : Sequence[str]
        A sequence of destination locations that must be visited exactly once.
    travel_matrix : Dict[str, Dict[str, float]]
        A dictionary representing the travel distance between locations.

    Returns
    -------
    Tuple[Tuple[str, ...], float]
        A tuple containing the route and its total distance.
    """
    if not destinations:
        return (start, start), 0.0

    unvisited = list(destinations)
    route: List[str] = [start]
    total_distance = 0.0
    current = start

    while unvisited:
        # Find the nearest unvisited destination
        best_next = min(unvisited, key=lambda loc: travel_matrix[current][loc])
        total_distance += travel_matrix[current][best_next]
        route.append(best_next)
        current = best_next
        unvisited.remove(best_next)

    # Return to start
    total_distance += travel_matrix[current][start]
    route.append(start)

    return tuple(route), total_distance


def two_opt_improve(
    route: Tuple[str, ...], distance: float, travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Improve a route using 2-opt local search.

    Repeatedly reverses segments of the route when doing so reduces
    total distance. Continues until no improvement is found.

    Parameters
    ----------
    route : Tuple[str, ...]
        An existing route (start, ..., start) to improve.
    distance : float
        The current total distance of the route.
    travel_matrix : Dict[str, Dict[str, float]]
        Travel distance matrix.

    Returns
    -------
    Tuple[Tuple[str, ...], float]
        The improved route and its distance.
    """
    # Work with a mutable list (excluding the final return-to-start)
    # route = (start, d1, d2, ..., dn, start)
    route_list = list(route[:-1])  # [start, d1, d2, ..., dn]
    n = len(route_list)

    if n <= 2:
        return route, distance

    improved = True
    best_distance = distance
    max_passes = n * 2  # Limit passes to prevent excessive runtime

    passes = 0
    while improved and passes < max_passes:
        improved = False
        passes += 1
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                # Cost of current edges: (i-1, i) and (j, j+1 or start)
                loc_before_i = route_list[i - 1]
                loc_i = route_list[i]
                loc_j = route_list[j]
                loc_after_j = route_list[j + 1] if j + 1 < n else route_list[0]

                # Current cost of the two edges being replaced
                current_cost = (
                    travel_matrix[loc_before_i][loc_i]
                    + travel_matrix[loc_j][loc_after_j]
                )
                # New cost if we reverse the segment [i..j]
                new_cost = (
                    travel_matrix[loc_before_i][loc_j]
                    + travel_matrix[loc_i][loc_after_j]
                )

                if new_cost < current_cost - 1e-10:
                    # Reverse the segment
                    route_list[i : j + 1] = route_list[i : j + 1][::-1]
                    best_distance -= (current_cost - new_cost)
                    improved = True

    # Rebuild the route tuple
    final_route = tuple(route_list) + (route_list[0],)
    return final_route, best_distance


def held_karp_tsp(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Solve a travelling‑salesperson problem using the Held-Karp algorithm.

    Uses dynamic programming with bitmasks to find the optimal tour in
    O(n² · 2ⁿ) time and O(n · 2ⁿ) space, where n is the number of
    destinations. This is significantly faster than brute force for
    n > 12 and practical for up to ~20 destinations.

    Parameters
    ----------
    start : str
        The starting (and ending) location for the route.
    destinations : Sequence[str]
        A sequence of destination locations that must be visited exactly once.
    travel_matrix : Dict[str, Dict[str, float]]
        A dictionary representing the travel distance between locations.

    Returns
    -------
    Tuple[Tuple[str, ...], float]
        A tuple containing the best route (including the start location at
        the beginning and end) and the total distance of that route.
    """
    if not destinations:
        return (start, start), 0.0

    n = len(destinations)

    # Handle single destination as a special case for clarity
    if n == 1:
        dest = destinations[0]
        dist = travel_matrix[start][dest] + travel_matrix[dest][start]
        return (start, dest, start), dist

    # Build a list of all nodes: index 0 = start, indices 1..n = destinations
    nodes: List[str] = [start] + list(destinations)

    # Pre-compute a distance array for fast index-based lookup
    dist: List[List[float]] = [
        [travel_matrix[nodes[i]][nodes[j]] for j in range(n + 1)]
        for i in range(n + 1)
    ]

    # dp[S][i] = minimum distance to reach destination node i (1-indexed)
    # having visited exactly the set of destination nodes represented by bitmask S,
    # starting from the start node (index 0).
    # S is a bitmask over destination indices 0..n-1 (mapped to node indices 1..n).
    full_mask = (1 << n) - 1

    # Initialize DP table with infinity
    dp: List[List[float]] = [
        [float("inf")] * n for _ in range(1 << n)
    ]
    # parent[S][i] = the previous destination index visited before arriving at i
    # with visited set S. Used to reconstruct the route.
    parent: List[List[int]] = [
        [-1] * n for _ in range(1 << n)
    ]

    # Base case: go directly from start (node 0) to each destination
    for i in range(n):
        dp[1 << i][i] = dist[0][i + 1]

    # Fill the DP table
    for mask in range(1, 1 << n):
        for last in range(n):
            # last must be in the current mask
            if not (mask & (1 << last)):
                continue
            if dp[mask][last] == float("inf"):
                continue

            # Try extending to each unvisited destination
            for next_dest in range(n):
                if mask & (1 << next_dest):
                    continue  # already visited
                new_mask = mask | (1 << next_dest)
                new_dist = dp[mask][last] + dist[last + 1][next_dest + 1]
                if new_dist < dp[new_mask][next_dest]:
                    dp[new_mask][next_dest] = new_dist
                    parent[new_mask][next_dest] = last

    # Find the optimal last destination before returning to start
    best_distance = float("inf")
    best_last = -1
    for last in range(n):
        total = dp[full_mask][last] + dist[last + 1][0]
        if total < best_distance:
            best_distance = total
            best_last = last

    # Reconstruct the route by backtracking through parent pointers
    route_indices: List[int] = []
    mask = full_mask
    current = best_last
    while current != -1:
        route_indices.append(current)
        prev = parent[mask][current]
        mask ^= (1 << current)
        current = prev

    route_indices.reverse()

    # Build the route as location strings
    route: Tuple[str, ...] = (
        (start,) + tuple(destinations[i] for i in route_indices) + (start,)
    )

    return route, best_distance


def estimate_route_distance(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> float:
    """Fast route distance estimate using nearest-neighbor + 2-opt.

    Designed for use during matching/capacity checks where speed matters
    more than exact optimality. Returns only the distance (no route
    reconstruction needed for capacity checks).

    Parameters
    ----------
    start : str
        The starting (and ending) location.
    destinations : Sequence[str]
        Destinations to visit.
    travel_matrix : Dict[str, Dict[str, float]]
        Travel distance matrix.

    Returns
    -------
    float
        Estimated total travel distance for the route.
    """
    if not destinations:
        return 0.0

    route, distance = nearest_neighbor_tsp(start, destinations, travel_matrix)
    _, distance = two_opt_improve(route, distance, travel_matrix)
    return distance


def find_optimal_route(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Find a route visiting all destinations and returning to start.

    Uses nearest-neighbor heuristic followed by 2-opt local search
    as the default algorithm. This provides near-optimal solutions
    in O(n²) time, making it scalable to large numbers of destinations.

    Parameters
    ----------
    start : str
        The starting (and ending) location for the route.
    destinations : Sequence[str]
        A sequence of destination locations that must be visited exactly once.
    travel_matrix : Dict[str, Dict[str, float]]
        A dictionary representing the travel distance between locations.

    Returns
    -------
    Tuple[Tuple[str, ...], float]
        A tuple containing the route (including start at the beginning
        and end) and its total distance.
    """
    if not destinations:
        return (start, start), 0.0

    route, distance = nearest_neighbor_tsp(start, destinations, travel_matrix)
    return two_opt_improve(route, distance, travel_matrix)
