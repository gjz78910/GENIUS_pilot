"""Routing functions for field engineer scheduling.

The main entry point is `find_optimal_route`, which returns a route that:
- starts at `start`
- visits each destination once
- returns to `start`
"""

from __future__ import annotations

from itertools import permutations
from typing import Sequence, Tuple, Dict

_BRUTE_FORCE_THRESHOLD = 8


def brute_force_tsp(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Solve TSP exactly via brute force — only practical for n ≤ 8."""
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


def _nearest_neighbour_tsp(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Nearest-neighbour greedy heuristic — O(n²)."""
    unvisited = list(destinations)
    route = [start]
    current = start
    total = 0.0
    while unvisited:
        nearest = min(
            unvisited,
            key=lambda loc: travel_matrix[current].get(loc, float("inf")),
        )
        total += travel_matrix[current][nearest]
        current = nearest
        route.append(nearest)
        unvisited.remove(nearest)
    total += travel_matrix[current][start]
    route.append(start)
    return tuple(route), total


def _two_opt_improve(
    route: Tuple[str, ...], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """2-opt local search: repeatedly reverse segments until no improvement — O(n²) per pass."""
    nodes = list(route)
    improved = True
    while improved:
        improved = False
        for i in range(1, len(nodes) - 2):
            for j in range(i + 1, len(nodes) - 1):
                d_before = (
                    travel_matrix[nodes[i - 1]][nodes[i]]
                    + travel_matrix[nodes[j]][nodes[j + 1]]
                )
                d_after = (
                    travel_matrix[nodes[i - 1]][nodes[j]]
                    + travel_matrix[nodes[i]][nodes[j + 1]]
                )
                if d_after < d_before:
                    nodes[i : j + 1] = nodes[i : j + 1][::-1]
                    improved = True
    total = sum(
        travel_matrix[nodes[k]][nodes[k + 1]] for k in range(len(nodes) - 1)
    )
    return tuple(nodes), total


def find_optimal_route(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Find a route visiting all destinations and returning to start.

    Uses exact brute force for small inputs (≤8 stops) and a
    nearest-neighbour + 2-opt heuristic for larger ones.
    """
    if not destinations:
        return (start, start), 0.0
    if len(destinations) <= _BRUTE_FORCE_THRESHOLD:
        return brute_force_tsp(start, destinations, travel_matrix)
    nn_route, _ = _nearest_neighbour_tsp(start, destinations, travel_matrix)
    return _two_opt_improve(nn_route, travel_matrix)
