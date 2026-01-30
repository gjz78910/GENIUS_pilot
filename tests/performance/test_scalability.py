"""Scalability tests for scheduling system.

These tests verify that the scheduler can handle large workloads efficiently.
They measure execution time (runtime) as the metric to assess scalability.

Purpose: Test if the system scales to handle realistic field service datasets.
Metric: Execution time in seconds (faster = better scalability).

IMPORTANT NOTES:
- These tests use the REAL scheduler with brute-force routing
- Current implementation is fast because engineers get few jobs each (limited by working hours)
- Brute-force TSP is called per engineer with their assigned jobs (typically 3-10 jobs)
- With 5 jobs per engineer: 5! = 120 permutations (fast)
- With 10 jobs per engineer: 10! = 3,628,800 permutations (slow!)
- The bottleneck appears when engineers have many jobs OR when testing with larger datasets

Unlike benchmark tests which measure solution quality, these tests focus on scalability.
Unlike correctness tests which check if code works, these tests check if code scales.

Note: The production code uses brute-force routing. While it's fast for current test cases
(engineers get few jobs), it would be VERY slow if engineers had many jobs per route.
Participants should optimize routing to handle cases where engineers have 10+ jobs.
"""

from __future__ import annotations

import math
import random
import time
import unittest
from typing import Dict, List, Sequence, Tuple

from src.models.engineer import Engineer
from src.models.job import Job
from src.scheduling.scheduler import Scheduler


# Realistic skill pools for field service industries
ALL_SKILLS = [
    "repair", "install", "inspect", "configure", "maintain",
    "replace", "upgrade", "troubleshoot", "calibrate", "test",
]


def _create_travel_matrix(
    num_locations: int, min_travel: float = 0.2, max_travel: float = 0.8, seed: int = 42
) -> Dict[str, Dict[str, float]]:
    """Create a travel matrix for given number of locations."""
    rng = random.Random(seed)
    locations = [f"LOC{i:05d}" for i in range(num_locations)]
    return {
        loc1: {
            loc2: round(rng.uniform(min_travel, max_travel), 2) if loc1 != loc2 else 0.0
            for loc2 in locations
        }
        for loc1 in locations
    }


def _create_engineers(
    num_engineers: int,
    num_locations: int,
    working_hours: float = 8.0,
    skill_variety: str = "uniform",
    seed: int = 42,
) -> List[Engineer]:
    """Create engineers with realistic, varied skill sets.

    skill_variety:
        "uniform"  - all engineers share the same two skills
        "mixed"    - engineers have 2-4 skills drawn from the full pool
        "specialist" - engineers each specialise in 1-2 skills
    """
    rng = random.Random(seed)
    engineers = []
    for i in range(1, num_engineers + 1):
        if skill_variety == "uniform":
            skills = ["repair", "install"]
        elif skill_variety == "mixed":
            k = rng.randint(2, 4)
            skills = rng.sample(ALL_SKILLS, k)
        else:  # specialist
            k = rng.randint(1, 2)
            skills = rng.sample(ALL_SKILLS, k)
        engineers.append(
            Engineer(
                id=i,
                name=f"Eng{i:04d}",
                location=f"LOC{(i * 10) % num_locations:05d}",
                skills=skills,
                working_hours=working_hours,
            )
        )
    return engineers


def _create_jobs(
    num_jobs: int,
    num_locations: int,
    length_range: Tuple[float, float] = (0.5, 3.0),
    skills_per_job: Tuple[int, int] = (1, 1),
    seed: int = 42,
) -> List[Job]:
    """Create jobs with variable lengths and skill requirements."""
    rng = random.Random(seed)
    jobs = []
    for i in range(1, num_jobs + 1):
        length = round(rng.uniform(*length_range), 1)
        k = rng.randint(*skills_per_job)
        required_skills = rng.sample(ALL_SKILLS, k)
        jobs.append(
            Job(
                id=i,
                location=f"LOC{i % num_locations:05d}",
                time="09:00",
                required_skills=required_skills,
                length=length,
            )
        )
    return jobs


def _print_result(label, elapsed, assignments, unassigned):
    """Print a summary of test results."""
    jobs_per_eng = [len(j) for j in assignments.values() if j]
    max_jobs = max(jobs_per_eng) if jobs_per_eng else 0
    avg_jobs = sum(jobs_per_eng) / len(jobs_per_eng) if jobs_per_eng else 0
    total = sum(len(j) for j in assignments.values())

    print(f"\n{label}")
    print(f"  Time: {elapsed:.2f}s")
    print(f"  Assigned: {total}, Unassigned: {len(unassigned)}")
    print(f"  Jobs/engineer: max={max_jobs}, avg={avg_jobs:.1f}")
    if max_jobs <= 5:
        print(f"  Routing load: LIGHT ({max_jobs} jobs) — brute-force is fine")
    elif max_jobs <= 8:
        print(f"  Routing load: MODERATE ({max_jobs} jobs) — optimisation helps")
    elif max_jobs <= 12:
        print(f"  Routing load: HEAVY ({max_jobs} jobs) — optimisation needed")
    else:
        perm = math.factorial(max_jobs) if max_jobs <= 20 else "> 2.4×10^18"
        print(f"  Routing load: EXTREME ({max_jobs} jobs, {perm} permutations) — brute-force infeasible")


class TestScalability(unittest.TestCase):
    """Progressive scalability tests modelled after real field-service companies.

    Each test simulates a larger / more complex company.  The brute-force
    router will struggle or time-out on harder tests, demonstrating why
    participants need to optimise routing.
    """

    # ------------------------------------------------------------------
    # Test 1 — Small HVAC company
    # ------------------------------------------------------------------
    def test_1_easy(self):
        """Test 1: EASY — Small HVAC company, 30 engineers, 300 short jobs.

        8-hour day, quick service calls (0.3-1.0h each).  All engineers
        share the same skills so every engineer is a candidate for every
        job.  Short jobs pack 8-10 per engineer, giving routing some work.
        30 metro-area locations.
        """
        tm = _create_travel_matrix(30, min_travel=0.1, max_travel=0.5)
        engineers = _create_engineers(30, 30, working_hours=8.0, skill_variety="uniform")
        jobs = _create_jobs(300, 30, length_range=(0.3, 1.0), skills_per_job=(1, 1))

        scheduler = Scheduler(engineers, jobs, tm)
        t0 = time.time()
        assignments, routes, unassigned = scheduler.create_schedule()
        elapsed = time.time() - t0

        _print_result("Test 1 — Small HVAC company", elapsed, assignments, unassigned)
        self.assertLess(elapsed, 120.0, f"Took {elapsed:.2f}s — target < 10s")
        self.assertGreater(sum(len(j) for j in assignments.values()), 0)

    # ------------------------------------------------------------------
    # Test 2 — Mid-size telecom installer
    # ------------------------------------------------------------------
    def test_2_moderate(self):
        """Test 2: MODERATE — Regional telecom, 80 engineers, 1000 jobs.

        9-hour days with short installations (0.3-1.0h) across 60 locations.
        Mixed skills (2-4 per engineer) create realistic matching pressure.
        Engineers accumulate 8-12 jobs each, stressing both matching and
        routing phases.
        """
        tm = _create_travel_matrix(60, min_travel=0.1, max_travel=0.8)
        engineers = _create_engineers(80, 60, working_hours=9.0, skill_variety="mixed")
        jobs = _create_jobs(1000, 60, length_range=(0.3, 1.0), skills_per_job=(1, 2))

        scheduler = Scheduler(engineers, jobs, tm)
        t0 = time.time()
        assignments, routes, unassigned = scheduler.create_schedule()
        elapsed = time.time() - t0

        _print_result("Test 2 — Regional telecom", elapsed, assignments, unassigned)
        self.assertLess(elapsed, 300.0, f"Took {elapsed:.2f}s — target < 5s")
        self.assertGreater(sum(len(j) for j in assignments.values()), 0)

    # ------------------------------------------------------------------
    # Test 3 — Regional utility company (inspections)
    # ------------------------------------------------------------------
    def test_3_hard(self):
        """Test 3: HARD — Utility company running meter reads and inspections.

        250 engineers doing 3000 short inspection jobs (0.2-0.6h each)
        across 140 locations with mixed skills.  Very short jobs mean
        engineers accumulate 12-20 jobs each, pushing brute-force into
        completely infeasible territory (15! ≈ 1.3T, 20! ≈ 2.4×10^18).
        """
        tm = _create_travel_matrix(140, min_travel=0.05, max_travel=0.4)
        engineers = _create_engineers(250, 140, working_hours=10.0, skill_variety="mixed")
        jobs = _create_jobs(3000, 140, length_range=(0.2, 0.6), skills_per_job=(1, 3))

        scheduler = Scheduler(engineers, jobs, tm)
        t0 = time.time()
        assignments, routes, unassigned = scheduler.create_schedule()
        elapsed = time.time() - t0

        _print_result("Test 3 — Utility inspections", elapsed, assignments, unassigned)
        self.assertLess(elapsed, 600.0, f"Took {elapsed:.2f}s — target < 10s")
        self.assertGreater(sum(len(j) for j in assignments.values()), 0)

    # ------------------------------------------------------------------
    # Test 4 — Large facilities company (long shifts, many short tasks)
    # ------------------------------------------------------------------
    def test_4_very_hard(self):
        """Test 4: VERY HARD — Facilities management across a city campus.

        350 engineers on 10-hour shifts handling 3800 quick maintenance
        tasks (0.2-1.0h) across 160 buildings.  Jobs require 1-3 specialist
        skills, creating heavy matching pressure.  Each engineer can
        accumulate 12-20 jobs, making brute-force completely infeasible
        (15! ≈ 1.3T).
        """
        tm = _create_travel_matrix(160, min_travel=0.05, max_travel=0.5)
        engineers = _create_engineers(350, 160, working_hours=10.0, skill_variety="mixed")
        jobs = _create_jobs(3800, 160, length_range=(0.2, 1.0), skills_per_job=(1, 3))

        scheduler = Scheduler(engineers, jobs, tm)
        t0 = time.time()
        assignments, routes, unassigned = scheduler.create_schedule()
        elapsed = time.time() - t0

        _print_result("Test 4 — Large facilities (10h shifts)", elapsed, assignments, unassigned)
        self.assertLess(elapsed, 1800.0, f"Took {elapsed:.2f}s — target < 15s")
        self.assertGreater(sum(len(j) for j in assignments.values()), 0)

    # ------------------------------------------------------------------
    # Test 5 — National field-service operation
    # ------------------------------------------------------------------
    def test_5_extremely_hard(self):
        """Test 5: EXTREMELY HARD — National operation, 350 engineers, 4000 jobs.

        Large-scale nationwide operation: 350 engineers across 180 locations,
        4000 jobs with specialist skill requirements (1-3 skills).
        10-hour days with short-to-medium tasks (0.3-1.5h) mean 8-15+ jobs
        per engineer.  Tests both matching throughput and routing scalability
        at enterprise scale.
        """
        tm = _create_travel_matrix(180, min_travel=0.1, max_travel=1.5)
        engineers = _create_engineers(350, 180, working_hours=10.0, skill_variety="mixed")
        jobs = _create_jobs(4000, 180, length_range=(0.3, 1.5), skills_per_job=(1, 3))

        scheduler = Scheduler(engineers, jobs, tm)
        t0 = time.time()
        assignments, routes, unassigned = scheduler.create_schedule()
        elapsed = time.time() - t0

        _print_result("Test 5 — National operation", elapsed, assignments, unassigned)
        self.assertLess(elapsed, 3600.0, f"Took {elapsed:.2f}s — target < 30s")
        self.assertGreater(sum(len(j) for j in assignments.values()), 0)


if __name__ == "__main__":
    unittest.main()
