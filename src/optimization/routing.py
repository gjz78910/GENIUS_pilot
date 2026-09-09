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


def find_optimal_route(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Find a route visiting all destinations and returning to start.

    Uses Held-Karp DP (O(n² · 2ⁿ)) instead of brute-force (O(n!)) so it
    stays fast for up to ~20 destinations while still returning the exact
    optimal route.

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

    dests = list(destinations)
    n = len(dests)

    INF = float("inf")
    # dp[mask][i] = min cost to reach dests[i] having visited the subset in mask
    dp = [[INF] * n for _ in range(1 << n)]
    parent = [[-1] * n for _ in range(1 << n)]

    for i in range(n):
        dp[1 << i][i] = travel_matrix.get(start, {}).get(dests[i], INF)

    for mask in range(1, 1 << n):
        for last in range(n):
            if not (mask >> last & 1) or dp[mask][last] == INF:
                continue
            cost_so_far = dp[mask][last]
            row = travel_matrix.get(dests[last], {})
            for nxt in range(n):
                if mask >> nxt & 1:
                    continue
                new_cost = cost_so_far + row.get(dests[nxt], INF)
                new_mask = mask | (1 << nxt)
                if new_cost < dp[new_mask][nxt]:
                    dp[new_mask][nxt] = new_cost
                    parent[new_mask][nxt] = last

    full_mask = (1 << n) - 1
    best_cost = INF
    best_last = -1
    for last in range(n):
        total = dp[full_mask][last] + travel_matrix.get(dests[last], {}).get(start, INF)
        if total < best_cost:
            best_cost = total
            best_last = last

    # Reconstruct path by tracing parent pointers
    path: list[str] = []
    mask = full_mask
    cur = best_last
    while cur != -1:
        path.append(dests[cur])
        prev = parent[mask][cur]
        mask ^= (1 << cur)
        cur = prev
    path.reverse()

    return (start,) + tuple(path) + (start,), best_cost
