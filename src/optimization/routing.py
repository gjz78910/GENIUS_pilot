"""Routing functions for field engineer scheduling.

The main entry point is `find_optimal_route`, which returns a route that:
- starts at `start`
- visits each destination once
- returns to `start`
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


def held_karp_tsp(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Solve TSP exactly using Held-Karp dynamic programming. O(n^2 * 2^n).

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

    dests: List[str] = list(destinations)
    n = len(dests)
    INF = float("inf")

    # dp[(mask, i)] = min cost to reach dests[i] after visiting exactly the nodes in mask,
    # departing from start.
    dp: Dict[Tuple[int, int], float] = {}
    parent: Dict[Tuple[int, int], int] = {}

    for i in range(n):
        dp[(1 << i, i)] = travel_matrix[start][dests[i]]
        parent[(1 << i, i)] = -1

    for mask in range(1, 1 << n):
        for last in range(n):
            if not (mask & (1 << last)):
                continue
            cost = dp.get((mask, last), INF)
            if cost == INF:
                continue
            for nxt in range(n):
                if mask & (1 << nxt):
                    continue
                new_mask = mask | (1 << nxt)
                new_cost = cost + travel_matrix[dests[last]][dests[nxt]]
                if new_cost < dp.get((new_mask, nxt), INF):
                    dp[(new_mask, nxt)] = new_cost
                    parent[(new_mask, nxt)] = last

    full_mask = (1 << n) - 1
    best_cost = INF
    best_last = -1
    for i in range(n):
        cost = dp.get((full_mask, i), INF) + travel_matrix[dests[i]][start]
        if cost < best_cost:
            best_cost = cost
            best_last = i

    # Reconstruct path by following parent pointers
    path_indices: List[int] = []
    mask = full_mask
    last = best_last
    while last != -1:
        path_indices.append(last)
        prev = parent[(mask, last)]
        mask ^= (1 << last)
        last = prev
    path_indices.reverse()

    route: Tuple[str, ...] = (start,) + tuple(dests[i] for i in path_indices) + (start,)
    return route, best_cost


def nearest_neighbor_tsp(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Solve TSP approximately using a nearest-neighbour greedy heuristic. O(n^2).

    Not guaranteed to find the optimal route, but runs in O(n^2) making it
    practical for large n where exact methods are too slow.

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
        A tuple containing the route (including the start location at the
        beginning and end) and the total distance of that route.
    """
    if not destinations:
        return (start, start), 0.0

    unvisited = set(destinations)
    route: List[str] = [start]
    total_distance = 0.0
    current = start

    while unvisited:
        nearest = min(
            unvisited,
            key=lambda loc: travel_matrix.get(current, {}).get(loc, float("inf")),
        )
        total_distance += travel_matrix[current][nearest]
        route.append(nearest)
        unvisited.remove(nearest)
        current = nearest

    total_distance += travel_matrix[current][start]
    route.append(start)
    return tuple(route), total_distance


# Use Held-Karp (exact) for small routes; nearest-neighbour (fast) above this threshold.
_HELD_KARP_MAX_N = 10


def find_optimal_route(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Find a route visiting all destinations and returning to start.

    Uses Held-Karp (exact, O(n^2 * 2^n)) for small routes and nearest-neighbour
    (approximate, O(n^2)) for larger ones where exact methods are too slow.

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
    if len(destinations) <= _HELD_KARP_MAX_N:
        return held_karp_tsp(start, destinations, travel_matrix)
    return nearest_neighbor_tsp(start, destinations, travel_matrix)
