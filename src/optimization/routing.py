"""Routing functions for field engineer scheduling.

The main entry point is `find_optimal_route`, which returns a route that:
- starts at `start`
- visits each destination once
- returns to `start`
"""

from __future__ import annotations

import heapq
from itertools import permutations
from typing import FrozenSet, Sequence, Tuple, Dict


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


def astar_tsp(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Solve a travelling‑salesperson problem using A* search.

    Uses an admissible heuristic (sum of minimum incoming edges for all nodes
    still to be visited) to prune the search space.  Finds the same optimal
    solution as brute force but typically explores far fewer states when some
    routes are clearly cheaper than others.

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

    all_nodes: list[str] = [start] + list(destinations)

    # Precompute the minimum incoming edge weight for each node once.
    # Used by the admissible heuristic: every node must be entered exactly once,
    # so summing these minimums is a valid lower bound on remaining tour cost.
    min_incoming: dict[str, float] = {
        dst: min(
            (travel_matrix[src][dst] for src in all_nodes if src != dst),
            default=0.0,
        )
        for dst in all_nodes
    }

    def heuristic(unvisited: FrozenSet[str]) -> float:
        return sum(min_incoming[node] for node in unvisited) + min_incoming[start]

    unvisited_initial: FrozenSet[str] = frozenset(destinations)

    # Heap entries: (f_cost, counter, g_cost, current, unvisited, path)
    # The counter breaks ties so frozensets are never compared directly.
    counter = 0
    heap: list = [
        (heuristic(unvisited_initial), counter, 0.0, start, unvisited_initial, (start,))
    ]
    # Best g-cost seen for each (current, unvisited) state.
    best_g: dict[tuple[str, FrozenSet[str]], float] = {}

    while heap:
        f, _, g, current, unvisited, path = heapq.heappop(heap)

        state = (current, unvisited)
        if best_g.get(state, float("inf")) < g:
            continue
        best_g[state] = g

        if not unvisited:
            return path + (start,), g + travel_matrix[current][start]

        for nxt in unvisited:
            new_g = g + travel_matrix[current][nxt]
            new_unvisited = unvisited - {nxt}
            new_state = (nxt, new_unvisited)
            if new_g < best_g.get(new_state, float("inf")):
                counter += 1
                heapq.heappush(
                    heap,
                    (new_g + heuristic(new_unvisited), counter, new_g, nxt, new_unvisited, path + (nxt,)),
                )

    raise ValueError("No route found — travel_matrix may be incomplete.")


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
    """return brute_force_tsp(start, destinations, travel_matrix)"""
    return astar_tsp(start, destinations, travel_matrix)
