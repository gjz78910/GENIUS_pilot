"""Routing functions for field engineer scheduling.

The main entry point is `find_optimal_route`, which returns a route that:
- starts at `start`
- visits each destination once
- returns to `start`

Algorithm selection:
- n <= HELD_KARP_THRESHOLD: exact Held-Karp DP (O(n² · 2ⁿ))
- n >  HELD_KARP_THRESHOLD: nearest-neighbour construction + 2-opt improvement
"""

from __future__ import annotations

from itertools import permutations
from typing import Dict, List, Sequence, Tuple

# Above this many destinations switch to heuristic (2^12 × 144 ≈ 590K ops per call)
HELD_KARP_THRESHOLD = 12


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
    if not destinations:
        return (start, start), 0.0

    best_distance: float = float("inf")
    best_route: Tuple[str, ...] | None = None

    for perm in permutations(destinations):
        distance: float = 0.0
        current = start
        for loc in perm:
            distance += travel_matrix[current][loc]
            current = loc
        distance += travel_matrix[current][start]
        if distance < best_distance:
            best_distance = distance
            best_route = (start,) + perm + (start,)

    assert best_route is not None
    return best_route, best_distance


def _edge(a: str, b: str, travel_matrix: Dict[str, Dict[str, float]]) -> float:
    return travel_matrix.get(a, {}).get(b, float("inf"))


def held_karp_tsp(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Exact TSP via Held-Karp bitmask DP.

    Time O(n² · 2ⁿ), space O(n · 2ⁿ).  Practical for n ≤ ~15.
    """
    dests: List[str] = list(destinations)
    n = len(dests)

    if n == 0:
        return (start, start), 0.0
    if n == 1:
        d = _edge(start, dests[0], travel_matrix) + _edge(dests[0], start, travel_matrix)
        return (start, dests[0], start), d

    INF = float("inf")
    full_mask = (1 << n) - 1

    dp = [[INF] * n for _ in range(full_mask + 1)]
    parent: List[List[int]] = [[-1] * n for _ in range(full_mask + 1)]

    for i in range(n):
        dp[1 << i][i] = _edge(start, dests[i], travel_matrix)

    for mask in range(1, full_mask + 1):
        for i in range(n):
            if not (mask & (1 << i)):
                continue
            cur_cost = dp[mask][i]
            if cur_cost == INF:
                continue
            for j in range(n):
                if mask & (1 << j):
                    continue
                new_mask = mask | (1 << j)
                new_cost = cur_cost + _edge(dests[i], dests[j], travel_matrix)
                if new_cost < dp[new_mask][j]:
                    dp[new_mask][j] = new_cost
                    parent[new_mask][j] = i

    best_cost = INF
    last = -1
    for i in range(n):
        total = dp[full_mask][i] + _edge(dests[i], start, travel_matrix)
        # Prefer non-start ending node on a tie to avoid a trailing duplicate in the route
        is_better = total < best_cost - 1e-10
        is_tie_preferred = (
            abs(total - best_cost) <= 1e-10
            and dests[i] != start
            and (last == -1 or dests[last] == start)
        )
        if is_better or is_tie_preferred:
            best_cost = total
            last = i

    # Reconstruct path
    path: List[str] = []
    mask = full_mask
    cur = last
    while cur != -1:
        path.append(dests[cur])
        prev = parent[mask][cur]
        mask ^= (1 << cur)
        cur = prev
    path.reverse()

    return (start,) + tuple(path) + (start,), best_cost


def _route_cost(route: List[str], travel_matrix: Dict[str, Dict[str, float]]) -> float:
    return sum(_edge(route[i], route[i + 1], travel_matrix) for i in range(len(route) - 1))


def _nearest_neighbour(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[List[str], float]:
    """Greedy nearest-neighbour construction heuristic."""
    unvisited = list(destinations)
    route: List[str] = [start]
    current = start
    while unvisited:
        nearest = min(unvisited, key=lambda x: _edge(current, x, travel_matrix))
        route.append(nearest)
        current = nearest
        unvisited.remove(nearest)
    route.append(start)
    return route, _route_cost(route, travel_matrix)


def _two_opt(
    route: List[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[List[str], float]:
    """Improve a route by iteratively reversing sub-segments (2-opt)."""
    best = route[:]
    best_cost = _route_cost(best, travel_matrix)
    n = len(best)
    improved = True
    while improved:
        improved = False
        for i in range(1, n - 2):
            for j in range(i + 1, n - 1):
                candidate = best[:i] + best[i : j + 1][::-1] + best[j + 1 :]
                c = _route_cost(candidate, travel_matrix)
                if c < best_cost - 1e-10:
                    best = candidate
                    best_cost = c
                    improved = True
    return best, best_cost


def estimate_route_time(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> float:
    """Fast O(n²) travel-time estimate using nearest-neighbour construction.

    Used during assignment to check capacity without paying the full
    optimisation cost.  Always returns a valid (if suboptimal) tour cost.
    """
    if not destinations:
        return 0.0
    _, cost = _nearest_neighbour(start, destinations, travel_matrix)
    return cost


def find_optimal_route(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Find a route visiting all destinations and returning to start.

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
    n = len(destinations)
    if n == 0:
        return (start, start), 0.0

    if n <= HELD_KARP_THRESHOLD:
        return held_karp_tsp(start, destinations, travel_matrix)

    route, _ = _nearest_neighbour(start, destinations, travel_matrix)
    route, cost = _two_opt(route, travel_matrix)
    return tuple(route), cost
