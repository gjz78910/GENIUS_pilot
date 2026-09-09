"""Routing functions for field engineer scheduling.

The main entry point is `find_optimal_route`, which returns a route that:
- starts at `start`
- visits each destination once
- optionally returns to `start` (controlled by `return_to_start`)
"""

from __future__ import annotations

from itertools import permutations
from typing import Sequence, Tuple, Dict

_BRUTE_FORCE_THRESHOLD = 8


def brute_force_tsp(
    start: str,
    destinations: Sequence[str],
    travel_matrix: Dict[str, Dict[str, float]],
    return_to_start: bool = True,
) -> Tuple[Tuple[str, ...], float]:
    """Solve TSP using brute force. Only suitable for small inputs (≤8 destinations).

    Parameters
    ----------
    start : str
        The starting location for the route.
    destinations : Sequence[str]
        Destination locations that must be visited exactly once.
    travel_matrix : Dict[str, Dict[str, float]]
        Travel distance/time between locations.
    return_to_start : bool
        Whether to include the return leg back to start.

    Returns
    -------
    Tuple[Tuple[str, ...], float]
        Best route and its total distance.
    """
    if not destinations:
        return ((start, start) if return_to_start else (start,)), 0.0

    best_distance: float = float("inf")
    best_route: Tuple[str, ...] | None = None

    for perm in permutations(destinations):
        distance: float = 0.0
        current = start
        for loc in perm:
            distance += travel_matrix.get(current, {}).get(loc, float("inf"))
            current = loc
        if return_to_start:
            distance += travel_matrix.get(current, {}).get(start, float("inf"))
        if distance < best_distance:
            best_distance = distance
            route = (start,) + perm
            best_route = route + (start,) if return_to_start else route

    assert best_route is not None
    return best_route, best_distance


def nearest_neighbor_tsp(
    start: str,
    destinations: Sequence[str],
    travel_matrix: Dict[str, Dict[str, float]],
    return_to_start: bool = True,
) -> Tuple[Tuple[str, ...], float]:
    """Solve TSP using a greedy nearest-neighbor heuristic. O(n²) — scales to large inputs.

    Parameters
    ----------
    start : str
        The starting location for the route.
    destinations : Sequence[str]
        Destination locations that must be visited exactly once.
    travel_matrix : Dict[str, Dict[str, float]]
        Travel distance/time between locations.
    return_to_start : bool
        Whether to include the return leg back to start.

    Returns
    -------
    Tuple[Tuple[str, ...], float]
        Heuristic route and its total distance.
    """
    if not destinations:
        return ((start, start) if return_to_start else (start,)), 0.0

    unvisited = list(destinations)
    route = [start]
    total: float = 0.0
    current = start

    while unvisited:
        next_loc = min(
            unvisited,
            key=lambda loc: travel_matrix.get(current, {}).get(loc, float("inf")),
        )
        total += travel_matrix.get(current, {}).get(next_loc, float("inf"))
        current = next_loc
        route.append(current)
        unvisited.remove(current)

    if return_to_start:
        total += travel_matrix.get(current, {}).get(start, float("inf"))
        route.append(start)

    return tuple(route), total


def find_optimal_route(
    start: str,
    destinations: Sequence[str],
    travel_matrix: Dict[str, Dict[str, float]],
    return_to_start: bool = True,
) -> Tuple[Tuple[str, ...], float]:
    """Find a route visiting all destinations, optionally returning to start.

    Uses brute-force for small inputs (≤8 destinations) and nearest-neighbor
    heuristic for larger ones.

    Parameters
    ----------
    start : str
        The starting location for the route.
    destinations : Sequence[str]
        Destination locations that must be visited exactly once.
    travel_matrix : Dict[str, Dict[str, float]]
        Travel distance/time between locations.
    return_to_start : bool
        Whether to include the return leg back to start. Set to False when
        estimating one-way working-day travel cost.

    Returns
    -------
    Tuple[Tuple[str, ...], float]
        Route and its total distance.
    """
    if len(destinations) <= _BRUTE_FORCE_THRESHOLD:
        return brute_force_tsp(start, destinations, travel_matrix, return_to_start)
    return nearest_neighbor_tsp(start, destinations, travel_matrix, return_to_start)
