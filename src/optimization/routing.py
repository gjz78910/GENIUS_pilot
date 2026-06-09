"""Routing functions for field engineer scheduling.

The main entry point is `find_optimal_route`, which returns a route that:
- starts at `start`
- visits each destination once
- returns to `start`

Uses nearest-neighbour + 2-opt, exploiting symmetric distances.
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple


def _route_distance(
    route: List[str], travel_matrix: Dict[str, Dict[str, float]]
) -> float:
    """Calculate total distance for a given route."""
    total = 0.0
    for i in range(len(route) - 1):
        total += travel_matrix[route[i]][route[i + 1]]
    return total


def _nearest_neighbour(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> List[str]:
    """Build an initial route using nearest-neighbour heuristic.

    Handles duplicate locations by tracking indices.
    """
    unvisited = list(range(len(destinations)))
    route = [start]
    current = start

    while unvisited:
        best_idx = min(unvisited, key=lambda idx: travel_matrix[current][destinations[idx]])
        nearest = destinations[best_idx]
        route.append(nearest)
        unvisited.remove(best_idx)
        current = nearest

    route.append(start)
    return route


def _two_opt(
    route: List[str], travel_matrix: Dict[str, Dict[str, float]]
) -> List[str]:
    """Improve a route using 2-opt. Symmetric distances make reversal valid.

    Limited to n passes to guarantee termination.
    """
    n = len(route)
    max_passes = n * 2
    for _ in range(max_passes):
        improved = False
        for i in range(1, n - 2):
            for j in range(i + 1, n - 1):
                # Current edge costs
                d1 = travel_matrix[route[i - 1]][route[i]]
                d2 = travel_matrix[route[j]][route[j + 1]]
                # New edge costs after reversing segment [i..j]
                d3 = travel_matrix[route[i - 1]][route[j]]
                d4 = travel_matrix[route[i]][route[j + 1]]
                if d3 + d4 < d1 + d2 - 1e-10:
                    route[i : j + 1] = route[i : j + 1][::-1]
                    improved = True
        if not improved:
            break
    return route


def find_optimal_route(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Find a route visiting all destinations and returning to start.

    Uses nearest-neighbour + 2-opt. Symmetric distances make segment
    reversal a valid improvement move.
    """
    if not destinations:
        return (start, start), 0.0

    route = _nearest_neighbour(start, destinations, travel_matrix)
    route = _two_opt(route, travel_matrix)

    distance = _route_distance(route, travel_matrix)
    return tuple(route), distance
