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


def _nearest_neighbor_2opt(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Nearest-neighbour construction followed by 2-opt improvement.

    Uses full cost recomputation (not the delta shortcut) so that it is
    correct for asymmetric travel matrices where d(A,B) != d(B,A).
    """
    dests: List[str] = list(destinations)
    n = len(dests)

    # --- nearest-neighbour greedy construction ---
    unvisited: set[int] = set(range(n))
    cur = start
    order: List[int] = []
    while unvisited:
        best = min(unvisited, key=lambda i: travel_matrix.get(cur, {}).get(dests[i], float("inf")))
        order.append(best)
        unvisited.discard(best)
        cur = dests[best]

    def d(a: str, b: str) -> float:
        return travel_matrix.get(a, {}).get(b, float("inf"))

    def locs_from(ord_: List[int]) -> List[str]:
        return [start] + [dests[ord_[k]] for k in range(n)] + [start]

    def tour_cost(locs: List[str]) -> float:
        return sum(d(locs[k], locs[k + 1]) for k in range(n + 1))

    current_cost = tour_cost(locs_from(order))

    # --- 2-opt improvement: full cost comparison, correct for asymmetric TSP ---
    improved = True
    while improved:
        improved = False
        for i in range(n - 1):
            for j in range(i + 2, n + 1):
                new_order = order[:i] + order[i:j][::-1] + order[j:]
                new_cost = tour_cost(locs_from(new_order))
                if new_cost < current_cost - 1e-9:
                    order = new_order
                    current_cost = new_cost
                    improved = True
                    break
            if improved:
                break

    return tuple(locs_from(order)), current_cost


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

    dests = list(destinations)
    n = len(dests)

    if n <= 6:
        return brute_force_tsp(start, destinations, travel_matrix)

    # For n > 6, Held-Karp grows as O(n² × 2^n) which becomes prohibitive when
    # routing hundreds of engineers each with 10-20 jobs. nn+2opt is O(n²) per
    # pass and finds near-optimal routes in microseconds.
    return _nearest_neighbor_2opt(start, destinations, travel_matrix)
