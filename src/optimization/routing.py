"""Routing functions for field engineer scheduling.

The main entry point is `find_optimal_route`, which returns a route that:
- starts at `start`
- visits each destination once
- returns to `start`
"""

from __future__ import annotations

from itertools import permutations
from typing import Sequence, Tuple, Dict


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


def held_karp_tsp(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Solve a travelling-salesperson problem using the Held-Karp algorithm.

    Uses bitmask dynamic programming to find the optimal route in
    O(n^2 * 2^n) time, significantly faster than brute force O(n!).

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
    nodes = list(destinations)

    # dp[visited_mask][i] = minimum distance to reach nodes[i] having visited
    # exactly the set of nodes indicated by visited_mask, starting from start.
    full_mask = (1 << n) - 1
    dp: Dict[Tuple[int, int], float] = {}
    parent: Dict[Tuple[int, int], int] = {}

    # Base case: go directly from start to each destination
    for i in range(n):
        mask = 1 << i
        dp[(mask, i)] = travel_matrix[start][nodes[i]]

    # Fill DP table: for each subset of visited nodes, try extending the route
    for mask in range(1, full_mask + 1):
        for last in range(n):
            if not (mask & (1 << last)):
                continue
            if (mask, last) not in dp:
                continue
            for nxt in range(n):
                if mask & (1 << nxt):
                    continue
                new_mask = mask | (1 << nxt)
                new_dist = dp[(mask, last)] + travel_matrix[nodes[last]][nodes[nxt]]
                if new_dist < dp.get((new_mask, nxt), float("inf")):
                    dp[(new_mask, nxt)] = new_dist
                    parent[(new_mask, nxt)] = last

    # Find the best final node (including return to start)
    best_distance = float("inf")
    best_last = -1
    for i in range(n):
        total = dp.get((full_mask, i), float("inf")) + travel_matrix[nodes[i]][start]
        if total < best_distance:
            best_distance = total
            best_last = i

    # Reconstruct the route by following parent pointers
    route_indices: list[int] = []
    mask = full_mask
    current = best_last
    while mask:
        route_indices.append(current)
        prev = parent.get((mask, current))
        if prev is None:
            break
        mask ^= (1 << current)
        current = prev

    route_indices.reverse()
    best_route = (start,) + tuple(nodes[i] for i in route_indices) + (start,)

    return best_route, best_distance


def nearest_neighbor_tsp(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Solve TSP using the nearest-neighbor heuristic in O(n^2) time.

    Not optimal, but fast enough for capacity estimation during matching
    and as a fallback for large destination sets.
    """
    if not destinations:
        return (start, start), 0.0

    unvisited = list(destinations)
    route = [start]
    total_distance = 0.0
    current = start

    while unvisited:
        nearest = min(unvisited, key=lambda loc: travel_matrix[current][loc])
        total_distance += travel_matrix[current][nearest]
        route.append(nearest)
        unvisited.remove(nearest)
        current = nearest

    total_distance += travel_matrix[current][start]
    route.append(start)
    return tuple(route), total_distance


_HELD_KARP_THRESHOLD = 10


def estimate_route_cost(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> float:
    """Return a fast travel-time estimate using nearest-neighbor. O(n^2)."""
    _, distance = nearest_neighbor_tsp(start, destinations, travel_matrix)
    return distance


def find_optimal_route(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Find a route visiting all destinations and returning to start.

    Uses Held-Karp (exact) for small destination sets and falls back to
    nearest-neighbor for larger ones to guarantee bounded runtime.

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
    if len(destinations) <= _HELD_KARP_THRESHOLD:
        return held_karp_tsp(start, destinations, travel_matrix)
    return nearest_neighbor_tsp(start, destinations, travel_matrix)
