"""Routing functions for field engineer scheduling using Nearest Neighbor heuristic.

The main entry point is `find_optimal_route`, which returns a route that:
- starts at `start`
- visits each destination once
- returns to `start`

This module is a faster alternative to routing.py. Instead of brute-forcing all
permutations (O(n!)), it uses the Nearest Neighbor greedy heuristic which runs
in O(n²) time — making it practical for much larger sets of destinations.

Trade-off: The solution is not guaranteed to be globally optimal, but in practice
it typically produces routes within 20-25% of the true optimum. For field engineer
scheduling with moderate numbers of jobs, this is usually acceptable.
"""

from __future__ import annotations

from typing import Sequence, Tuple, Dict


def nearest_neighbor_tsp(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Solve a travelling-salesperson problem using the Nearest Neighbor heuristic.

    Algorithm overview:
    1. Begin at the start location.
    2. From the current location, move to the nearest unvisited destination.
    3. Repeat step 2 until all destinations have been visited.
    4. Return to the start location to complete the round trip.

    This greedy approach builds the route incrementally by always choosing
    the locally shortest next step. It does not backtrack or reconsider
    earlier decisions, which is why it is fast but not necessarily optimal.

    Parameters
    ----------
    start : str
        The starting (and ending) location for the route.
    destinations : Sequence[str]
        A sequence of destination locations that must be visited exactly once.
    travel_matrix : Dict[str, Dict[str, float]]
        A dictionary representing the travel distance between locations.
        travel_matrix[A][B] gives the distance from location A to location B.

    Returns
    -------
    Tuple[Tuple[str, ...], float]
        A tuple containing:
        - The route as a tuple of location strings (starting and ending with `start`).
        - The total distance of that route.
    """
    # If there are no destinations, return a trivial route with zero cost.
    # This matches the behaviour of the brute-force implementation.
    if not destinations:
        return (start, start), 0.0

    # Track which destinations have not yet been added to the route.
    # We use a set for O(1) membership checks and removal.
    unvisited = set(destinations)

    # Initialise the route with the starting location.
    route = [start]

    # Keep a running total of the distance travelled.
    total_distance: float = 0.0

    # The current position begins at the start location.
    current = start

    # Main loop: greedily pick the nearest unvisited destination at each step.
    while unvisited:
        # Find the nearest unvisited destination from the current location.
        # We iterate through all remaining unvisited locations and keep track
        # of the one with the smallest travel distance from `current`.
        nearest: str | None = None
        nearest_distance: float = float("inf")

        for candidate in unvisited:
            # Look up the distance from current location to this candidate.
            dist = travel_matrix[current][candidate]

            # If this candidate is closer than anything we've seen so far,
            # update our best choice.
            if dist < nearest_distance:
                nearest = candidate
                nearest_distance = dist

        # At this point `nearest` is guaranteed to be set because `unvisited`
        # is non-empty (loop guard), so assert for the type checker.
        assert nearest is not None

        # Move to the nearest destination:
        # - Add the travel distance to our running total.
        # - Append the destination to the route.
        # - Remove it from the unvisited set.
        # - Update our current position.
        total_distance += nearest_distance
        route.append(nearest)
        unvisited.remove(nearest)
        current = nearest

    # After visiting all destinations, return to the start to complete the
    # round trip (this is a requirement of the TSP formulation).
    total_distance += travel_matrix[current][start]
    route.append(start)

    # Convert the route list to a tuple for immutability (matches the
    # interface of the brute-force implementation).
    return tuple(route), total_distance


def find_optimal_route(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Find a route visiting all destinations and returning to start.

    This is the public entry point, mirroring the interface in routing.py.
    It delegates to the Nearest Neighbor heuristic for fast approximate
    solutions.

    Parameters
    ----------
    start : str
        The starting (and ending) location for the route.
    destinations : Sequence[str]
        A sequence of destination locations that must be visited exactly once.
    travel_matrix : Dict[str, Dict[str, float]]
        A dictionary representing the travel distance between locations.
        travel_matrix[A][B] gives the distance from location A to location B.

    Returns
    -------
    Tuple[Tuple[str, ...], float]
        A tuple containing the route (including start at the beginning
        and end) and its total distance.
    """
    return nearest_neighbor_tsp(start, destinations, travel_matrix)
