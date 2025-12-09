"""Tests for scheduling logic including assignment and routing."""

import unittest

from typing import Dict, List

from src.models.engineer import Engineer
from src.models.job import Job
from src.scheduling.scheduler import Scheduler
from data.sample_data import engineers as sample_engineers, jobs as sample_jobs
from data.travel_matrix import travel_matrix


class TestScheduler(unittest.TestCase):
    def setUp(self) -> None:
        # copy sample data to avoid mutation
        self.engineers: List[Engineer] = [Engineer(e.id, e.name, e.location, e.skills.copy()) for e in sample_engineers]
        self.jobs: List[Job] = [Job(j.id, j.location, j.time, j.required_skills.copy()) for j in sample_jobs]
        self.scheduler = Scheduler(self.engineers, self.jobs, travel_matrix)

    def test_assignments(self) -> None:
        assignments, _ = self.scheduler.create_schedule()
        # Build mapping of engineer id to job ids for easier assertion
        assigned_job_ids: Dict[int, List[int]] = {
            eng.id: [job.id for job in jobs]
            for eng_id, jobs in assignments.items()
            for eng in self.engineers
            if eng.id == eng_id
        }
        # Expected assignments based on skills and proximity
        expected = {
            1: [4, 5, 6, 7, 8, 9, 10, 11, 12, 13],  # Engineer 1 (Alice) gets all jobs at location A
            2: [2],     # Engineer 2 should get job 2
            3: [3],     # Engineer 3 should get job 3
            4: [1],     # Engineer 4 should get job 1
        }
        # Compare sets to ignore ordering
        for eng_id, job_ids in expected.items():
            self.assertCountEqual(assigned_job_ids.get(eng_id, []), job_ids)

    def test_routes(self) -> None:
        assignments, routes = self.scheduler.create_schedule()
        # Check that each engineer's route starts and ends at the engineer's location
        for engineer in self.engineers:
            assigned_jobs = assignments.get(engineer.id, [])
            if not assigned_jobs:
                # Engineers with no jobs should not have a route
                self.assertNotIn(engineer.id, routes)
                continue
            route, distance = routes[engineer.id]
            # route should start and end at engineer.location
            self.assertEqual(route[0], engineer.location)
            self.assertEqual(route[-1], engineer.location)
            # route should contain exactly len(assigned_jobs) + 2 points (start and end)
            self.assertEqual(len(route), len(assigned_jobs) + 2)


if __name__ == "__main__":
    unittest.main()