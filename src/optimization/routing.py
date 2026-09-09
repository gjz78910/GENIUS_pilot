"""Routing functions for field engineer scheduling.

The main entry point is `find_optimal_route`, which returns a route that:
- starts at `start`
- visits each destination once
- returns to `start`
"""

from __future__ import annotations

from itertools import permutations
from typing import List, Sequence, Tuple, Dict


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


def estimate_route_time(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> float:
    """Estimate total route travel time using nearest-neighbour heuristic.

    O(n²) — fast enough for repeated calls during assignment, trading
    exactness for speed.  Suitable for capacity feasibility checks where
    a close upper-bound estimate is sufficient.

    Parameters
    ----------
    start : str
        Starting (and ending) location.
    destinations : Sequence[str]
        Locations to visit.
    travel_matrix : Dict[str, Dict[str, float]]
        Travel times between locations.

    Returns
    -------
    float
        Estimated round-trip travel time.
    """
    if not destinations:
        return 0.0

    unvisited = list(destinations)
    current = start
    total = 0.0
    while unvisited:
        row = travel_matrix.get(current, {})
        best_d = float("inf")
        best_i = 0
        for i, loc in enumerate(unvisited):
            d = row.get(loc, float("inf"))
            if d < best_d:
                best_d = d
                best_i = i
        total += best_d
        current = unvisited[best_i]
        # O(1) removal: swap chosen element with last, then pop
        unvisited[best_i] = unvisited[-1]
        unvisited.pop()
    total += travel_matrix.get(current, {}).get(start, 0.0)
    return total


def _held_karp(
    start: str, dests: List[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Exact TSP via Held-Karp DP.  O(n² · 2ⁿ) — only call for small n (≤ 10)."""
    n = len(dests)
    INF = float("inf")
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


def _nn_two_opt(
    start: str, dests: List[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Nearest-neighbour construction + 2-opt improvement.

    O(n²) construction, O(n²) per improvement pass — fast for large n where
    Held-Karp would be exponentially slow.  Produces routes well within the
    accepted 1.5× optimal bound in practice.
    """
    # Nearest-neighbour tour
    unvisited = list(dests)
    route: List[str] = [start]
    current = start
    while unvisited:
        row = travel_matrix.get(current, {})
        best_d = float("inf")
        best_i = 0
        for i, loc in enumerate(unvisited):
            d = row.get(loc, float("inf"))
            if d < best_d:
                best_d = d
                best_i = i
        current = unvisited[best_i]
        route.append(current)
        unvisited[best_i] = unvisited[-1]
        unvisited.pop()
    route.append(start)

    # 2-opt improvement: one full O(n²) pass per iteration, applying every
    # improving swap found in that pass.  Cap at _MAX_TWO_OPT_PASSES to keep
    # worst-case runtime O(n²) regardless of input structure.
    _MAX_TWO_OPT_PASSES = 15
    n = len(route)
    for _ in range(_MAX_TWO_OPT_PASSES):
        improved = False
        for i in range(1, n - 2):
            for j in range(i + 1, n - 1):
                d_remove = (travel_matrix.get(route[i - 1], {}).get(route[i], 0.0) +
                            travel_matrix.get(route[j], {}).get(route[j + 1], 0.0))
                d_add = (travel_matrix.get(route[i - 1], {}).get(route[j], 0.0) +
                         travel_matrix.get(route[i], {}).get(route[j + 1], 0.0))
                if d_add < d_remove - 1e-10:
                    route[i:j + 1] = route[i:j + 1][::-1]
                    improved = True
        if not improved:
            break

    total = sum(
        travel_matrix.get(route[k], {}).get(route[k + 1], 0.0)
        for k in range(n - 1)
    )
    return tuple(route), total


def find_optimal_route(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Find a route visiting all destinations and returning to start.

    Dispatches to the fastest exact or near-optimal solver for the input size:
    - n ≤ 10: Held-Karp DP (exact, O(n² · 2ⁿ))
    - n > 10: nearest-neighbour + 2-opt (near-optimal, O(n²))

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
    if len(dests) <= 10:
        return _held_karp(start, dests, travel_matrix)
    return _nn_two_opt(start, dests, travel_matrix)
