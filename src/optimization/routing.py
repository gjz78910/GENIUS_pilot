"""Routing functions for field engineer scheduling.

Overview
--------
Given an engineer's home location and a set of job destinations, find the
shortest round-trip route that visits every destination exactly once.
This is the Travelling Salesperson Problem (TSP).

    Home ──► Job A ──► Job C ──► Job B ──► Home
         2h       1h       3h       2h
                                          total = 8h

The main entry point is `find_optimal_route`, which delegates to a pluggable
routing strategy.

Strategy Pattern
----------------
The module uses a strategy pattern so routing algorithms can be swapped
without changing calling code:

    ┌────────────────────┐
    │  find_optimal_route│  ◄── public entry point
    └────────┬───────────┘
             │ delegates to
             ▼
    ┌────────────────────┐
    │  RoutingStrategy   │  ◄── abstract base class
    └────────┬───────────┘
             │
      ┌──────┴──────────────────────┐
      │                             │
      ▼                             ▼
    ┌──────────────┐   ┌──────────────────────────┐
    │ BruteForce   │   │ NearestNeighborTwoOpt    │  ◄── default
    │ O(n!)        │   │ O(n² · k)                │
    │ exact        │   │ heuristic, near-optimal   │
    └──────────────┘   └──────────────────────────┘

Usage:
    # Default (NN + 2-opt):
    route, dist = find_optimal_route(start, dests, matrix)

    # Explicit brute-force for verification:
    route, dist = find_optimal_route(start, dests, matrix, strategy=BruteForceStrategy())

    # Custom strategy:
    routing.DEFAULT_STRATEGY = MyCustomStrategy()

Implementing a new strategy:
    Subclass `RoutingStrategy` and implement `solve()`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from itertools import permutations
from typing import Dict, Sequence, Tuple


# ---------------------------------------------------------------------------
# Strategy interface
# ---------------------------------------------------------------------------


class RoutingStrategy(ABC):
    """Abstract base class for TSP routing strategies.

    Subclass this and implement `solve()` to create a new routing algorithm.
    The method must return a route that:
    - Starts at `start`
    - Visits each destination exactly once
    - Returns to `start`
    """

    @abstractmethod
    def solve(
        self,
        start: str,
        destinations: Sequence[str],
        travel_matrix: Dict[str, Dict[str, float]],
    ) -> Tuple[Tuple[str, ...], float]:
        """Find a route visiting all destinations and returning to start.

        Parameters
        ----------
        start : str
            The starting (and ending) location.
        destinations : Sequence[str]
            Locations that must be visited exactly once.
        travel_matrix : Dict[str, Dict[str, float]]
            Travel distances between locations.

        Returns
        -------
        Tuple[Tuple[str, ...], float]
            (route, total_distance) where route is a tuple of location
            strings including start at the beginning and end.
        """
        ...


# ---------------------------------------------------------------------------
# Brute-force strategy (exact, O(n!))
# ---------------------------------------------------------------------------


class BruteForceStrategy(RoutingStrategy):
    """Solve TSP by evaluating all permutations.

    Guarantees the optimal solution but has factorial time complexity.
    Only feasible for small numbers of destinations.

    Complexity
    ----------
    Time:  O(n!)  where n = number of destinations
    Space: O(n)

    Feasibility by destination count:
        n=5  →       120 permutations  (instant)
        n=8  →    40,320 permutations  (~40ms)
        n=10 → 3,628,800 permutations  (~2s)
        n=12 → 479,001,600 perms       (~5 minutes)
        n=15 → 1.3 trillion perms      (infeasible)

    Example
    -------
    Destinations: [B, C, D], start: A

    Evaluates all orderings:
        A → B → C → D → A  = 2 + 3 + 4 + 5 = 14
        A → B → D → C → A  = 2 + 6 + 4 + 3 = 15
        A → C → B → D → A  = 3 + 3 + 6 + 5 = 17
        A → C → D → B → A  = 3 + 4 + 6 + 2 = 15
        A → D → B → C → A  = 5 + 6 + 3 + 3 = 17
        A → D → C → B → A  = 5 + 4 + 3 + 2 = 14  ◄── tied best
                                                ▲
    Returns first found best: (A, B, C, D, A), distance=14
    """

    def solve(
        self,
        start: str,
        destinations: Sequence[str],
        travel_matrix: Dict[str, Dict[str, float]],
    ) -> Tuple[Tuple[str, ...], float]:
        if not destinations:
            return (start, start), 0.0

        best_distance: float = float("inf")
        best_route: Tuple[str, ...] | None = None

        for perm in permutations(destinations):
            distance: float = 0.0
            current = start
            for loc in perm:
                distance += travel_matrix[current][loc]
                current = loc
            distance += travel_matrix[current][start]

            if distance < best_distance:
                best_distance = distance
                best_route = (start,) + perm + (start,)

        assert best_route is not None
        return best_route, best_distance


# ---------------------------------------------------------------------------
# Nearest Neighbor + 2-opt strategy (heuristic, fast)
# ---------------------------------------------------------------------------


class NearestNeighborTwoOptStrategy(RoutingStrategy):
    """Nearest-neighbor construction followed by 2-opt local improvement.

    Two-phase approach:

    Phase 1: Nearest Neighbor Construction — O(n²)
    -----------------------------------------------
    Builds an initial route by always visiting the closest unvisited
    destination. Fast but can produce suboptimal routes.

        Start at Home, pick closest unvisited each step:

        Home ─(1)─► B ─(2)─► D ─(5)─► C ─(4)─► Home  = 12
                ▲
                └── B is closest to Home

    Phase 2: 2-opt Improvement — O(n² · k iterations)
    ---------------------------------------------------
    Iteratively improves the route by reversing segments that reduce
    the total distance. Continues until no improving swap exists.

    How 2-opt works:

        Before (crossing edges):       After (uncrossed):

        A ──────► B                    A ──────► C
                   ╲  ╱                           │
                    ╳                             │
                   ╱  ╲                           │
        C ◄────── D                    B ◄────── D

        Route: ...A → B → C → D...    Route: ...A → C → B → D...
                         ▲ reversed segment

        If dist(A,C) + dist(B,D) < dist(A,B) + dist(C,D):
            Reverse the segment [B..C] → yields [C..B]

    Typical quality: within 5-10% of optimal for random instances.

    Complexity
    ----------
    Time:  O(n²) construction + O(n² · k) improvement
           where k = number of improvement rounds (usually small)
    Space: O(n)

    Example with 10 destinations:
        Brute force:  3,628,800 permutations → ~2 seconds
        NN + 2-opt:   ~100 distance evaluations → ~0.05ms
    """

    def solve(
        self,
        start: str,
        destinations: Sequence[str],
        travel_matrix: Dict[str, Dict[str, float]],
    ) -> Tuple[Tuple[str, ...], float]:
        if not destinations:
            return (start, start), 0.0

        # Phase 1: build initial route via nearest-neighbor
        route = self._nearest_neighbor(start, destinations, travel_matrix)

        # Phase 2: improve route via 2-opt swaps
        route = self._two_opt(route, travel_matrix)

        total_distance = self._route_distance(route, travel_matrix)
        return tuple(route), total_distance

    def _nearest_neighbor(
        self,
        start: str,
        destinations: Sequence[str],
        travel_matrix: Dict[str, Dict[str, float]],
    ) -> list[str]:
        """Build initial route using nearest-neighbor heuristic.

        Algorithm:
            1. Start at home location
            2. Find the closest unvisited destination
            3. Move there, mark as visited
            4. Repeat until all destinations visited
            5. Return to start

            Step 1    Step 2    Step 3    Step 4
            H         H         H         H
            │         │╲        │╲        │╲
            ▼         ▼  ╲      ▼  ╲      ▼  ╲
            B(1)      B───►D    B───►D    B───►D
                              ╲         │         │
                               C        ▼         ▼
                                        C───────► H
        """
        unvisited = list(destinations)
        route = [start]
        current = start

        while unvisited:
            nearest = min(unvisited, key=lambda loc: travel_matrix[current][loc])
            route.append(nearest)
            unvisited.remove(nearest)
            current = nearest

        route.append(start)  # return to start
        return route

    def _two_opt(
        self,
        route: list[str],
        travel_matrix: Dict[str, Dict[str, float]],
    ) -> list[str]:
        """Improve route by reversing sub-tours that reduce total distance.

        For each pair of edges (i-1, i) and (j, j+1), check if reversing
        the segment between i and j produces a shorter route:

            Index:    0    1    2    3    4    5
            Route:  [ H ][ A ][ B ][ C ][ D ][ H ]
                          ▲i             ▲j

            Current edges: H→A (cost 5) + D→H (cost 4) = 9
            New edges:     H→D (cost 2) + A→H (cost 5) = 7  ◄── better!

            Reverse segment [A, B, C, D] → [D, C, B, A]:
            New route:  [ H ][ D ][ C ][ B ][ A ][ H ]

        Repeats until no improving swap is found (local optimum).
        """
        n = len(route)
        improved = True

        while improved:
            improved = False
            for i in range(1, n - 2):
                for j in range(i + 1, n - 1):
                    # Cost of current edges: (i-1)→(i) and (j)→(j+1)
                    d_current = (
                        travel_matrix[route[i - 1]][route[i]]
                        + travel_matrix[route[j]][route[j + 1]]
                    )
                    # Cost after reversing segment [i..j]
                    d_new = (
                        travel_matrix[route[i - 1]][route[j]]
                        + travel_matrix[route[i]][route[j + 1]]
                    )
                    if d_new < d_current:
                        route[i : j + 1] = reversed(route[i : j + 1])
                        improved = True

        return route

    def _route_distance(
        self, route: list[str], travel_matrix: Dict[str, Dict[str, float]]
    ) -> float:
        """Calculate total distance of a complete route.

        Route: [H, A, B, C, H]
        Distance = dist(H,A) + dist(A,B) + dist(B,C) + dist(C,H)
        """
        return sum(
            travel_matrix[route[i]][route[i + 1]] for i in range(len(route) - 1)
        )


# ---------------------------------------------------------------------------
# Module default and public entry point
# ---------------------------------------------------------------------------

DEFAULT_STRATEGY: RoutingStrategy = NearestNeighborTwoOptStrategy()


def find_optimal_route(
    start: str,
    destinations: Sequence[str],
    travel_matrix: Dict[str, Dict[str, float]],
    strategy: RoutingStrategy | None = None,
) -> Tuple[Tuple[str, ...], float]:
    """Find a route visiting all destinations and returning to start.

    This is the public entry point for routing. It delegates to the
    configured strategy (default: nearest-neighbor + 2-opt).

    Parameters
    ----------
    start : str
        The starting (and ending) location for the route.
    destinations : Sequence[str]
        A sequence of destination locations that must be visited exactly once.
    travel_matrix : Dict[str, Dict[str, float]]
        A dictionary representing the travel distance between locations.
    strategy : RoutingStrategy | None
        The routing strategy to use. Defaults to `DEFAULT_STRATEGY`.

    Returns
    -------
    Tuple[Tuple[str, ...], float]
        A tuple containing the route (including start at the beginning
        and end) and its total distance.

    Examples
    --------
    >>> matrix = {"A": {"A": 0, "B": 1, "C": 3}, "B": {"A": 1, "B": 0, "C": 1}, "C": {"A": 3, "B": 1, "C": 0}}
    >>> find_optimal_route("A", ["B", "C"], matrix)
    (('A', 'B', 'C', 'A'), 5)
    """
    if strategy is None:
        strategy = DEFAULT_STRATEGY
    return strategy.solve(start, destinations, travel_matrix)


# ---------------------------------------------------------------------------
# Legacy alias for backwards compatibility
# ---------------------------------------------------------------------------


def brute_force_tsp(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Solve TSP using brute force. Kept for backwards compatibility."""
    return BruteForceStrategy().solve(start, destinations, travel_matrix)
