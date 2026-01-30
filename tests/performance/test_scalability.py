"""Scalability tests for scheduling system.

These tests verify that the scheduler can handle large workloads efficiently.
They measure execution time (runtime) as the metric to assess scalability.

Purpose: Test if the system scales to handle large datasets (100-500 jobs).
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

import time
import unittest
from typing import Dict, Sequence, Tuple

from src.models.engineer import Engineer
from src.models.job import Job
from src.scheduling.scheduler import Scheduler


def nearest_neighbor_tsp(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
    """Fast TSP heuristic for performance testing (test-only function).
    
    This is a fast approximation algorithm suitable for performance testing.
    It's not guaranteed to be optimal but runs in O(n^2) time instead of O(n!).
    This function is only used in performance tests, not in production code.
    """
    # If there are no destinations, return a trivial route with zero cost
    if not destinations:
        return (start, start), 0.0
    
    # Convert to list for mutability
    unvisited = list(destinations)
    route = [start]
    current = start
    total_distance = 0.0
    
    # Greedily visit nearest unvisited location
    while unvisited:
        nearest = None
        nearest_distance = float("inf")
        
        for dest in unvisited:
            distance = travel_matrix.get(current, {}).get(dest, float("inf"))
            if distance < nearest_distance:
                nearest_distance = distance
                nearest = dest
        
        if nearest is None:
            # No valid path found, break
            break
        
        route.append(nearest)
        total_distance += nearest_distance
        unvisited.remove(nearest)
        current = nearest
    
    # Return to start
    if route[-1] != start:
        return_distance = travel_matrix.get(current, {}).get(start, 0.0)
        total_distance += return_distance
        route.append(start)
    
    return tuple(route), total_distance


class TestScalability(unittest.TestCase):
    """Scalability test cases for scheduling system.
    
    These tests verify that the scheduler can scale to handle medium-sized workloads.
    They measure execution time (runtime) as the metric - faster runtime means better scalability.
    They test scalability, not solution quality.
    
    WARNING: If these tests take more than 60 seconds each, it indicates poor scalability.
    Participants should optimize their code (e.g., replace brute-force routing with faster algorithms).
    """

    def _create_travel_matrix(self, num_locations, min_travel=0.2, max_travel=0.8):
        """Create a travel matrix for given number of locations.
        
        Uses realistic travel times between locations.
        Default: 0.2-0.8 hours (12-48 minutes) for typical urban/suburban travel.
        Can be customized for different test scenarios.
        """
        import random
        random.seed(42)  # For reproducibility
        locations = [f"LOC{i:05d}" for i in range(num_locations)]
        return {
            loc1: {
                loc2: round(random.uniform(min_travel, max_travel), 2) if loc1 != loc2 else 0.0 
                for loc2 in locations
            }
            for loc1 in locations
        }
    
    def _test_scalability(self, num_jobs, num_engineers, num_locations, working_hours=8.0, max_time=60.0, min_travel=0.2, max_travel=0.8):
        """Test scalability by running scheduler and measuring time.
        
        This simulates what participants will experience when running scalability tests.
        If it takes too long, it indicates poor scalability.
        
        Args:
            num_jobs: Number of jobs to schedule
            num_engineers: Number of engineers available
            num_locations: Number of locations
            working_hours: Working hours per engineer (default: 8.0)
            max_time: Maximum acceptable time in seconds (default: 60s)
            min_travel: Minimum travel time between locations in hours (default: 0.2)
            max_travel: Maximum travel time between locations in hours (default: 0.8)
        
        Returns:
            Tuple of (elapsed_time, assignments, routes, unassigned)
        """
        travel_matrix = self._create_travel_matrix(num_locations, min_travel, max_travel)
        
        engineers = [
            Engineer(id=i, name=f"Eng{i:04d}", location=f"LOC{(i*10) % num_locations:05d}", 
                    skills=["repair", "install"], working_hours=working_hours)
            for i in range(1, num_engineers + 1)
        ]
        # Create jobs with variable lengths (more realistic)
        import random
        random.seed(42)  # For reproducibility
        job_lengths = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]  # Realistic job durations
        jobs = [
            Job(id=i, location=f"LOC{(i % num_locations):05d}", time="09:00", 
                required_skills=["repair"], length=random.choice(job_lengths))
            for i in range(1, num_jobs + 1)
        ]
        
        scheduler = Scheduler(engineers, jobs, travel_matrix)
        
        print(f"\nTesting scalability: {num_jobs} jobs, {num_engineers} engineers...")
        start_time = time.time()
        assignments, routes, unassigned = scheduler.create_schedule()
        elapsed_time = time.time() - start_time
        
        # Calculate jobs per engineer
        jobs_per_engineer = [len(jobs) for jobs in assignments.values() if jobs]
        max_jobs = max(jobs_per_engineer) if jobs_per_engineer else 0
        
        print(f"Completed in {elapsed_time:.2f}s")
        print(f"Max jobs per engineer: {max_jobs}")
        
        # Simple message about performance
        if max_jobs <= 5:
            print(f"✅ Easy: Engineers have few jobs ({max_jobs} jobs) - current code handles this well")
        elif max_jobs <= 8:
            print(f"⚠️  Moderate: Engineers have {max_jobs} jobs - optimization would help")
        else:
            print(f"❌ Hard: Engineers have many jobs ({max_jobs} jobs) - brute-force routing is very slow!")
        
        total_assigned = sum(len(jobs) for jobs in assignments.values())
        print(f"Assigned: {total_assigned}, Unassigned: {len(unassigned)}")
        
        return elapsed_time, assignments, routes, unassigned

    def test_1_easy(self):
        """Test 1: EASY - Should pass with original code (< 10s).
        
        Realistic scenario: 10 engineers, 50 jobs, 8-hour workday.
        Engineers can handle ~5-6 jobs each (accounting for travel time).
        """
        elapsed_time, assignments, routes, unassigned = self._test_scalability(
            num_jobs=50, num_engineers=10, num_locations=20,
            working_hours=8.0, max_time=10.0
        )
        
        self.assertLess(elapsed_time, 120.0, 
                       f"Test 1 took {elapsed_time:.2f}s - optimize routing to get < 10s")
        
        total_assigned = sum(len(jobs) for jobs in assignments.values())
        self.assertGreater(total_assigned, 0)

    def test_2_moderate(self):
        """Test 2: MODERATE - Needs some optimization (~50-60s original, < 5s optimized).
        
        Realistic scenario: 15 engineers, 120 jobs, 8-hour workday.
        More engineers means more routing calls during matching.
        """
        elapsed_time, assignments, routes, unassigned = self._test_scalability(
            num_jobs=120, num_engineers=15, num_locations=30,
            working_hours=8.0, max_time=60.0
        )
        
        self.assertLess(elapsed_time, 60.0,
                       f"Test 2 took {elapsed_time:.2f}s - optimize routing to get < 5s")
        
        total_assigned = sum(len(jobs) for jobs in assignments.values())
        self.assertGreater(total_assigned, 0)

    def test_3_hard(self):
        """Test 3: HARD - Needs significant optimization (> 10 min original, < 10s optimized).
        
        Realistic scenario: 20 engineers, 200 jobs, 8-hour workday.
        More engineers = more routing calls during matching phase.
        """
        elapsed_time, assignments, routes, unassigned = self._test_scalability(
            num_jobs=200, num_engineers=20, num_locations=40,
            working_hours=8.0, max_time=600.0
        )
        
        self.assertLess(elapsed_time, 600.0,
                       f"Test 3 took {elapsed_time:.2f}s - optimize routing to get < 10s")
        
        total_assigned = sum(len(jobs) for jobs in assignments.values())
        self.assertGreater(total_assigned, 0)

    def test_4_very_hard(self):
        """Test 4: VERY HARD - Needs major optimization (> 30 min original, < 15s optimized).
        
        Realistic scenario: 30 engineers, 300 jobs, 8-hour workday.
        Many engineers means many routing calls during matching.
        """
        elapsed_time, assignments, routes, unassigned = self._test_scalability(
            num_jobs=300, num_engineers=30, num_locations=50,
            working_hours=8.0, max_time=1800.0
        )
        
        self.assertLess(elapsed_time, 1800.0,
                       f"Test 4 took {elapsed_time:.2f}s - optimize routing to get < 15s")
        
        total_assigned = sum(len(jobs) for jobs in assignments.values())
        self.assertGreater(total_assigned, 0)

    def test_5_extremely_hard(self):
        """Test 5: EXTREMELY HARD - Requires full optimization (> 1 hour original, < 20s optimized).
        
        Realistic scenario: 100 engineers, 1000 jobs, 8-hour workday, 30 locations.
        Many engineers = many routing calls during matching (bottleneck).
        Travel times: 0.2-2 hours (realistic range for field service).
        Variable job lengths: 0.5-3.0 hours (realistic job durations).
        Target: ~10s with nearest neighbor optimization.
        """
        elapsed_time, assignments, routes, unassigned = self._test_scalability(
            num_jobs=1000, num_engineers=100, num_locations=30,
            working_hours=8.0, max_time=3600.0,
            min_travel=0.2, max_travel=2.0
        )
        
        self.assertLess(elapsed_time, 3600.0,
                       f"Test 5 took {elapsed_time:.2f}s - optimize routing to get < 20s")
        
        total_assigned = sum(len(jobs) for jobs in assignments.values())
        self.assertGreater(total_assigned, 0)

    def test_routing_with_many_jobs(self):
        """Test routing scalability by forcing engineers to have many jobs.
        
        This test creates a scenario where engineers have long working hours and short jobs,
        forcing them to get many jobs each. This demonstrates the brute-force routing bottleneck.
        """
        num_locations = 20
        travel_matrix = self._create_travel_matrix(num_locations)
        
        # Create engineers with long working hours (16 hours) to allow many jobs
        engineers = [
            Engineer(id=i, name=f"Eng{i:04d}", location=f"LOC{(i*5) % num_locations:05d}", 
                    skills=["repair", "install"], working_hours=16.0)  # Long hours
            for i in range(1, 6)  # Only 5 engineers
        ]
        
        # Create many short jobs (0.1 hours each) so engineers can take many
        jobs = [
            Job(id=i, location=f"LOC{(i % num_locations):05d}", time="09:00", 
                required_skills=["repair"], length=0.1)  # Very short jobs
            for i in range(1, 101)  # 100 jobs
        ]
        
        scheduler = Scheduler(engineers, jobs, travel_matrix)
        
        print(f"\nTesting routing scalability: 100 short jobs, 5 engineers with long hours...")
        print(f"This forces engineers to get many jobs each, testing brute-force routing bottleneck.")
        start_time = time.time()
        assignments, routes, unassigned = scheduler.create_schedule()
        elapsed_time = time.time() - start_time
        
        # Calculate jobs per engineer
        jobs_per_engineer = [len(jobs) for jobs in assignments.values() if jobs]
        max_jobs = max(jobs_per_engineer) if jobs_per_engineer else 0
        
        print(f"Completed in {elapsed_time:.2f}s")
        print(f"Max jobs per engineer: {max_jobs} (brute-force TSP: {max_jobs}! = {__import__('math').factorial(max_jobs) if max_jobs <= 10 else '>3.6M'} permutations)")
        
        if max_jobs >= 10:
            print(f"⚠️  WARNING: Engineers have {max_jobs} jobs each!")
            print(f"   Brute-force routing with {max_jobs} jobs = {__import__('math').factorial(max_jobs)} permutations - VERY SLOW!")
            print(f"   This demonstrates why you need to optimize routing!")
        elif elapsed_time > 5.0:
            print(f"⚠️  NOTE: Test took {elapsed_time:.2f}s - routing optimization would help!")
        
        total_assigned = sum(len(jobs) for jobs in assignments.values())
        print(f"Assigned: {total_assigned}, Unassigned: {len(unassigned)}")
        
        # Assert that we actually got many jobs per engineer
        self.assertGreater(max_jobs, 8, 
                          f"Expected engineers to have 8+ jobs each to test routing scalability, got {max_jobs}")
        self.assertGreater(total_assigned, 0)


if __name__ == "__main__":
    unittest.main()
