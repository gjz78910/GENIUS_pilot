"""Use-case tests covering routing quality, matching order-independence,
and workload balance.

These tests address gaps not covered by the existing test suite:
1. No routing quality test for medium-sized inputs (12+ destinations)
2. No matching order-independence test (shuffled job input)
3. No workload balance test for equally-qualified engineers

Each test is written from a use-case perspective, asserting only
observable behavior without depending on implementation details.
"""

from __future__ import annotations

import random
import unittest

from src.optimization.routing import find_optimal_route
from src.optimization.matching import assign_jobs
from src.models.engineer import Engineer
from src.models.job import Job


class TestUseCases(unittest.TestCase):
    """New use-case tests that fill coverage gaps in the existing suite."""

    # ================================================================
    # Gap 1: Routing quality for medium-sized inputs
    # ================================================================

    def test_routing_quality_within_reasonable_factor_of_optimal(self):
        """A 12-destination route should be within 2x of the known optimal.

        Use case: a dispatcher plans a route through 12 job sites arranged
        in a ring. The system should produce a route whose total distance
        is no worse than twice the shortest possible tour.

        Setup
        -----
        13 locations (start "S" + 12 destinations "D01".."D12") arranged
        on a ring. Adjacent locations on the ring are 1.0 apart; all
        non-adjacent pairs are 5.0 apart. The optimal tour follows the
        ring in either direction: cost = 13.0.

        Assertions
        ----------
        - Route visits every destination exactly once, starts and ends
          at "S".
        - Total distance <= 26.0 (2x optimal).

        Why it matters
        --------------
        Catches heuristic routers that degrade severely at moderate scale,
        e.g., random-order traversals that ignore proximity. Existing
        tests check correctness and speed but never check solution quality
        for inputs larger than 3 destinations.
        """
        nodes = ["S"] + [f"D{i:02d}" for i in range(1, 13)]
        n = len(nodes)  # 13

        travel_matrix = {}
        for i, src in enumerate(nodes):
            travel_matrix[src] = {}
            for j, dst in enumerate(nodes):
                if i == j:
                    travel_matrix[src][dst] = 0.0
                elif abs(i - j) == 1 or abs(i - j) == n - 1:
                    # Adjacent on the ring (including wrap-around)
                    travel_matrix[src][dst] = 1.0
                else:
                    # Non-adjacent: expensive shortcut
                    travel_matrix[src][dst] = 5.0

        destinations = nodes[1:]  # D01 through D12
        optimal_cost = 13.0  # Full ring traversal

        route, distance = find_optimal_route("S", destinations, travel_matrix)

        # Structural correctness
        self.assertEqual(route[0], "S", "Route must start at S")
        self.assertEqual(route[-1], "S", "Route must end at S")
        for d in destinations:
            self.assertIn(d, route, f"Destination {d} missing from route")
            self.assertEqual(
                route.count(d), 1, f"Destination {d} visited more than once"
            )

        # Quality: route must be within 2x of the known optimal
        self.assertLessEqual(
            distance,
            optimal_cost * 2.0,
            f"Route distance {distance:.1f} exceeds 2x optimal "
            f"({optimal_cost:.1f}). The router is producing poor-quality "
            f"routes for 12 destinations.",
        )

    # ================================================================
    # Gap 2: Matching order-independence
    # ================================================================

    def test_matching_order_independence(self):
        """Shuffling the job list should not reduce the number of assigned jobs.

        Use case: a dispatcher uploads a batch of jobs; the system should
        not accidentally leave jobs unassigned because the rows arrived in
        a different order from a CSV export.

        Setup
        -----
        3 engineers with overlapping skills at different locations.
        6 jobs (1 hour each) with varied skill requirements and locations.
        Travel times are short (0.5h) and capacity is generous (8h), so
        all 6 jobs are assignable regardless of processing order.

        Assertions
        ----------
        - Baseline (original order): all 6 jobs assigned, 0 unassigned.
        - 5 shuffled orderings: each assigns the same total number of
          jobs as the baseline.

        Why it matters
        --------------
        Greedy matchers that process jobs one-at-a-time can make
        suboptimal early decisions based on input order, filling an
        engineer's capacity with easy jobs and leaving harder ones
        stranded. This test exposes such order-sensitivity.
        """
        travel_matrix = {
            "A": {"A": 0.0, "B": 0.5, "C": 0.5},
            "B": {"A": 0.5, "B": 0.0, "C": 0.5},
            "C": {"A": 0.5, "B": 0.5, "C": 0.0},
        }

        engineers = [
            Engineer(
                id=1, name="Alice", location="A",
                skills=["electrical", "plumbing"], working_hours=8.0,
            ),
            Engineer(
                id=2, name="Bob", location="B",
                skills=["electrical", "hvac"], working_hours=8.0,
            ),
            Engineer(
                id=3, name="Carol", location="C",
                skills=["plumbing", "hvac"], working_hours=8.0,
            ),
        ]

        jobs = [
            Job(id=1, location="A", time="09:00", required_skills=["electrical"], length=1.0),
            Job(id=2, location="B", time="09:00", required_skills=["electrical"], length=1.0),
            Job(id=3, location="A", time="10:00", required_skills=["plumbing"], length=1.0),
            Job(id=4, location="C", time="10:00", required_skills=["plumbing"], length=1.0),
            Job(id=5, location="B", time="11:00", required_skills=["hvac"], length=1.0),
            Job(id=6, location="C", time="11:00", required_skills=["hvac"], length=1.0),
        ]

        # Baseline: original order
        assignments_orig, unassigned_orig = assign_jobs(
            engineers, list(jobs), travel_matrix
        )
        baseline_assigned = sum(len(v) for v in assignments_orig.values())

        self.assertEqual(
            len(unassigned_orig), 0,
            f"Baseline left {len(unassigned_orig)} jobs unassigned; "
            f"all 6 should fit given ample capacity and matching skills.",
        )

        # Shuffled orderings should produce equally good results
        rng = random.Random(42)
        for trial in range(5):
            shuffled = list(jobs)
            rng.shuffle(shuffled)
            assignments_shuf, unassigned_shuf = assign_jobs(
                engineers, shuffled, travel_matrix
            )
            assigned_count = sum(len(v) for v in assignments_shuf.values())

            self.assertEqual(
                assigned_count,
                baseline_assigned,
                f"Shuffle trial {trial}: assigned {assigned_count} jobs "
                f"vs baseline {baseline_assigned}. Input order should not "
                f"change total assignments.",
            )

    # ================================================================
    # Gap 3: Workload balance among equally-qualified engineers
    # ================================================================

    def test_workload_balanced_among_equal_engineers(self):
        """Work should be spread across engineers, not piled onto one.

        Use case: a company has 3 identically-skilled engineers based at
        the same depot. When 6 short local jobs come in, a good scheduler
        distributes the work so no single engineer is overloaded while
        others sit idle.

        Setup
        -----
        3 engineers at location "HQ", each with skill "general" and 8h
        capacity. 6 jobs at "HQ", each 1 hour, requiring "general".
        Zero travel overhead (all same location).

        Assertions
        ----------
        - All 6 jobs assigned (plenty of capacity).
        - No single engineer has more than 4 of the 6 jobs (generous
          upper bound; perfect balance = 2 each).
        - At least 2 of the 3 engineers receive work.

        Why it matters
        --------------
        A greedy matcher that always tries the first eligible engineer
        will assign all 6 jobs to engineer #1 (loads = [6, 0, 0]).
        This wastes workforce capacity and creates an unfair schedule.
        The test ensures the system distributes work when engineers are
        interchangeable.
        """
        travel_matrix = {
            "HQ": {"HQ": 0.0},
        }

        engineers = [
            Engineer(id=1, name="Eng1", location="HQ", skills=["general"], working_hours=8.0),
            Engineer(id=2, name="Eng2", location="HQ", skills=["general"], working_hours=8.0),
            Engineer(id=3, name="Eng3", location="HQ", skills=["general"], working_hours=8.0),
        ]

        jobs = [
            Job(
                id=i, location="HQ", time="09:00",
                required_skills=["general"], length=1.0,
            )
            for i in range(1, 7)
        ]

        assignments, unassigned = assign_jobs(engineers, jobs, travel_matrix)

        # All jobs should be assigned
        self.assertEqual(
            len(unassigned), 0, "All 6 jobs should be assigned"
        )
        total_assigned = sum(len(v) for v in assignments.values())
        self.assertEqual(total_assigned, 6, "Total assigned should be 6")

        # Balance checks
        loads = [len(assignments[eid]) for eid in [1, 2, 3]]

        max_load = max(loads)
        self.assertLessEqual(
            max_load, 4,
            f"Workload imbalance: loads are {loads}. Max load {max_load} "
            f"exceeds 4 (perfect balance = 2 each). Work should be "
            f"distributed, not piled onto one engineer.",
        )

        engineers_with_work = sum(1 for load in loads if load > 0)
        self.assertGreaterEqual(
            engineers_with_work, 2,
            f"Only {engineers_with_work} engineer(s) got work out of 3. "
            f"At least 2 identical engineers should share the load.",
        )


if __name__ == "__main__":
    unittest.main()
