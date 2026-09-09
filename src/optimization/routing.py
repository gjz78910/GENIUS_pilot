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


def nearest_neighbor_tsp(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Solve TSP using the nearest-neighbor heuristic.

    Greedy O(n²) approach: from the current location always travel to the
    closest unvisited destination.  Produces a good-enough route in a fraction
    of the time needed by brute force, which is O(n!).

    Parameters
    ----------
    start : str
        The starting (and ending) location for the route.
    destinations : Sequence[str]
        Locations that must be visited exactly once.
    travel_matrix : Dict[str, Dict[str, float]]
        Travel distances between locations.

    Returns
    -------
    Tuple[Tuple[str, ...], float]
        Route tuple (start … stops … start) and its total distance.
    """
    if not destinations:
        return (start, start), 0.0

    unvisited: List[str] = list(destinations)
    route: List[str] = [start]
    total_distance: float = 0.0
    current: str = start

    while unvisited:
        nearest = min(unvisited, key=lambda loc: travel_matrix[current][loc])
        total_distance += travel_matrix[current][nearest]
        current = nearest
        route.append(nearest)
        unvisited.remove(nearest)

    total_distance += travel_matrix[current][start]
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
    return nearest_neighbor_tsp(start, destinations, travel_matrix)
