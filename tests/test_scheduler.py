"""Tests for scheduling logic including assignment and routing.

Note: These tests work with the dynamic sample data (100 jobs, 10 engineers).
"""

import unittest

from typing import Dict, List

from src.models.engineer import Engineer
from src.models.job import Job
from src.scheduling.scheduler import Scheduler
from data.sample_data import engineers as sample_engineers, jobs as sample_jobs
from data.travel_matrix import travel_matrix


class TestScheduler(unittest.TestCase):
    def setUp(self) -> None:
        # Copy sample data to avoid mutation, preserving all attributes
        self.engineers: List[Engineer] = [
            Engineer(e.id, e.name, e.location, e.skills.copy(), e.working_hours) 
            for e in sample_engineers
        ]
        self.jobs: List[Job] = [
            Job(j.id, j.location, j.time, j.required_skills.copy(), j.length) 
            for j in sample_jobs
        ]
        self.scheduler = Scheduler(self.engineers, self.jobs, travel_matrix)

    def test_assignments(self) -> None:
        """Test that jobs are assigned and all engineers with skills get work."""
        assignments, _, unassigned = self.scheduler.create_schedule()
        
        # Verify all engineers are in assignments dict
        self.assertEqual(len(assignments), len(self.engineers))
        
        # Count total assigned jobs
        total_assigned = sum(len(jobs) for jobs in assignments.values())
        
        # Verify jobs are being assigned (should be > 0)
        self.assertGreater(total_assigned, 0)
        
        # Verify assigned + unassigned = total jobs
        self.assertEqual(total_assigned + len(unassigned), len(self.jobs))
        
        # Verify each assigned job has an engineer with required skills
        for eng_id, jobs in assignments.items():
            engineer = next(e for e in self.engineers if e.id == eng_id)
            for job in jobs:
                self.assertTrue(
                    all(skill in engineer.skills for skill in job.required_skills),
                    f"Engineer {eng_id} lacks skills for job {job.id}"
                )

    def test_routes(self) -> None:
        """Test that routes are generated correctly for assigned engineers."""
        assignments, routes, unassigned = self.scheduler.create_schedule()
        
        # Check that each engineer's route starts and ends at the engineer's location
        for engineer in self.engineers:
            assigned_jobs = assignments.get(engineer.id, [])
            if not assigned_jobs:
                # Engineers with no jobs should not have a route
                self.assertNotIn(engineer.id, routes)
                continue
            
            route, distance = routes[engineer.id]
            
            # Route should start and end at engineer.location
            self.assertEqual(route[0], engineer.location)
            self.assertEqual(route[-1], engineer.location)
            
            # Route should contain exactly len(assigned_jobs) + 2 points (start and end)
            self.assertEqual(len(route), len(assigned_jobs) + 2)
            
            # Distance should be non-negative
            self.assertGreaterEqual(distance, 0.0)
    
    def test_working_hours_respected(self) -> None:
        """Test that engineers don't exceed their working hours."""
        assignments, routes, unassigned = self.scheduler.create_schedule()
        
        for engineer in self.engineers:
            assigned_jobs = assignments.get(engineer.id, [])
            if not assigned_jobs:
                continue
            
            # Calculate total job time
            total_job_time = sum(job.length for job in assigned_jobs)
            
            # Get travel time from route
            route, travel_time = routes.get(engineer.id, ((), 0.0))
            
            # Total time should not exceed working hours
            total_time = total_job_time + travel_time
            self.assertLessEqual(
                total_time, 
                engineer.working_hours,
                f"Engineer {engineer.id} exceeds working hours: {total_time:.1f}h > {engineer.working_hours}h"
            )


if __name__ == "__main__":
    unittest.main()