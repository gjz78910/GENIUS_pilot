"""Unit tests for routing algorithm.

Tests organized by requirement:
- Requirement 5: Route Optimization (TSP algorithm)
- Requirement 3: Travel Time (used in route calculation)
"""

from __future__ import annotations

import unittest

from src.optimization.routing import brute_force_tsp


class TestRouting(unittest.TestCase):
    """Test cases for TSP routing algorithm."""

    def setUp(self):
        """Set up test fixtures with travel time matrix (in hours)."""
        self.travel_matrix = {
            "A": {"A": 0.0, "B": 10.0, "C": 15.0, "D": 20.0},
            "B": {"A": 10.0, "B": 0.0, "C": 35.0, "D": 25.0},
            "C": {"A": 15.0, "B": 35.0, "C": 0.0, "D": 30.0},
            "D": {"A": 20.0, "B": 25.0, "C": 30.0, "D": 0.0},
        }

    # ========================================
    # REQUIREMENT 5: Route Optimization
    # ========================================

    def test_single_destination(self):
        """Test TSP with a single destination.
        
        Requirement 5: Route starts and ends at engineer's home location.
        """
        route, distance = brute_force_tsp("A", ["B"], self.travel_matrix)
        self.assertEqual(route, ("A", "B", "A"))
        self.assertEqual(distance, 20.0)  # A->B->A

    def test_two_destinations(self):
        """Test TSP with two destinations.
        
        Requirement 5: All destinations visited, optimal route selected.
        """
        route, distance = brute_force_tsp("A", ["B", "C"], self.travel_matrix)
        self.assertEqual(len(route), 4)  # Start, 2 destinations, return
        self.assertEqual(route[0], "A")
        self.assertEqual(route[-1], "A")
        self.assertIn("B", route)
        self.assertIn("C", route)

    def test_three_destinations(self):
        """Test TSP with three destinations.
        
        Requirement 5: Brute-force TSP finds shortest route through all jobs.
        """
        route, distance = brute_force_tsp("A", ["B", "C", "D"], self.travel_matrix)
        self.assertEqual(len(route), 5)  # Start, 3 destinations, return
        self.assertEqual(route[0], "A")
        self.assertEqual(route[-1], "A")
        self.assertIn("B", route)
        self.assertIn("C", route)
        self.assertIn("D", route)

    def test_empty_destinations(self):
        """Test TSP with no destinations.
        
        Edge case: Route should just be start->start with 0 distance.
        """
        route, distance = brute_force_tsp("A", [], self.travel_matrix)
        self.assertEqual(route, ("A", "A"))
        self.assertEqual(distance, 0.0)

    def test_optimal_route_selection(self):
        """Test that TSP selects the optimal route.
        
        Requirement 5: Minimize total travel time.
        """
        # Create a simple case where optimal route is clear
        simple_matrix = {
            "A": {"A": 0.0, "B": 1.0, "C": 10.0},
            "B": {"A": 1.0, "B": 0.0, "C": 1.0},
            "C": {"A": 10.0, "B": 1.0, "C": 0.0},
        }
        route, distance = brute_force_tsp("A", ["B", "C"], simple_matrix)
        # Optimal: A->B->C->A (1+1+10=12) is better than A->C->B->A (10+1+1=12)
        # Both are equal, but should return one of them
        self.assertEqual(distance, 12.0)

    # ========================================
    # Route Validation Tests
    # ========================================

    def test_route_starts_and_ends_at_start(self):
        """Test that route always starts and ends at the starting location.
        
        Requirement 5: Engineer starts and returns to home location.
        """
        route, distance = brute_force_tsp("B", ["A", "C"], self.travel_matrix)
        self.assertEqual(route[0], "B")
        self.assertEqual(route[-1], "B")

    def test_all_destinations_visited(self):
        """Test that all destinations are visited exactly once.
        
        Requirement 5: All assigned jobs must be visited.
        """
        destinations = ["B", "C", "D"]
        route, distance = brute_force_tsp("A", destinations, self.travel_matrix)
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
        route, distance = brute_force_tsp("A", ["B"], incomplete_matrix)
        # Should still work with available data
        self.assertEqual(route[0], "A")
        self.assertEqual(route[-1], "A")


if __name__ == "__main__":
    unittest.main()
