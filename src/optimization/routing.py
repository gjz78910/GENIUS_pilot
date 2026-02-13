"""Routing functions for field engineer scheduling.

The entry point `find_optimal_route` uses a hybrid strategy:
- exact dynamic programming for small instances
- fast heuristic (nearest-neighbour + 2-opt) for larger instances
"""

from __future__ import annotations

from collections import Counter
from typing import Dict, List, Sequence, Tuple


def _distance(a: str, b: str, travel_matrix: Dict[str, Dict[str, float]]) -> float:
    """Return distance between two locations; missing edges are treated as inf."""
    return travel_matrix.get(a, {}).get(b, float("inf"))


def _normalize_destinations(start: str, destinations: Sequence[str]) -> List[str]:
    """Deduplicate destinations while preserving order.

    Repeated jobs at the same location do not require repeated route visits.
    """
    seen = set()
    unique: List[str] = []
    for location in destinations:
        if location == start:
            continue
        if location in seen:
            continue
        seen.add(location)
        unique.append(location)
    return unique


def _route_distance(route: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]) -> float:
    """Compute total route distance."""
    total = 0.0
    for idx in range(len(route) - 1):
        total += _distance(route[idx], route[idx + 1], travel_matrix)
    return total


def _held_karp_tsp(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Exact TSP with dynamic programming for small destination sets."""
    n = len(destinations)
    # dp[(mask, last_idx)] = (cost, predecessor_idx)
    dp: Dict[Tuple[int, int], Tuple[float, int | None]] = {}

    for i in range(n):
        loc = destinations[i]
        dp[(1 << i, i)] = (_distance(start, loc, travel_matrix), None)

    for mask in range(1, 1 << n):
        for last in range(n):
            if not (mask & (1 << last)):
                continue
            state = (mask, last)
            if state not in dp:
                continue
            cost_so_far, _ = dp[state]
            remaining = ((1 << n) - 1) ^ mask
            r = remaining
            while r:
                bit = r & -r
                nxt = bit.bit_length() - 1
                new_mask = mask | bit
                new_cost = cost_so_far + _distance(
                    destinations[last], destinations[nxt], travel_matrix
                )
                new_state = (new_mask, nxt)
                old = dp.get(new_state)
                if old is None or new_cost < old[0]:
                    dp[new_state] = (new_cost, last)
                r ^= bit

    full_mask = (1 << n) - 1
    best_cost = float("inf")
    best_last = 0
    for last in range(n):
        state = (full_mask, last)
        if state not in dp:
            continue
        cost = dp[state][0] + _distance(destinations[last], start, travel_matrix)
        if cost < best_cost:
            best_cost = cost
            best_last = last

    order: List[int] = []
    mask = full_mask
    last = best_last
    while True:
        order.append(last)
        prev = dp[(mask, last)][1]
        if prev is None:
            break
        mask ^= 1 << last
        last = prev
    order.reverse()

    route = tuple([start] + [destinations[i] for i in order] + [start])
    return route, best_cost


def _nearest_neighbor_route(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[List[str], float]:
    """Construct a fast initial route."""
    unvisited = set(destinations)
    route = [start]
    current = start
    while unvisited:
        nxt = min(unvisited, key=lambda loc: _distance(current, loc, travel_matrix))
        route.append(nxt)
        unvisited.remove(nxt)
        current = nxt
    route.append(start)
    return route, _route_distance(route, travel_matrix)


def _two_opt(
    route: List[str], travel_matrix: Dict[str, Dict[str, float]], max_iterations: int = 2
) -> Tuple[List[str], float]:
    """Perform bounded 2-opt to improve a heuristic route quickly."""
    best_route = route[:]
    best_cost = _route_distance(best_route, travel_matrix)
    n = len(best_route)
    improved = True
    iterations = 0
    while improved and iterations < max_iterations:
        improved = False
        iterations += 1
        for i in range(1, n - 2):
            for j in range(i + 1, n - 1):
                if j - i == 1:
                    continue
                a, b = best_route[i - 1], best_route[i]
                c, d = best_route[j - 1], best_route[j]
                delta = (
                    _distance(a, c, travel_matrix)
                    + _distance(b, d, travel_matrix)
                    - _distance(a, b, travel_matrix)
                    - _distance(c, d, travel_matrix)
                )
                if delta < -1e-12:
                    best_route[i:j] = reversed(best_route[i:j])
                    best_cost += delta
                    improved = True
    return best_route, best_cost


def _heuristic_tsp(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Heuristic route for larger instances."""
    initial_route, _ = _nearest_neighbor_route(start, destinations, travel_matrix)
    improved_route, improved_cost = _two_opt(initial_route, travel_matrix, max_iterations=2)
    return tuple(improved_route), improved_cost


def find_optimal_route(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Find a route visiting all destinations and returning to start."""
    destination_counts = Counter(destinations)
    unique_destinations = _normalize_destinations(start, destinations)
    if not destination_counts:
        return (start, start), 0.0

    # Base route optimisation on unique non-start destinations.
    if not unique_destinations:
        base_route = (start, start)
    elif len(unique_destinations) <= 12:
        base_route, _ = _held_karp_tsp(start, unique_destinations, travel_matrix)
    else:
        base_route, _ = _heuristic_tsp(start, unique_destinations, travel_matrix)

    # Expand route so repeated job locations still appear once per job.
    expanded: List[str] = [start]
    start_repeat = destination_counts.get(start, 0)
    if start_repeat > 0:
        expanded.extend([start] * start_repeat)
    for location in base_route[1:-1]:
        repeats = destination_counts.get(location, 0)
        if repeats > 0:
            expanded.extend([location] * repeats)
    expanded.append(start)

    expanded_tuple = tuple(expanded)
    return expanded_tuple, _route_distance(expanded_tuple, travel_matrix)
