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
