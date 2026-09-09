"""Routing functions for field engineer scheduling.

The main entry point is `find_optimal_route`, which returns a route that:
- starts at `start`
- visits each destination once
- returns to `start`
"""

from __future__ import annotations

from typing import List, Sequence, Tuple, Dict


def nearest_neighbour_tsp(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Solve a travelling-salesperson problem using a nearest-neighbour heuristic.

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
        A tuple containing the route (including the start location at
        the beginning and end) and the total distance of that route.
    """
    if not destinations:
        return (start, start), 0.0

    unvisited: List[str] = list(destinations)
    route: List[str] = [start]
    total_distance: float = 0.0
    current = start

    while unvisited:
        nearest = min(unvisited, key=lambda loc: travel_matrix[current].get(loc, float("inf")))
        total_distance += travel_matrix[current].get(nearest, float("inf"))
        current = nearest
        route.append(nearest)
        unvisited.remove(nearest)

    # return to start
    total_distance += travel_matrix[current].get(start, float("inf"))
    route.append(start)

    return tuple(route), total_distance


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
    return nearest_neighbour_tsp(start, destinations, travel_matrix)
