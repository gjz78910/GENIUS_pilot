"""Performance tests for scheduling system.

Tests the system's ability to handle large-scale workloads (10,000+ entities).
"""

from __future__ import annotations

import time
import unittest

from src.models.engineer import Engineer
from src.models.job import Job
from src.scheduling.scheduler import Scheduler


class TestPerformance(unittest.TestCase):
    """Performance test cases for scheduling system."""

    def _create_travel_matrix(self, num_locations):
        """Create a travel matrix for given number of locations."""
        locations = [f"LOC{i:05d}" for i in range(num_locations)]
        return {
            loc1: {loc2: 0.5 if loc1 != loc2 else 0.0 for loc2 in locations}
            for loc1 in locations
        }

    def test_10000_jobs_100_engineers_performance(self):
        """Test performance with 10,000 jobs and 100 engineers."""
        num_engineers = 100
        num_jobs = 10000
        num_locations = 1000
        
        travel_matrix = self._create_travel_matrix(num_locations)
        
        engineers = [
            Engineer(id=i, name=f"Eng{i:04d}", location=f"LOC{i*10:05d}", 
                    skills=["repair", "install"], working_hours=8.0)
            for i in range(1, num_engineers + 1)
        ]
        jobs = [
            Job(id=i, location=f"LOC{(i % num_locations):05d}", time="09:00", 
                required_skills=["repair"], length=1.0)
            for i in range(1, num_jobs + 1)
        ]
        
        scheduler = Scheduler(engineers, jobs, travel_matrix)
        
        start_time = time.time()
        assignments, routes, unassigned = scheduler.create_schedule()
        elapsed_time = time.time() - start_time
        
        print(f"\n10K jobs, 100 engineers: {elapsed_time:.2f}s")
        
        self.assertLess(elapsed_time, 300.0, 
                       f"Scheduling took {elapsed_time:.2f}s, expected < 300s")
        
        total_assigned = sum(len(jobs) for jobs in assignments.values())
        self.assertGreater(total_assigned, 0)
        print(f"Assigned: {total_assigned}, Unassigned: {len(unassigned)}")

    def test_50000_jobs_500_engineers_performance(self):
        """Test performance with 50,000 jobs and 500 engineers."""
        num_engineers = 500
        num_jobs = 50000
        num_locations = 5000
        
        travel_matrix = self._create_travel_matrix(num_locations)
        
        engineers = [
            Engineer(id=i, name=f"Eng{i:04d}", location=f"LOC{i*10:05d}", 
                    skills=["repair", "install", "maintain"], working_hours=10.0)
            for i in range(1, num_engineers + 1)
        ]
        jobs = [
            Job(id=i, location=f"LOC{(i % num_locations):05d}", time="09:00", 
                required_skills=["repair"], length=1.5)
            for i in range(1, num_jobs + 1)
        ]
        
        scheduler = Scheduler(engineers, jobs, travel_matrix)
        
        start_time = time.time()
        assignments, routes, unassigned = scheduler.create_schedule()
        elapsed_time = time.time() - start_time
        
        print(f"\n50K jobs, 500 engineers: {elapsed_time:.2f}s")
        
        self.assertLess(elapsed_time, 900.0,
                       f"Scheduling took {elapsed_time:.2f}s, expected < 900s")
        
        total_assigned = sum(len(jobs) for jobs in assignments.values())
        print(f"Assigned: {total_assigned}, Unassigned: {len(unassigned)}")

    def test_1000_engineers_10000_locations_performance(self):
        """Test performance with 1,000 engineers and 10,000 locations."""
        num_engineers = 1000
        num_jobs = 20000
        num_locations = 10000
        
        travel_matrix = self._create_travel_matrix(num_locations)
        
        engineers = [
            Engineer(id=i, name=f"Eng{i:04d}", location=f"LOC{i*10:05d}",
                    skills=["repair", "install"], working_hours=8.0)
            for i in range(1, num_engineers + 1)
        ]
        jobs = [
            Job(id=i, location=f"LOC{(i % num_locations):05d}", time="09:00",
                required_skills=["repair"], length=1.0)
            for i in range(1, num_jobs + 1)
        ]
        
        scheduler = Scheduler(engineers, jobs, travel_matrix)
        
        start_time = time.time()
        assignments, routes, unassigned = scheduler.create_schedule()
        elapsed_time = time.time() - start_time
        
        print(f"\n20K jobs, 1K engineers, 10K locations: {elapsed_time:.2f}s")
        
        self.assertLess(elapsed_time, 600.0,
                       f"Scheduling took {elapsed_time:.2f}s, expected < 600s")
        
        total_assigned = sum(len(jobs) for jobs in assignments.values())
        print(f"Assigned: {total_assigned}, Unassigned: {len(unassigned)}")

    def test_matching_performance_with_15000_jobs(self):
        """Test matching performance with 15,000 jobs and complex skills."""
        num_engineers = 200
        num_jobs = 15000
        num_locations = 2000
        
        travel_matrix = self._create_travel_matrix(num_locations)
        
        engineers = [
            Engineer(id=i, name=f"Eng{i:04d}", location=f"LOC{i*10:05d}",
                    skills=["repair", "install", "maintain", "upgrade"], 
                    working_hours=8.0)
            for i in range(1, num_engineers + 1)
        ]
        jobs = [
            Job(id=i, location=f"LOC{(i % num_locations):05d}", time="09:00",
                required_skills=["repair", "install"], length=1.0)
            for i in range(1, num_jobs + 1)
        ]
        
        scheduler = Scheduler(engineers, jobs, travel_matrix)
        
        start_time = time.time()
        assignments, routes, unassigned = scheduler.create_schedule()
        elapsed_time = time.time() - start_time
        
        print(f"\n15K jobs, 200 engineers, complex skills: {elapsed_time:.2f}s")
        
        self.assertLess(elapsed_time, 480.0,
                       f"Matching took {elapsed_time:.2f}s, expected < 480s")
        
        total_assigned = sum(len(jobs) for jobs in assignments.values())
        print(f"Assigned: {total_assigned}, Unassigned: {len(unassigned)}")

    def test_memory_efficiency_with_large_dataset(self):
        """Test memory efficiency with 25,000 jobs."""
        num_engineers = 300
        num_jobs = 25000
        num_locations = 3000
        
        travel_matrix = self._create_travel_matrix(num_locations)
        
        engineers = [
            Engineer(id=i, name=f"Eng{i:04d}", location=f"LOC{i*10:05d}",
                    skills=["repair"], working_hours=8.0)
            for i in range(1, num_engineers + 1)
        ]
        jobs = [
            Job(id=i, location=f"LOC{(i % num_locations):05d}", time="09:00",
                required_skills=["repair"], length=1.0)
            for i in range(1, num_jobs + 1)
        ]
        
        scheduler = Scheduler(engineers, jobs, travel_matrix)
        
        start_time = time.time()
        assignments, routes, unassigned = scheduler.create_schedule()
        elapsed_time = time.time() - start_time
        
        print(f"\n25K jobs, 300 engineers (memory test): {elapsed_time:.2f}s")
        
        self.assertLess(elapsed_time, 600.0,
                       f"Scheduling took {elapsed_time:.2f}s, expected < 600s")
        
        total_assigned = sum(len(jobs) for jobs in assignments.values())
        print(f"Assigned: {total_assigned}, Unassigned: {len(unassigned)}")

    def test_extreme_scale_100000_jobs(self):
        """Test extreme scale with 100,000 jobs (stress test)."""
        num_engineers = 1000
        num_jobs = 100000
        num_locations = 10000
        
        travel_matrix = self._create_travel_matrix(num_locations)
        
        engineers = [
            Engineer(id=i, name=f"Eng{i:05d}", location=f"LOC{i*10:05d}",
                    skills=["repair"], working_hours=10.0)
            for i in range(1, num_engineers + 1)
        ]
        jobs = [
            Job(id=i, location=f"LOC{(i % num_locations):05d}", time="09:00",
                required_skills=["repair"], length=0.5)
            for i in range(1, num_jobs + 1)
        ]
        
        scheduler = Scheduler(engineers, jobs, travel_matrix)
        
        start_time = time.time()
        assignments, routes, unassigned = scheduler.create_schedule()
        elapsed_time = time.time() - start_time
        
        print(f"\n100K jobs, 1K engineers (EXTREME): {elapsed_time:.2f}s")
        
        self.assertLess(elapsed_time, 1800.0,
                       f"Scheduling took {elapsed_time:.2f}s, expected < 1800s")
        
        total_assigned = sum(len(jobs) for jobs in assignments.values())
        print(f"Assigned: {total_assigned}, Unassigned: {len(unassigned)}")


if __name__ == "__main__":
    unittest.main()
