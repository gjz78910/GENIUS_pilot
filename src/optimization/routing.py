"""Routing functions for field engineer scheduling.

The main entry point is `find_optimal_route`, which returns a route that:
- starts at `start`
- visits each destination once
- returns to `start`

Strategy:
- For small destination lists (≤ BRUTE_FORCE_THRESHOLD), use exact brute-force.
- For larger lists, use nearest-neighbour construction followed by 2-opt improvement.
"""

from __future__ import annotations

from itertools import permutations
from typing import Sequence, Tuple, Dict, List

# Threshold at which we switch from exact brute-force to heuristic.
# 8! = 40,320 completes in milliseconds; above that we use heuristics.
BRUTE_FORCE_THRESHOLD = 8


def brute_force_tsp(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Solve a travelling-salesperson problem using brute force.

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


def _nearest_neighbour_tsp(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[List[str], float]:
    """Build an initial tour using the nearest-neighbour heuristic.

    Starting from `start`, repeatedly visit the closest unvisited destination,
    then return to `start`.

    Returns
    -------
    Tuple[List[str], float]
        The route as a mutable list (start … start) and its total distance.
    """
    unvisited = list(destinations)
    route: List[str] = [start]
    total_distance = 0.0
    current = start

    while unvisited:
        # Find nearest unvisited destination
        nearest = min(unvisited, key=lambda loc: travel_matrix[current][loc])
        total_distance += travel_matrix[current][nearest]
        route.append(nearest)
        unvisited.remove(nearest)
        current = nearest

    # Return to start
    total_distance += travel_matrix[current][start]
    route.append(start)
    return route, total_distance


def _route_distance(route: List[str], travel_matrix: Dict[str, Dict[str, float]]) -> float:
    """Calculate total distance of a route."""
    total = 0.0
    for i in range(len(route) - 1):
        total += travel_matrix[route[i]][route[i + 1]]
    return total


def _two_opt_improve(
    route: List[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[List[str], float]:
    """Improve a tour using 2-opt swaps.

    Repeatedly reverses subsections of the route. If a reversal reduces the
    total distance, it is kept. Continues until no further improvement is found.

    Parameters
    ----------
    route : List[str]
        A tour starting and ending at the same location.
    travel_matrix : Dict[str, Dict[str, float]]
        Travel distances between locations.

    Returns
    -------
    Tuple[List[str], float]
        The improved route and its total distance.
    """
    improved = True
    best_route = route[:]
    best_distance = _route_distance(best_route, travel_matrix)

    while improved:
        improved = False
        # Indices 1..n-1 are the destinations (0 and n are the fixed start)
        for i in range(1, len(best_route) - 2):
            for j in range(i + 1, len(best_route) - 1):
                # Reverse the segment between i and j (inclusive)
                new_route = best_route[:i] + best_route[i:j + 1][::-1] + best_route[j + 1:]
                new_distance = _route_distance(new_route, travel_matrix)
                if new_distance < best_distance:
                    best_route = new_route
                    best_distance = new_distance
                    improved = True
        # Each full pass through the loops; repeat until stable

    return best_route, best_distance


def nearest_neighbour_2opt_tsp(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Solve TSP using nearest-neighbour construction + 2-opt improvement.

    Parameters
    ----------
    start : str
        The starting (and ending) location for the route.
    destinations : Sequence[str]
        Destinations to visit exactly once.
    travel_matrix : Dict[str, Dict[str, float]]
        Travel distances between locations.

    Returns
    -------
    Tuple[Tuple[str, ...], float]
        The best route found and its total distance.
    """
    if not destinations:
        return (start, start), 0.0

    # Phase 1: construct initial tour via nearest-neighbour
    route, _ = _nearest_neighbour_tsp(start, destinations, travel_matrix)

    # Phase 2: improve with 2-opt
    route, distance = _two_opt_improve(route, travel_matrix)

    return tuple(route), distance


def find_optimal_route(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Find a route visiting all destinations and returning to start.

    Uses exact brute-force for small inputs (≤ BRUTE_FORCE_THRESHOLD destinations)
    and nearest-neighbour + 2-opt heuristic for larger inputs.

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
    if len(destinations) <= BRUTE_FORCE_THRESHOLD:
        return brute_force_tsp(start, destinations, travel_matrix)
    else:
        return nearest_neighbour_2opt_tsp(start, destinations, travel_matrix)
