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

    O(n²) construction + O(n² × passes) improvement. Used for large n where
    Held-Karp becomes too expensive.
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

    def get_locs() -> List[str]:
        return [start] + [dests[order[k]] for k in range(n)] + [start]

    def tour_cost(locs: List[str]) -> float:
        return sum(d(locs[k], locs[k + 1]) for k in range(len(locs) - 1))

    # --- 2-opt improvement ---
    improved = True
    while improved:
        improved = False
        locs = get_locs()
        for i in range(1, n):
            for j in range(i + 1, n + 1):
                delta = (
                    d(locs[i - 1], locs[j]) + d(locs[i], locs[j + 1])
                    - d(locs[i - 1], locs[i]) - d(locs[j], locs[j + 1])
                )
                if delta < -1e-9:
                    order[i - 1:j] = order[i - 1:j][::-1]
                    improved = True
                    break
            if improved:
                break

    locs = get_locs()
    return tuple(locs), tour_cost(locs)


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
