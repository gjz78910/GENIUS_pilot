"""Integration tests for Scheduler.

Tests organized by requirement:
- End-to-end workflow testing
- Integration of all requirements (1-5)
- Output requirements validation
"""

from __future__ import annotations

import unittest

from src.models.engineer import Engineer
from src.models.job import Job
from src.scheduling.scheduler import Scheduler


class TestSchedulerIntegration(unittest.TestCase):
    """Integration test cases for Scheduler."""

    def setUp(self):
        """Set up test fixtures with travel time matrix (in hours)."""
        self.travel_matrix = {
            "A": {"A": 0.0, "B": 0.5, "C": 1.0, "D": 1.5},
            "B": {"A": 0.5, "B": 0.0, "C": 0.5, "D": 1.0},
            "C": {"A": 1.0, "B": 0.5, "C": 0.0, "D": 0.5},
            "D": {"A": 1.5, "B": 1.0, "C": 0.5, "D": 0.0},
        }

    # ========================================
    # INTEGRATION: Complete Workflow
    # ========================================

    def test_complete_scheduling_workflow(self):
        """Test complete scheduling workflow from assignment to routing.
        
        Integration test: Requirements 1-5 working together.
        """
        engineers = [
            Engineer(id=1, name="Alice", location="A", skills=["repair"], working_hours=8.0),
            Engineer(id=2, name="Bob", location="B", skills=["install"], working_hours=8.0),
        ]
        jobs = [
            Job(id=1, location="B", time="09:00", required_skills=["repair"], length=2.0),
            Job(id=2, location="C", time="10:00", required_skills=["install"], length=2.0),
        ]
        
        scheduler = Scheduler(engineers, jobs, self.travel_matrix)
        assignments, routes, unassigned = scheduler.create_schedule()
        
        self.assertEqual(len(assignments), 2)
        self.assertEqual(len(unassigned), 0)
        self.assertGreater(len(routes), 0)

    # ========================================
    # Edge Cases
    # ========================================

    def test_scheduler_with_no_jobs(self):
        """Test scheduler with no jobs.
        
        Edge case: Should handle empty job list gracefully.
        """
        engineers = [Engineer(id=1, name="Alice", location="A", skills=["repair"], working_hours=8.0)]
        jobs = []
        
        scheduler = Scheduler(engineers, jobs, self.travel_matrix)
        assignments, routes, unassigned = scheduler.create_schedule()
        
        self.assertEqual(len(assignments[1]), 0)
        self.assertEqual(len(routes), 0)
        self.assertEqual(len(unassigned), 0)

    def test_scheduler_with_no_engineers(self):
        """Test scheduler with no engineers.
        
        Edge case: All jobs should be unassigned (Requirement 4).
        """
        engineers = []
        jobs = [Job(id=1, location="A", time="09:00", required_skills=["repair"], length=2.0)]
        
        scheduler = Scheduler(engineers, jobs, self.travel_matrix)
        assignments, routes, unassigned = scheduler.create_schedule()
        
        self.assertEqual(len(assignments), 0)
        self.assertEqual(len(routes), 0)
        self.assertEqual(len(unassigned), 1)

    # ========================================
    # REQUIREMENT 5: Route Generation
    # ========================================

    def test_routes_generated_for_assigned_engineers(self):
        """Test that routes are generated only for engineers with assignments.
        
        Requirement 5: Routes only needed for engineers with jobs.
        """
        engineers = [
            Engineer(id=1, name="Alice", location="A", skills=["repair"], working_hours=8.0),
            Engineer(id=2, name="Bob", location="B", skills=["install"], working_hours=8.0),
        ]
        jobs = [Job(id=1, location="C", time="09:00", required_skills=["repair"], length=2.0)]
        
        scheduler = Scheduler(engineers, jobs, self.travel_matrix)
        assignments, routes, unassigned = scheduler.create_schedule()
        
        self.assertIn(1, routes)  # Alice has a job
        self.assertNotIn(2, routes)  # Bob has no jobs

    def test_route_includes_all_job_locations(self):
        """Test that generated routes include all assigned job locations.
        
        Requirement 5: Route must visit all assigned job locations.
        """
        engineers = [Engineer(id=1, name="Alice", location="A", skills=["repair"], working_hours=8.0)]
        jobs = [
            Job(id=1, location="B", time="09:00", required_skills=["repair"], length=1.0),
            Job(id=2, location="C", time="10:00", required_skills=["repair"], length=1.0),
        ]
        
        scheduler = Scheduler(engineers, jobs, self.travel_matrix)
        assignments, routes, unassigned = scheduler.create_schedule()
        
        route, distance = routes[1]
        self.assertIn("B", route)
        self.assertIn("C", route)
        self.assertEqual(route[0], "A")  # Starts at engineer location
        self.assertEqual(route[-1], "A")  # Returns to engineer location

    # ========================================
    # REQUIREMENT 4: Unassigned Jobs Tracking
    # ========================================

    def test_unassigned_jobs_tracked(self):
        """Test that unassigned jobs are properly tracked.
        
        Requirement 4: Track and highlight unassigned jobs.
        """
        engineers = [Engineer(id=1, name="Alice", location="A", skills=["repair"], working_hours=2.0)]
        jobs = [
            Job(id=1, location="D", time="09:00", required_skills=["repair"], length=1.0),
            Job(id=2, location="D", time="10:00", required_skills=["repair"], length=1.0),
            Job(id=3, location="D", time="11:00", required_skills=["repair"], length=1.0),
        ]
        
        scheduler = Scheduler(engineers, jobs, self.travel_matrix)
        assignments, routes, unassigned = scheduler.create_schedule()
        
        self.assertGreater(len(unassigned), 0)

    # ========================================
    # REQUIREMENT 2: Capacity Management
    # ========================================

    def test_multiple_jobs_per_engineer(self):
        """Test that engineers can be assigned multiple jobs.
        
        Requirement 2: Engineers can handle multiple jobs within capacity.
        """
        engineers = [Engineer(id=1, name="Alice", location="A", skills=["repair"], working_hours=10.0)]
        jobs = [
            Job(id=1, location="B", time="09:00", required_skills=["repair"], length=1.0),
            Job(id=2, location="C", time="10:00", required_skills=["repair"], length=1.0),
            Job(id=3, location="D", time="11:00", required_skills=["repair"], length=1.0),
        ]
        
        scheduler = Scheduler(engineers, jobs, self.travel_matrix)
        assignments, routes, unassigned = scheduler.create_schedule()
        
        self.assertGreaterEqual(len(assignments[1]), 2)

    def test_scheduler_respects_working_hours(self):
        """Test that scheduler respects engineer working hours.
        
        Requirement 2 & 3: total_job_time + travel_time ≤ working_hours
        """
        engineers = [Engineer(id=1, name="Alice", location="A", skills=["repair"], working_hours=3.0)]
        jobs = [
            Job(id=1, location="B", time="09:00", required_skills=["repair"], length=2.0),
            Job(id=2, location="C", time="10:00", required_skills=["repair"], length=2.0),
        ]
        
        scheduler = Scheduler(engineers, jobs, self.travel_matrix)
        assignments, routes, unassigned = scheduler.create_schedule()
        
        # Verify total time doesn't exceed working hours
        if assignments[1]:
            route, travel_time = routes.get(1, ((), 0.0))
            job_time = sum(j.length for j in assignments[1])
            total_time = job_time + travel_time
            # Total time should not exceed engineer's working hours
            self.assertLessEqual(total_time, 3.0)


if __name__ == "__main__":
    unittest.main()
