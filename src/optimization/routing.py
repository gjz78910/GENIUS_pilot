"""Routing functions for field engineer scheduling.

The main entry point is `find_optimal_route`, which returns a route that:
- starts at `start`
- visits each destination once
- returns to `start`
"""

from __future__ import annotations

from itertools import permutations
from typing import Sequence, Tuple, Dict


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


_BRUTE_FORCE_THRESHOLD = 4


def _nearest_neighbor_tsp(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    route = [start]
    remaining = list(range(len(destinations)))
    current = start
    total_distance = 0.0

    while remaining:
        nearest_idx = min(remaining, key=lambda idx: travel_matrix[current][destinations[idx]])
        nearest = destinations[nearest_idx]
        total_distance += travel_matrix[current][nearest]
        route.append(nearest)
        remaining.remove(nearest_idx)
        current = nearest

    total_distance += travel_matrix[current][start]
    route.append(start)
    return tuple(route), total_distance


def _two_opt_improve(
    route: Tuple[str, ...], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    route_list = list(route)
    best_distance = sum(
        travel_matrix[route_list[k]][route_list[k + 1]]
        for k in range(len(route_list) - 1)
    )
    improved = True

    while improved:
        improved = False
        for i in range(1, len(route_list) - 2):
            for j in range(i + 1, len(route_list) - 1):
                old_segment = sum(
                    travel_matrix[route_list[k]][route_list[k + 1]]
                    for k in range(i - 1, j + 1)
                )
                reversed_seg = route_list[i : j + 1][::-1]
                new_segment = travel_matrix[route_list[i - 1]][reversed_seg[0]]
                for k in range(len(reversed_seg) - 1):
                    new_segment += travel_matrix[reversed_seg[k]][reversed_seg[k + 1]]
                new_segment += travel_matrix[reversed_seg[-1]][route_list[j + 1]]
                if new_segment < old_segment - 1e-10:
                    route_list[i : j + 1] = reversed_seg
                    best_distance += new_segment - old_segment
                    improved = True
                    break
            if improved:
                break

    total_distance = sum(
        travel_matrix[route_list[k]][route_list[k + 1]]
        for k in range(len(route_list) - 1)
    )
    return tuple(route_list), total_distance


def find_optimal_route(
    start: str,
    destinations: Sequence[str],
    travel_matrix: Dict[str, Dict[str, float]],
    *,
    optimize: bool = False,
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
    optimize : bool
        When True, apply 2-opt local search to improve route quality.
        Use for final routes; skip during repeated capacity estimation.

    Returns
    -------
    Tuple[Tuple[str, ...], float]
        A tuple containing the route (including start at the beginning
        and end) and its total distance.
    """
    if not destinations:
        return (start, start), 0.0
    if len(destinations) <= _BRUTE_FORCE_THRESHOLD:
        return brute_force_tsp(start, destinations, travel_matrix)
    route, distance = _nearest_neighbor_tsp(start, destinations, travel_matrix)
    if optimize:
        return _two_opt_improve(route, travel_matrix)
    return route, distance
