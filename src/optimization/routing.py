"""Routing functions for field engineer scheduling.

The main entry point is `find_optimal_route`, which returns a route that:
- starts at `start`
- visits each destination once
- returns to `start`
"""

from __future__ import annotations

from typing import Sequence, Tuple, Dict, List


def nearest_neighbour_route(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Build a route greedily: at each step move to the nearest unvisited location."""
    unvisited = list(destinations)
    route = [start]
    total_distance = 0.0
    current = start

    while unvisited:
        nearest = min(
            unvisited,
            key=lambda loc: travel_matrix.get(current, {}).get(loc, float("inf")),
        )
        total_distance += travel_matrix.get(current, {}).get(nearest, 0.0)
        route.append(nearest)
        unvisited.remove(nearest)
        current = nearest

    total_distance += travel_matrix.get(current, {}).get(start, 0.0)
    route.append(start)
    return tuple(route), total_distance


def _route_cost(path: List[str], travel_matrix: Dict[str, Dict[str, float]]) -> float:
    return sum(
        travel_matrix.get(path[k], {}).get(path[k + 1], 0.0)
        for k in range(len(path) - 1)
    )


def or_opt_improve(
    route: Tuple[str, ...], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Improve a route by relocating individual nodes to better positions.

    Or-opt moves each internal node to the position in the route where it reduces
    total cost most. Unlike 2-opt, relocation never reverses edge directions, so
    it is safe for asymmetric travel matrices.
    """
    path = list(route)
    improved = True
    while improved:
        improved = False
        for k in range(1, len(path) - 1):
            node = path[k]
            prev_k = path[k - 1]
            next_k = path[k + 1]

            # Cost saving from removing node at k
            remove_gain = (
                travel_matrix.get(prev_k, {}).get(node, 0.0)
                + travel_matrix.get(node, {}).get(next_k, 0.0)
                - travel_matrix.get(prev_k, {}).get(next_k, 0.0)
            )

            best_delta = 1e-9  # only accept strict improvements
            best_j = None

            for j in range(len(path) - 1):
                if j == k - 1 or j == k:
                    continue  # same position — no change
                a, b = path[j], path[j + 1]
                insert_cost = (
                    travel_matrix.get(a, {}).get(node, 0.0)
                    + travel_matrix.get(node, {}).get(b, 0.0)
                    - travel_matrix.get(a, {}).get(b, 0.0)
                )
                delta = insert_cost - remove_gain
                if delta < -best_delta:
                    best_delta = -delta
                    best_j = j

            if best_j is not None:
                path.pop(k)
                # After pop(k), indices >= k shift down by 1; adjust insertion point
                insert_pos = best_j + 1 if best_j < k else best_j
                path.insert(insert_pos, node)
                improved = True
                break  # restart after each move

    return tuple(path), _route_cost(path, travel_matrix)


def find_optimal_route(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Find a route visiting all destinations and returning to start.

    Uses a nearest-neighbour heuristic seeded into Or-opt local search.
    Or-opt relocates individual nodes, which is safe for asymmetric travel matrices.
    """
    if not destinations:
        return (start, start), 0.0
    route, _ = nearest_neighbour_route(start, destinations, travel_matrix)
    return or_opt_improve(route, travel_matrix)
