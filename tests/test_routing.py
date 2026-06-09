"""Unit tests for routing algorithm.

Tests verify the behaviour of the route optimisation entry point
(`find_optimal_route`).  The tests are algorithm-agnostic: they check
correctness of results, not which algorithm is used internally.
"""

from __future__ import annotations

import unittest

from src.optimization.routing import find_optimal_route


class TestRouting(unittest.TestCase):
    """Test cases for route optimisation."""

    def setUp(self):
        """Set up test fixtures with travel time matrix (in hours)."""
        self.travel_matrix = {
            "A": {"A": 0.0, "B": 10.0, "C": 15.0, "D": 20.0},
            "B": {"A": 10.0, "B": 0.0, "C": 35.0, "D": 25.0},
            "C": {"A": 15.0, "B": 35.0, "C": 0.0, "D": 30.0},
            "D": {"A": 20.0, "B": 25.0, "C": 30.0, "D": 0.0},
        }

    # ========================================
    # Route Optimization
    # ========================================

    def test_single_destination(self):
        """Test routing with a single destination.

        Route starts and ends at engineer's home location.
        """
        route, distance = find_optimal_route("A", ["B"], self.travel_matrix)
        self.assertEqual(route, ("A", "B", "A"))
        self.assertEqual(distance, 20.0)  # A->B->A

    def test_two_destinations(self):
        """Test routing with two destinations.

        All destinations visited, optimal route selected.
        """
        route, distance = find_optimal_route("A", ["B", "C"], self.travel_matrix)
        self.assertEqual(len(route), 4)  # Start, 2 destinations, return
        self.assertEqual(route[0], "A")
        self.assertEqual(route[-1], "A")
        self.assertIn("B", route)
        self.assertIn("C", route)

    def test_three_destinations(self):
        """Test routing with three destinations.

        Finds shortest route through all jobs.
        """
        route, distance = find_optimal_route("A", ["B", "C", "D"], self.travel_matrix)
        self.assertEqual(len(route), 5)  # Start, 3 destinations, return
        self.assertEqual(route[0], "A")
        self.assertEqual(route[-1], "A")
        self.assertIn("B", route)
        self.assertIn("C", route)
        self.assertIn("D", route)

    def test_empty_destinations(self):
        """Test routing with no destinations.

        Edge case: Route should just be start->start with 0 distance.
        """
        route, distance = find_optimal_route("A", [], self.travel_matrix)
        self.assertEqual(route, ("A", "A"))
        self.assertEqual(distance, 0.0)

    def test_optimal_route_selection(self):
        """Test that routing selects the optimal route.

        Minimize total travel time.
        """
        # Create a simple case where optimal route is clear
        simple_matrix = {
            "A": {"A": 0.0, "B": 1.0, "C": 10.0},
            "B": {"A": 1.0, "B": 0.0, "C": 1.0},
            "C": {"A": 10.0, "B": 1.0, "C": 0.0},
        }
        route, distance = find_optimal_route("A", ["B", "C"], simple_matrix)
        # Optimal: A->B->C->A (1+1+10=12) is better than A->C->B->A (10+1+1=12)
        # Both are equal, but should return one of them
        self.assertEqual(distance, 12.0)

    # ========================================
    # Route Validation Tests
    # ========================================

    def test_route_starts_and_ends_at_start(self):
        """Test that route always starts and ends at the starting location.

        Engineer starts and returns to home location.
        """
        route, distance = find_optimal_route("B", ["A", "C"], self.travel_matrix)
        self.assertEqual(route[0], "B")
        self.assertEqual(route[-1], "B")

    def test_all_destinations_visited(self):
        """Test that all destinations are visited exactly once.

        All assigned jobs must be visited.
        """
        destinations = ["B", "C", "D"]
        route, distance = find_optimal_route("A", destinations, self.travel_matrix)
        route_list = list(route)
        for dest in destinations:
            self.assertEqual(route_list.count(dest), 1)

    # ========================================
    # Edge Cases
    # ========================================

    def test_missing_travel_matrix_entry(self):
        """Test behavior with missing travel matrix entries.

        Edge case: Should handle incomplete travel matrices gracefully.
        """
        incomplete_matrix = {
            "A": {"A": 0.0, "B": 10.0},
            "B": {"A": 10.0, "B": 0.0},
        }
        route, distance = find_optimal_route("A", ["B"], incomplete_matrix)
        # Should still work with available data
        self.assertEqual(route[0], "A")
        self.assertEqual(route[-1], "A")


if __name__ == "__main__":
    unittest.main()


class TestCalculateRouteDistance(unittest.TestCase):
    """Unit tests for the _calculate_route_distance helper."""

    def setUp(self):
        """Set up a symmetric travel matrix for testing."""
        from src.optimization.routing import _calculate_route_distance

        self.calc = _calculate_route_distance
        self.travel_matrix = {
            "A": {"A": 0.0, "B": 10.0, "C": 15.0, "D": 20.0},
            "B": {"A": 10.0, "B": 0.0, "C": 35.0, "D": 25.0},
            "C": {"A": 15.0, "B": 35.0, "C": 0.0, "D": 30.0},
            "D": {"A": 20.0, "B": 25.0, "C": 30.0, "D": 0.0},
        }

    def test_known_route_distance(self):
        """Test distance calculation with a known route."""
        # A->B->C->A = 10 + 35 + 15 = 60
        route = ("A", "B", "C", "A")
        self.assertEqual(self.calc(route, self.travel_matrix), 60.0)

    def test_different_route_order(self):
        """Test that route order affects distance."""
        # A->C->B->A = 15 + 35 + 10 = 60
        route = ("A", "C", "B", "A")
        self.assertEqual(self.calc(route, self.travel_matrix), 60.0)

        # A->B->D->A = 10 + 25 + 20 = 55
        route = ("A", "B", "D", "A")
        self.assertEqual(self.calc(route, self.travel_matrix), 55.0)

    def test_trivial_route_returns_zero(self):
        """Test that a trivial route (start, start) returns 0.0."""
        route = ("A", "A")
        self.assertEqual(self.calc(route, self.travel_matrix), 0.0)

    def test_single_destination_round_trip(self):
        """Test distance for a single-destination round trip."""
        # A->B->A = 10 + 10 = 20
        route = ("A", "B", "A")
        self.assertEqual(self.calc(route, self.travel_matrix), 20.0)

    def test_asymmetric_matrix(self):
        """Test with an asymmetric travel matrix where A->B != B->A."""
        asymmetric_matrix = {
            "X": {"X": 0.0, "Y": 3.0, "Z": 7.0},
            "Y": {"X": 5.0, "Y": 0.0, "Z": 2.0},
            "Z": {"X": 4.0, "Y": 6.0, "Z": 0.0},
        }
        # X->Y->Z->X = 3 + 2 + 4 = 9
        route = ("X", "Y", "Z", "X")
        self.assertEqual(self.calc(route, asymmetric_matrix), 9.0)

        # X->Z->Y->X = 7 + 6 + 5 = 18
        route = ("X", "Z", "Y", "X")
        self.assertEqual(self.calc(route, asymmetric_matrix), 18.0)

    def test_result_is_non_negative(self):
        """Test that the result is always non-negative for valid matrices."""
        route = ("A", "B", "C", "D", "A")
        distance = self.calc(route, self.travel_matrix)
        self.assertGreaterEqual(distance, 0.0)

    def test_full_tour_distance(self):
        """Test distance for a complete tour visiting all nodes."""
        # A->B->C->D->A = 10 + 35 + 30 + 20 = 95
        route = ("A", "B", "C", "D", "A")
        self.assertEqual(self.calc(route, self.travel_matrix), 95.0)


class TestNearestNeighborTSP(unittest.TestCase):
    """Unit and property tests for the nearest_neighbor_tsp function."""

    def setUp(self):
        """Set up test fixtures."""
        from src.optimization.routing import nearest_neighbor_tsp, _calculate_route_distance

        self.nn_tsp = nearest_neighbor_tsp
        self.calc_dist = _calculate_route_distance

        # Symmetric matrix
        self.travel_matrix = {
            "A": {"A": 0.0, "B": 10.0, "C": 15.0, "D": 20.0},
            "B": {"A": 10.0, "B": 0.0, "C": 35.0, "D": 25.0},
            "C": {"A": 15.0, "B": 35.0, "C": 0.0, "D": 30.0},
            "D": {"A": 20.0, "B": 25.0, "C": 30.0, "D": 0.0},
        }

        # Asymmetric matrix
        self.asymmetric_matrix = {
            "X": {"X": 0.0, "Y": 3.0, "Z": 7.0, "W": 12.0},
            "Y": {"X": 5.0, "Y": 0.0, "Z": 2.0, "W": 8.0},
            "Z": {"X": 4.0, "Y": 6.0, "Z": 0.0, "W": 1.0},
            "W": {"X": 9.0, "Y": 11.0, "Z": 3.0, "W": 0.0},
        }

    # ========================================
    # Route Completeness (Property 1)
    # ========================================

    def test_visits_all_destinations_exactly_once(self):
        """Every destination appears exactly once in route[1:-1]."""
        destinations = ["B", "C", "D"]
        route, _ = self.nn_tsp("A", destinations, self.travel_matrix)
        interior = list(route[1:-1])
        self.assertEqual(sorted(interior), sorted(destinations))

    def test_visits_all_destinations_asymmetric(self):
        """Route completeness holds for asymmetric matrices."""
        destinations = ["Y", "Z", "W"]
        route, _ = self.nn_tsp("X", destinations, self.asymmetric_matrix)
        interior = list(route[1:-1])
        self.assertEqual(sorted(interior), sorted(destinations))

    def test_single_destination(self):
        """Single destination produces a valid round trip."""
        route, distance = self.nn_tsp("A", ["B"], self.travel_matrix)
        self.assertEqual(route, ("A", "B", "A"))
        self.assertEqual(distance, 20.0)

    def test_route_length(self):
        """Route has exactly len(destinations) + 2 elements."""
        destinations = ["B", "C", "D"]
        route, _ = self.nn_tsp("A", destinations, self.travel_matrix)
        self.assertEqual(len(route), len(destinations) + 2)

    # ========================================
    # Route Circularity (Property 2)
    # ========================================

    def test_starts_and_ends_at_start(self):
        """Route starts and ends at the given start location."""
        route, _ = self.nn_tsp("A", ["B", "C", "D"], self.travel_matrix)
        self.assertEqual(route[0], "A")
        self.assertEqual(route[-1], "A")

    def test_different_start_location(self):
        """Route circularity holds regardless of start location."""
        route, _ = self.nn_tsp("C", ["A", "B", "D"], self.travel_matrix)
        self.assertEqual(route[0], "C")
        self.assertEqual(route[-1], "C")

    # ========================================
    # Distance Accuracy (Property 3)
    # ========================================

    def test_reported_distance_matches_calculation(self):
        """Returned distance matches sum of consecutive edge weights."""
        route, distance = self.nn_tsp("A", ["B", "C", "D"], self.travel_matrix)
        expected = self.calc_dist(route, self.travel_matrix)
        self.assertAlmostEqual(distance, expected)

    def test_distance_matches_for_asymmetric_matrix(self):
        """Distance accuracy holds for asymmetric matrices."""
        route, distance = self.nn_tsp("X", ["Y", "Z", "W"], self.asymmetric_matrix)
        expected = self.calc_dist(route, self.asymmetric_matrix)
        self.assertAlmostEqual(distance, expected)

    # ========================================
    # Greedy Selection (Property 7)
    # ========================================

    def test_greedy_selects_nearest_unvisited(self):
        """Each step picks the closest unvisited destination.

        From A: closest is B (10), then from B: closest unvisited is D (25),
        then from D: closest unvisited is C (30). Route: A->B->D->C->A.
        """
        route, _ = self.nn_tsp("A", ["B", "C", "D"], self.travel_matrix)
        # From A: B=10, C=15, D=20 -> picks B
        self.assertEqual(route[1], "B")
        # From B: C=35, D=25 -> picks D
        self.assertEqual(route[2], "D")
        # From D: C=30 -> picks C (only one left)
        self.assertEqual(route[3], "C")

    def test_greedy_selection_asymmetric(self):
        """Greedy selection verified on asymmetric matrix.

        From X: Y=3, Z=7, W=12 -> picks Y
        From Y: Z=2, W=8 -> picks Z
        From Z: W=1 -> picks W
        Route: X->Y->Z->W->X
        """
        route, _ = self.nn_tsp("X", ["Y", "Z", "W"], self.asymmetric_matrix)
        self.assertEqual(route[1], "Y")
        self.assertEqual(route[2], "Z")
        self.assertEqual(route[3], "W")

    # ========================================
    # Property Tests with Randomized Inputs
    # ========================================

    def _generate_random_matrix(self, locations, seed=42):
        """Helper to generate a random travel matrix."""
        import random

        rng = random.Random(seed)
        matrix = {}
        for a in locations:
            matrix[a] = {}
            for b in locations:
                if a == b:
                    matrix[a][b] = 0.0
                else:
                    matrix[a][b] = rng.uniform(1.0, 100.0)
        return matrix

    def test_property_completeness_random(self):
        """Property: all destinations visited for random inputs."""
        locations = [f"L{i}" for i in range(10)]
        matrix = self._generate_random_matrix(locations)
        start = "L0"
        destinations = locations[1:]

        route, _ = self.nn_tsp(start, destinations, matrix)
        self.assertEqual(sorted(route[1:-1]), sorted(destinations))

    def test_property_circularity_random(self):
        """Property: route starts/ends at start for random inputs."""
        locations = [f"L{i}" for i in range(10)]
        matrix = self._generate_random_matrix(locations)
        start = "L0"
        destinations = locations[1:]

        route, _ = self.nn_tsp(start, destinations, matrix)
        self.assertEqual(route[0], start)
        self.assertEqual(route[-1], start)

    def test_property_distance_accuracy_random(self):
        """Property: reported distance matches edge sum for random inputs."""
        locations = [f"L{i}" for i in range(10)]
        matrix = self._generate_random_matrix(locations)
        start = "L0"
        destinations = locations[1:]

        route, distance = self.nn_tsp(start, destinations, matrix)
        expected = self.calc_dist(route, matrix)
        self.assertAlmostEqual(distance, expected)

    def test_property_greedy_selection_random(self):
        """Property: each step selects the nearest unvisited destination."""
        locations = [f"L{i}" for i in range(8)]
        matrix = self._generate_random_matrix(locations, seed=99)
        start = "L0"
        destinations = locations[1:]

        route, _ = self.nn_tsp(start, destinations, matrix)

        # Replay the greedy logic and verify route matches
        unvisited = set(destinations)
        current = start
        for step in range(1, len(route) - 1):
            # Find what nearest-neighbor should have picked
            nearest = min(unvisited, key=lambda loc: matrix[current][loc])
            self.assertEqual(route[step], nearest,
                             f"At step {step}, expected {nearest} but got {route[step]}")
            unvisited.remove(nearest)
            current = nearest
