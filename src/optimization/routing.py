"""Routing functions for field engineer scheduling.

The main entry point is `find_optimal_route`, which returns a route that:
- starts at `start`
- visits each destination once
- returns to `start`
"""

from __future__ import annotations

from itertools import permutations
from typing import Sequence, Tuple, Dict


BRUTE_FORCE_THRESHOLD: int = 8
"""Maximum number of destinations for which brute-force is used.

At or below this threshold, brute_force_tsp guarantees an optimal result.
Above it, nearest_neighbor_tsp + two_opt_improve provides a fast heuristic.
"""


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
    """Construct a route using the nearest-neighbor heuristic.

    Builds a tour by greedily selecting the closest unvisited destination
    at each step, starting and ending at `start`.

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

    unvisited = set(destinations)
    route = [start]
    current = start
    total_distance = 0.0

    while unvisited:
        # Find the closest unvisited destination
        nearest = min(unvisited, key=lambda loc: travel_matrix[current][loc])
        nearest_dist = travel_matrix[current][nearest]

        route.append(nearest)
        total_distance += nearest_dist
        current = nearest
        unvisited.remove(nearest)

    # Return to start
    total_distance += travel_matrix[current][start]
    route.append(start)

    return tuple(route), total_distance


def _calculate_route_distance(
    route: Tuple[str, ...], travel_matrix: Dict[str, Dict[str, float]]
) -> float:
    """Calculate the total travel distance for a given route.

    Sums the travel distance between all consecutive location pairs in the route.

    Parameters
    ----------
    route : Tuple[str, ...]
        A tuple of location strings representing the route to measure.
    travel_matrix : Dict[str, Dict[str, float]]
        A dictionary representing the travel distance between locations.

    Returns
    -------
    float
        The total distance of the route (non-negative).
    """
    return sum(
        travel_matrix[route[i]][route[i + 1]] for i in range(len(route) - 1)
    )


def two_opt_improve(
    route: Tuple[str, ...], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Improve a route using 2-opt local search.

    Iteratively reverses sub-segments of the route when doing so reduces
    the total distance. Terminates when no single 2-opt swap yields an
    improvement (the route is locally optimal).

    Parameters
    ----------
    route : Tuple[str, ...]
        A valid route tuple starting and ending at the same location.
    travel_matrix : Dict[str, Dict[str, float]]
        A dictionary representing the travel distance between locations.

    Returns
    -------
    Tuple[Tuple[str, ...], float]
        A tuple containing the improved route and its total distance.
        The distance is guaranteed to be <= the input route's distance.
    """
    current_route = list(route)
    n = len(current_route)
    current_distance = _calculate_route_distance(tuple(current_route), travel_matrix)
    improved = True

    while improved:
        improved = False
        for i in range(1, n - 2):
            for j in range(i + 1, n - 1):
                # Reverse the segment between i and j (inclusive)
                new_route = current_route[:]
                new_route[i:j + 1] = new_route[i:j + 1][::-1]
                new_distance = _calculate_route_distance(tuple(new_route), travel_matrix)

                if new_distance < current_distance:
                    current_route = new_route
                    current_distance = new_distance
                    improved = True
                    break
            if improved:
                break

    improved_route = tuple(current_route)
    return improved_route, current_distance


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
    if not destinations:
        return (start, start), 0.0

    if len(destinations) <= BRUTE_FORCE_THRESHOLD:
        return brute_force_tsp(start, destinations, travel_matrix)

    # Heuristic path: construct with nearest-neighbor, then improve with 2-opt
    route, distance = nearest_neighbor_tsp(start, destinations, travel_matrix)
    route, distance = two_opt_improve(route, travel_matrix)
    return route, distance
