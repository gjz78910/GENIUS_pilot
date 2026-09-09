"""Routing functions for field engineer scheduling.

The main entry point is `find_optimal_route`, which returns a route that:
- starts at `start`
- visits each destination once
- returns to `start`
"""

from __future__ import annotations

from typing import Sequence, Tuple, Dict, List


def _route_distance(route: List[str], travel_matrix: Dict[str, Dict[str, float]]) -> float:
    """Return the total distance of a closed route (last node back to first)."""
    return sum(
        travel_matrix[route[i]][route[i + 1]] for i in range(len(route) - 1)
    ) + travel_matrix[route[-1]][route[0]]


def _nearest_neighbour(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> List[str]:
    """Build an initial route using the nearest-neighbour heuristic. O(n²)."""
    unvisited = list(destinations)
    route = [start]
    current = start
    while unvisited:
        next_loc = min(unvisited, key=lambda loc: travel_matrix[current][loc])
        route.append(next_loc)
        unvisited.remove(next_loc)
        current = next_loc
    return route


def _two_opt(
    route: List[str], travel_matrix: Dict[str, Dict[str, float]]
) -> List[str]:
    """Improve a route with 2-opt edge swaps until no improvement is found."""
    best = route[:]
    improved = True
    while improved:
        improved = False
        for i in range(1, len(best) - 1):
            for j in range(i + 1, len(best)):
                candidate = best[:i] + best[i:j + 1][::-1] + best[j + 1:]
                if _route_distance(candidate, travel_matrix) < _route_distance(best, travel_matrix):
                    best = candidate
                    improved = True
    return best


def find_optimal_route(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Find a route visiting all destinations and returning to start.

    Uses nearest-neighbour construction followed by 2-opt improvement.
    O(n²) in practice — handles 10+ destinations efficiently.

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

    route = _nearest_neighbour(start, destinations, travel_matrix)
    route = _two_opt(route, travel_matrix)
    distance = _route_distance(route, travel_matrix)
    return tuple(route) + (route[0],), distance
