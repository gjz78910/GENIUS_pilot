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


# Above this many destinations, brute force (n!) becomes too slow to use on
# every routing call, so we switch to a nearest-neighbour + 2-opt heuristic.
_BRUTE_FORCE_MAX_DESTINATIONS = 8


def _nearest_neighbor_route(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[str, ...]:
    """Build a route greedily by always visiting the closest unvisited stop."""
    remaining = list(destinations)
    route = [start]
    current = start
    while remaining:
        nxt = min(remaining, key=lambda d: travel_matrix.get(current, {}).get(d, float("inf")))
        route.append(nxt)
        remaining.remove(nxt)
        current = nxt
    route.append(start)
    return tuple(route)


def _route_distance(route: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]) -> float:
    return sum(
        travel_matrix.get(route[i], {}).get(route[i + 1], 0.0) for i in range(len(route) - 1)
    )


def find_optimal_route(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Find a route visiting all destinations and returning to start.

    Small instances (up to `_BRUTE_FORCE_MAX_DESTINATIONS` stops) are solved
    exactly with brute force. Larger instances use a nearest-neighbour
    heuristic, which stays fast even with dozens of stops per engineer.
    (A 2-opt refinement pass was deliberately left out: its standard swap
    formula assumes a symmetric travel matrix, and this codebase's travel
    matrices are not guaranteed symmetric — applying it anyway can make the
    "improvement" check inconsistent with the true reversed-segment cost and
    loop indefinitely.)

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
    if len(destinations) <= _BRUTE_FORCE_MAX_DESTINATIONS:
        return brute_force_tsp(start, destinations, travel_matrix)

    route = _nearest_neighbor_route(start, destinations, travel_matrix)
    return route, _route_distance(route, travel_matrix)
