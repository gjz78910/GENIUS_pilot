"""Routing functions for field engineer scheduling.

The main entry point is `find_optimal_route`, which returns a route that:
- starts at `start`
- visits each destination once
- returns to `start`
"""

from __future__ import annotations

from typing import Sequence, Tuple, Dict


def nearest_neighbour_tsp(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Solve TSP with a nearest-neighbour greedy heuristic — O(n²).

    Not guaranteed optimal but runs in O(n²) vs O(n·n!) for brute force,
    making it practical for real engineer schedules (10–100+ stops).
    """
    if not destinations:
        return (start, start), 0.0

    unvisited = set(destinations)
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


def find_optimal_route(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Find a route visiting all destinations and returning to start."""
    return nearest_neighbour_tsp(start, destinations, travel_matrix)
