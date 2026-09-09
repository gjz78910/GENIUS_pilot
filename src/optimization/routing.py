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


def held_karp_tsp(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Solve TSP using the Held-Karp dynamic programming algorithm.

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

    dests = list(destinations)
    n = len(dests)
    INF = float("inf")

    # dp[(mask, k)] = min cost to reach dests[k] from start visiting exactly
    # the nodes encoded in mask (bit i set means dests[i] has been visited).
    dp: Dict[Tuple[int, int], float] = {}
    # parent[(mask, k)] = index m of the node visited just before dests[k]
    parent: Dict[Tuple[int, int], int] = {}

    # Base case: single-node subsets — travel directly from start
    for k in range(n):
        dp[(1 << k, k)] = travel_matrix[start][dests[k]]

    # Build up solutions for subsets of increasing size
    for size in range(2, n + 1):
        for mask in range(1, 1 << n):
            if bin(mask).count("1") != size:
                continue
            for k in range(n):
                if not (mask >> k & 1):
                    continue
                prev_mask = mask ^ (1 << k)
                best = INF
                best_m = -1
                for m in range(n):
                    if not (prev_mask >> m & 1):
                        continue
                    cost = dp.get((prev_mask, m), INF) + travel_matrix[dests[m]][dests[k]]
                    if cost < best:
                        best = cost
                        best_m = m
                dp[(mask, k)] = best
                parent[(mask, k)] = best_m

    # Find the minimum-cost last node before returning to start
    full_mask = (1 << n) - 1
    opt = INF
    last = -1
    for k in range(n):
        cost = dp.get((full_mask, k), INF) + travel_matrix[dests[k]][start]
        if cost < opt:
            opt = cost
            last = k

    # Reconstruct the path by following parent pointers backwards
    path = []
    mask = full_mask
    k = last
    while True:
        path.append(dests[k])
        if bin(mask).count("1") == 1:
            break
        prev_k = parent[(mask, k)]
        mask ^= (1 << k)
        k = prev_k

    path.reverse()
    return (start,) + tuple(path) + (start,), opt


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
    return held_karp_tsp(start, destinations, travel_matrix)
