"""Benchmark tests with known optimal solutions.

Tests the scheduling system against SMALL benchmark instances that have
known optimal solutions. These benchmarks measure solution QUALITY by comparing
actual results to the optimal solution stored in each benchmark JSON file.

**Why Benchmark Tests with Optimal Solutions?**
Benchmark tests are different from correctness and scalability tests:

1. **Correctness Tests** (test_matching.py, test_routing.py):
   - Purpose: Validate that solutions follow rules (skills, working hours, constraints)
   - Question: "Is the solution valid?" (binary: pass/fail)
   - Fast, small examples

2. **Benchmark Tests with Optimal Solutions** (this file - test_benchmarks.py):
   - Purpose: Measure solution QUALITY by comparing to known optimal solutions
   - Question: "How good is the solution?" (quantitative: accuracy, travel time ratio)
   - SMALL instances only (2-5 jobs) - each has a known optimal solution in the JSON file
   - Each benchmark file contains an "optimal_solution" field with:
     * Expected job assignments per engineer
     * Expected unassigned jobs
     * Optimal total travel time
   - Measures: assignment correctness, travel time efficiency, route quality
   - NOT for scalability - use test_scalability.py for that
"""

from __future__ import annotations

import json
import os
import unittest
from typing import Dict, List, Set

from src.models.engineer import Engineer
from src.models.job import Job
from src.scheduling.scheduler import Scheduler


def load_benchmark(file_path: str) -> dict:
    """Load a benchmark instance from JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)


def compute_distance_to_optimal(
    actual_assignments: Dict[int, List[Job]],
    actual_unassigned: List[Job],
    actual_routes: Dict[int, tuple[tuple[str, ...], float]],
    optimal_assignments: Dict[str, List[int]],
    optimal_unassigned: List[int],
    optimal_travel_time: float,
    travel_matrix: Dict[str, Dict[str, float]],
) -> Dict[str, float]:
    """Compute distance to optimal solution.

    Returns metrics comparing actual solution to optimal:
    - assignment_accuracy: fraction of jobs assigned correctly (0.0 to 1.0)
    - unassigned_penalty: number of extra/missing unassigned jobs
    - assignment_count_diff: difference in number of assigned jobs
    - travel_time_ratio: actual travel time / optimal travel time (1.0 = optimal, >1.0 = worse)
    - travel_time_diff: absolute difference in travel time (hours)
    """
    # Convert actual assignments to job ID sets for comparison
    actual_job_sets: Dict[int, Set[int]] = {
        eng_id: {job.id for job in jobs} for eng_id, jobs in actual_assignments.items()
    }
    actual_unassigned_ids = {job.id for job in actual_unassigned}

    optimal_job_sets: Dict[int, Set[int]] = {
        int(eng_id): set(job_ids) for eng_id, job_ids in optimal_assignments.items()
    }
    optimal_unassigned_set = set(optimal_unassigned)

    # Count correctly assigned jobs
    total_jobs = sum(len(jobs) for jobs in optimal_job_sets.values()) + len(optimal_unassigned_set)
    correctly_assigned = 0

    # Check assignments match optimal
    for eng_id, optimal_jobs in optimal_job_sets.items():
        actual_jobs = actual_job_sets.get(eng_id, set())
        correctly_assigned += len(optimal_jobs & actual_jobs)

    # Check unassigned jobs match
    correctly_unassigned = len(optimal_unassigned_set & actual_unassigned_ids)

    assignment_accuracy = (correctly_assigned + correctly_unassigned) / total_jobs if total_jobs > 0 else 1.0

    # Penalty for extra unassigned jobs
    extra_unassigned = len(actual_unassigned_ids - optimal_unassigned_set)
    missing_unassigned = len(optimal_unassigned_set - actual_unassigned_ids)
    unassigned_penalty = extra_unassigned + missing_unassigned

    # Difference in total assigned jobs
    actual_assigned_count = sum(len(jobs) for jobs in actual_assignments.values())
    optimal_assigned_count = sum(len(jobs) for jobs in optimal_job_sets.values())
    assignment_count_diff = abs(actual_assigned_count - optimal_assigned_count)

    # Calculate actual total travel time
    actual_total_travel_time = sum(
        travel_time for _, travel_time in actual_routes.values()
    )

    # Travel time metrics
    travel_time_diff = abs(actual_total_travel_time - optimal_travel_time)
    travel_time_ratio = (
        actual_total_travel_time / optimal_travel_time
        if optimal_travel_time > 0
        else (1.0 if actual_total_travel_time == 0 else float("inf"))
    )

    return {
        "assignment_accuracy": assignment_accuracy,
        "unassigned_penalty": unassigned_penalty,
        "assignment_count_diff": assignment_count_diff,
        "travel_time_ratio": travel_time_ratio,
        "travel_time_diff": travel_time_diff,
    }


class TestBenchmarksWithOptimal(unittest.TestCase):
    """Test benchmarks that have known optimal solutions.
    
    Each benchmark JSON file contains an "optimal_solution" field that specifies:
    - Which jobs should be assigned to which engineers
    - Which jobs should remain unassigned
    - The optimal total travel time
    
    Tests compare actual results to these optimal solutions to measure quality.
    """

    def setUp(self):
        """Set up benchmark directory path."""
        self.benchmark_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "benchmarks"
        )

    def _load_and_run_benchmark(self, filename: str):
        """Load benchmark and run scheduler."""
        file_path = os.path.join(self.benchmark_dir, filename)
        benchmark = load_benchmark(file_path)

        # Create engineers
        engineers = [
            Engineer(
                id=e["id"],
                name=e["name"],
                location=e["location"],
                skills=e["skills"],
                working_hours=e["working_hours"],
            )
            for e in benchmark["engineers"]
        ]

        # Create jobs
        jobs = [
            Job(
                id=j["id"],
                location=j["location"],
                time=j["time"],
                required_skills=j["required_skills"],
                length=j["length"],
            )
            for j in benchmark["jobs"]
        ]

        # Create scheduler and run
        scheduler = Scheduler(engineers, jobs, benchmark["travel_matrix"])
        assignments, routes, unassigned = scheduler.create_schedule()

        return assignments, routes, unassigned, benchmark

    def test_benchmark_small_01(self):
        """Test benchmark 1: Simple 2-engineer, 3-job case with known optimal solution."""
        assignments, routes, unassigned, benchmark = self._load_and_run_benchmark(
            "benchmark_small_01.json"
        )

        optimal = benchmark["optimal_solution"]

        # Compute distance to optimal
        metrics = compute_distance_to_optimal(
            assignments,
            unassigned,
            routes,
            optimal["assignments"],
            optimal["unassigned_jobs"],
            optimal.get("total_travel_time", 0.0),
            benchmark["travel_matrix"],
        )

        # Print metrics for participant visibility
        print(f"\n  Benchmark 1 Metrics:")
        print(f"    assignment_accuracy: {metrics['assignment_accuracy']:.3f} (target: 1.0)")
        print(f"    travel_time_ratio: {metrics['travel_time_ratio']:.3f} (target: ≤ 1.5)")
        print(f"    unassigned_penalty: {metrics['unassigned_penalty']}")
        
        # Should achieve optimal solution (accuracy = 1.0, no penalties)
        self.assertEqual(metrics["assignment_accuracy"], 1.0, "Should match optimal assignments")
        self.assertEqual(metrics["unassigned_penalty"], 0, "Should have no unassigned penalty")
        self.assertEqual(metrics["assignment_count_diff"], 0, "Should assign same number of jobs")
        
        # Travel time should be optimal or close to optimal
        self.assertLessEqual(
            metrics["travel_time_ratio"], 1.5,
            f"Travel time ratio {metrics['travel_time_ratio']:.2f} should be <= 1.5 (optimal = 1.0)"
        )

        # Verify all jobs assigned
        self.assertEqual(len(unassigned), 0, "All jobs should be assigned")

    def test_benchmark_small_02(self):
        """Test benchmark 2: 3-engineer, 5-job case with known optimal solution."""
        assignments, routes, unassigned, benchmark = self._load_and_run_benchmark(
            "benchmark_small_02.json"
        )

        optimal = benchmark["optimal_solution"]

        # Compute distance to optimal
        metrics = compute_distance_to_optimal(
            assignments,
            unassigned,
            routes,
            optimal["assignments"],
            optimal["unassigned_jobs"],
            optimal.get("total_travel_time", 0.0),
            benchmark["travel_matrix"],
        )

        # Print metrics for participant visibility
        print(f"\n  Benchmark 2 Metrics:")
        print(f"    assignment_accuracy: {metrics['assignment_accuracy']:.3f} (target: 1.0)")
        print(f"    travel_time_ratio: {metrics['travel_time_ratio']:.3f} (target: ≤ 1.5)")
        print(f"    unassigned_penalty: {metrics['unassigned_penalty']}")
        
        # Should achieve optimal solution (accuracy = 1.0, no penalties)
        self.assertEqual(metrics["assignment_accuracy"], 1.0, "Should match optimal assignments")
        self.assertEqual(metrics["unassigned_penalty"], 0, "Should have no unassigned penalty")
        # Travel time should be optimal or close to optimal
        self.assertLessEqual(
            metrics["travel_time_ratio"], 1.5,
            f"Travel time ratio {metrics['travel_time_ratio']:.2f} should be <= 1.5 (optimal = 1.0)"
        )
        self.assertEqual(len(unassigned), 0, "All assignable jobs should be assigned")

    def test_benchmark_small_03(self):
        """Test benchmark 3: Case with unassignable jobs and known optimal solution."""
        assignments, routes, unassigned, benchmark = self._load_and_run_benchmark(
            "benchmark_small_03.json"
        )

        optimal = benchmark["optimal_solution"]

        # Compute distance to optimal
        metrics = compute_distance_to_optimal(
            assignments,
            unassigned,
            routes,
            optimal["assignments"],
            optimal["unassigned_jobs"],
            optimal.get("total_travel_time", 0.0),
            benchmark["travel_matrix"],
        )

        # Should correctly identify unassignable job
        unassigned_ids = {job.id for job in unassigned}
        optimal_unassigned = set(optimal["unassigned_jobs"])
        self.assertEqual(
            unassigned_ids, optimal_unassigned, "Should correctly identify unassignable jobs"
        )

        # Print metrics for participant visibility
        print(f"\n  Benchmark 3 Metrics:")
        print(f"    assignment_accuracy: {metrics['assignment_accuracy']:.3f} (target: 1.0)")
        if optimal.get("total_travel_time", 0.0) > 0:
            print(f"    travel_time_ratio: {metrics['travel_time_ratio']:.3f} (target: ≤ 1.5)")
        print(f"    unassigned_penalty: {metrics['unassigned_penalty']}")
        
        # Should achieve optimal solution (accuracy = 1.0 for assignable jobs)
        self.assertEqual(metrics["assignment_accuracy"], 1.0, "Should match optimal assignments for assignable jobs")
        self.assertEqual(metrics["unassigned_penalty"], 0, "Should have no unassigned penalty for assignable jobs")
        # Travel time should be optimal or close to optimal
        if optimal.get("total_travel_time", 0.0) > 0:
            self.assertLessEqual(
                metrics["travel_time_ratio"], 1.5,
                f"Travel time ratio {metrics['travel_time_ratio']:.2f} should be <= 1.5 (optimal = 1.0)"
            )

    def test_benchmark_small_04(self):
        """Test benchmark 4: Capacity-skill trade-off — greedy leaves a job unassigned."""
        assignments, routes, unassigned, benchmark = self._load_and_run_benchmark(
            "benchmark_small_04.json"
        )

        optimal = benchmark["optimal_solution"]

        # Compute distance to optimal
        metrics = compute_distance_to_optimal(
            assignments,
            unassigned,
            routes,
            optimal["assignments"],
            optimal["unassigned_jobs"],
            optimal.get("total_travel_time", 0.0),
            benchmark["travel_matrix"],
        )

        # Print metrics for participant visibility
        print(f"\n  Benchmark 4 Metrics:")
        print(f"    assignment_accuracy: {metrics['assignment_accuracy']:.3f} (target: 1.0)")
        print(f"    unassigned_penalty: {metrics['unassigned_penalty']} (target: 0)")
        print(f"    jobs_assigned: {sum(len(j) for j in assignments.values())}/{len(benchmark['jobs'])}")
        if metrics["unassigned_penalty"] == 0:
            print(f"    travel_time_ratio: {metrics['travel_time_ratio']:.3f} (target: ≤ 1.5)")

        # Verify all jobs assigned
        self.assertEqual(len(unassigned), 0, "All jobs should be assigned")
        self.assertEqual(metrics["unassigned_penalty"], 0, "Should have no unassigned penalty")

        # Should achieve optimal solution
        self.assertEqual(metrics["assignment_accuracy"], 1.0, "Should match optimal assignments")

        # Travel time should be optimal or close to optimal
        self.assertLessEqual(
            metrics["travel_time_ratio"], 1.5,
            f"Travel time ratio {metrics['travel_time_ratio']:.2f} should be <= 1.5 (optimal = 1.0)"
        )

    def test_benchmark_small_05(self):
        """Test benchmark 5: Exclusive skill trap — greedy fills capacity with shared skills."""
        assignments, routes, unassigned, benchmark = self._load_and_run_benchmark(
            "benchmark_small_05.json"
        )

        optimal = benchmark["optimal_solution"]

        # Compute distance to optimal
        metrics = compute_distance_to_optimal(
            assignments,
            unassigned,
            routes,
            optimal["assignments"],
            optimal["unassigned_jobs"],
            optimal.get("total_travel_time", 0.0),
            benchmark["travel_matrix"],
        )

        # Print metrics for participant visibility
        print(f"\n  Benchmark 5 Metrics:")
        print(f"    assignment_accuracy: {metrics['assignment_accuracy']:.3f} (target: 1.0)")
        print(f"    unassigned_penalty: {metrics['unassigned_penalty']} (target: 0)")
        print(f"    jobs_assigned: {sum(len(j) for j in assignments.values())}/{len(benchmark['jobs'])}")
        if metrics["unassigned_penalty"] == 0:
            print(f"    travel_time_ratio: {metrics['travel_time_ratio']:.3f} (target: ≤ 1.5)")

        # Verify all jobs assigned
        self.assertEqual(len(unassigned), 0, "All jobs should be assigned")
        self.assertEqual(metrics["unassigned_penalty"], 0, "Should have no unassigned penalty")

        # Should achieve optimal solution
        self.assertEqual(metrics["assignment_accuracy"], 1.0, "Should match optimal assignments")

        # Travel time should be optimal or close to optimal
        self.assertLessEqual(
            metrics["travel_time_ratio"], 1.5,
            f"Travel time ratio {metrics['travel_time_ratio']:.2f} should be <= 1.5 (optimal = 1.0)"
        )

    def test_brute_force_routing_optimal(self):
        """Test that brute-force routing finds optimal routes for small instances."""
        assignments, routes, unassigned, benchmark = self._load_and_run_benchmark(
            "benchmark_small_01.json"
        )

        # For engineer 1 with jobs at same location, travel should be minimal
        if 1 in routes:
            route, travel_time = routes[1]
            # Engineer 1 is at A, jobs 1 and 3 are at A
            # Optimal route: A -> A -> A (no travel between jobs at same location)
            self.assertLessEqual(travel_time, 0.1, "Travel time should be minimal for same location")


if __name__ == "__main__":
    unittest.main()
