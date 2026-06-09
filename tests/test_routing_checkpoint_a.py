"""Checkpoint A specific routing test.

This test is intentionally stricter than the general routing correctness tests.
It validates route correctness and enforces a runtime target so the baseline
brute-force implementation does not pass unchanged.
"""

from __future__ import annotations

import time
import unittest

from src.optimization.new_alg_route import find_optimal_route


class TestRoutingCheckpointA(unittest.TestCase):
    """Routing-only gate for Task 1 Checkpoint A."""

    def setUp(self):
        # Deterministic 11-location matrix (start + 10 destinations)
        self.locations = [f"L{i}" for i in range(11)]
        self.travel_matrix = {
            src: {
                dst: 0.0 if src == dst else float(((i + j) % 9) + 1)
                for j, dst in enumerate(self.locations)
            }
            for i, src in enumerate(self.locations)
        }

    def test_route_valid_and_fast_for_10_destinations(self):
        start = "L0"
        destinations = self.locations[1:]

        t0 = time.perf_counter()
        route, _ = find_optimal_route(start, destinations, self.travel_matrix)
        elapsed = time.perf_counter() - t0

        # Correctness checks
        self.assertEqual(route[0], start)
        self.assertEqual(route[-1], start)
        for dest in destinations:
            self.assertEqual(route.count(dest), 1)

        # Checkpoint A performance gate: baseline brute-force should fail this.
        if elapsed >= 0.25:
            self.fail(
                f"Routing is too slow: Routing took {elapsed:.3f}s. "
                "Target for Checkpoint A is < 0.25s."
            )


if __name__ == "__main__":
    unittest.main()
