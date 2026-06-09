"""Unit tests for matching algorithm.

Tests organized by requirement:
1. Skill Matching (Requirement 1)
2. Location Proximity (Requirement 1)
3. Working Hours & Capacity (Requirement 2)
4. Travel Time Integration (Requirement 3)
5. Overflow Handling (Requirement 4)
6. Edge Cases
"""

from __future__ import annotations

import unittest

from src.models.engineer import Engineer
from src.models.job import Job
from src.optimization.matching import assign_jobs


class TestMatching(unittest.TestCase):
    """Test cases for job assignment algorithm."""

    def setUp(self):
        """Set up test fixtures with simple travel matrix."""
        self.travel_matrix = {
            "A": {"A": 0.0, "B": 0.5, "C": 1.0},
            "B": {"A": 0.5, "B": 0.0, "C": 0.5},
            "C": {"A": 1.0, "B": 0.5, "C": 0.0},
        }

    # ========================================
    # REQUIREMENT 1: Skill Matching
    # ========================================

    def test_assign_job_to_skilled_engineer(self):
        """Test that jobs are assigned to engineers with required skills.
        
        Requirement 1: Skill matching - Engineers must have all required skills.
        """
        engineers = [Engineer(id=1, name="Alice", location="A", skills=["repair"], working_hours=8.0)]
        jobs = [Job(id=1, location="B", time="09:00", required_skills=["repair"], length=2.0)]
        
        assignments, unassigned = assign_jobs(engineers, jobs, self.travel_matrix)
        
        # Alice has repair skill, so job should be assigned
        self.assertEqual(len(assignments[1]), 1)
        self.assertEqual(assignments[1][0].id, 1)
        self.assertEqual(len(unassigned), 0)

    def test_no_assignment_without_skills(self):
        """Test that jobs are not assigned to engineers without required skills.
        
        Requirement 1: Skill matching - Job should remain unassigned if no engineer has skills.
        Requirement 4: Unassigned jobs should be tracked.
        """
        engineers = [Engineer(id=1, name="Alice", location="A", skills=["install"], working_hours=8.0)]
        jobs = [Job(id=1, location="B", time="09:00", required_skills=["repair"], length=2.0)]
        
        assignments, unassigned = assign_jobs(engineers, jobs, self.travel_matrix)
        
        # Alice lacks repair skill, job should be unassigned
        self.assertEqual(len(assignments[1]), 0)
        self.assertEqual(len(unassigned), 1)
        self.assertEqual(unassigned[0].id, 1)

    def test_multiple_required_skills(self):
        """Test assignment with multiple required skills.
        
        Requirement 1: Engineer must have ALL required skills for the job.
        """
        engineers = [
            Engineer(id=1, name="Alice", location="A", skills=["repair"], working_hours=8.0),
            Engineer(id=2, name="Bob", location="B", skills=["repair", "install"], working_hours=8.0),
        ]
        jobs = [Job(id=1, location="B", time="09:00", required_skills=["repair", "install"], length=2.0)]
        
        assignments, unassigned = assign_jobs(engineers, jobs, self.travel_matrix)
        
        # Only Bob has both repair AND install skills
        self.assertEqual(len(assignments[2]), 1)
        self.assertEqual(len(assignments[1]), 0)
        self.assertEqual(len(unassigned), 0)

    # ========================================
    # REQUIREMENT 1: Location Proximity
    # ========================================

    def test_assign_to_closest_engineer(self):
        """Test that jobs are assigned to the closest qualified engineer.
        
        Requirement 1: Location proximity - Prefer closest qualified engineer.
        """
        engineers = [
            Engineer(id=1, name="Alice", location="A", skills=["repair"], working_hours=8.0),
            Engineer(id=2, name="Bob", location="B", skills=["repair"], working_hours=8.0),
        ]
        jobs = [Job(id=1, location="B", time="09:00", required_skills=["repair"], length=2.0)]
        
        assignments, unassigned = assign_jobs(engineers, jobs, self.travel_matrix)
        
        # Bob at location B is closer to job at B (0.0h vs 0.5h travel)
        self.assertEqual(len(assignments[2]), 1)
        self.assertEqual(len(assignments[1]), 0)
        self.assertEqual(len(unassigned), 0)

    # ========================================
    # REQUIREMENT 2: Working Hours & Capacity
    # ========================================

    def test_capacity_constraint_respected(self):
        """Test that engineers are not assigned jobs exceeding their working hours.
        
        Requirement 2: total_job_time + travel_time + new_job ≤ working_hours
        """
        engineers = [Engineer(id=1, name="Alice", location="A", skills=["repair"], working_hours=3.0)]
        jobs = [
            Job(id=1, location="A", time="09:00", required_skills=["repair"], length=2.0),
            Job(id=2, location="A", time="10:00", required_skills=["repair"], length=2.0),
        ]
        
        assignments, unassigned = assign_jobs(engineers, jobs, self.travel_matrix)
        
        # Alice has 3.0h capacity, can't fit both 2.0h jobs
        self.assertEqual(len(assignments[1]), 1)
        self.assertEqual(len(unassigned), 1)

    # ========================================
    # REQUIREMENT 3: Travel Time Integration
    # ========================================

    def test_travel_time_included_in_capacity(self):
        """Test that travel time is accounted for in capacity checks.
        
        Requirement 3: Travel time is included in capacity calculations.
        Uses optimized TSP route for accurate estimation.
        """
        engineers = [Engineer(id=1, name="Alice", location="A", skills=["repair"], working_hours=3.0)]
        jobs = [
            Job(id=1, location="C", time="09:00", required_skills=["repair"], length=1.5),
            Job(id=2, location="C", time="10:00", required_skills=["repair"], length=1.5),
        ]
        
        assignments, unassigned = assign_jobs(engineers, jobs, self.travel_matrix)
        
        # With travel time from A to C (1.0h each way), only one job should fit
        # Job 1: 1.5h + ~2.0h travel = ~3.5h (exceeds 3.0h with both jobs)
        self.assertLessEqual(len(assignments[1]), 1)

    # ========================================
    # REQUIREMENT 4: Overflow Handling
    # ========================================

    def test_multiple_engineers_share_load(self):
        """Test that jobs are distributed when one engineer reaches capacity.
        
        Requirement 4: If closest engineer is at capacity, try next closest.
        Aim to assign all jobs by distributing across available engineers.
        """
        engineers = [
            Engineer(id=1, name="Alice", location="A", skills=["repair"], working_hours=3.0),
            Engineer(id=2, name="Bob", location="B", skills=["repair"], working_hours=8.0),
        ]
        jobs = [
            Job(id=1, location="A", time="09:00", required_skills=["repair"], length=2.0),
            Job(id=2, location="A", time="10:00", required_skills=["repair"], length=2.0),
        ]
        
        assignments, unassigned = assign_jobs(engineers, jobs, self.travel_matrix)
        
        # Alice (closest) gets first job, Bob gets second when Alice is full
        self.assertEqual(len(assignments[1]) + len(assignments[2]), 2)
        self.assertEqual(len(unassigned), 0)

    # ========================================
    # EDGE CASES
    # ========================================

    def test_empty_engineers_list(self):
        """Test behavior with no engineers.
        
        Edge case: All jobs should be unassigned.
        """
        engineers = []
        jobs = [Job(id=1, location="A", time="09:00", required_skills=["repair"], length=2.0)]
        
        assignments, unassigned = assign_jobs(engineers, jobs, self.travel_matrix)
        
        self.assertEqual(len(assignments), 0)
        self.assertEqual(len(unassigned), 1)

    def test_empty_jobs_list(self):
        """Test behavior with no jobs.
        
        Edge case: No assignments should be made.
        """
        engineers = [Engineer(id=1, name="Alice", location="A", skills=["repair"], working_hours=8.0)]
        jobs = []
        
        assignments, unassigned = assign_jobs(engineers, jobs, self.travel_matrix)
        
        self.assertEqual(len(assignments[1]), 0)
        self.assertEqual(len(unassigned), 0)


if __name__ == "__main__":
    unittest.main()


class TestBuildEligibilityMap(unittest.TestCase):
    """Unit tests for the _build_eligibility_map helper."""

    def setUp(self):
        """Set up test fixtures."""
        from src.optimization.matching import _build_eligibility_map

        self.build_map = _build_eligibility_map

    def test_single_skill_match(self):
        """Engineers with required skill are included."""
        engineers = [
            Engineer(id=1, name="Alice", location="A", skills=["repair"]),
            Engineer(id=2, name="Bob", location="B", skills=["install"]),
        ]
        jobs = [Job(id=1, location="A", time="09:00", required_skills=["repair"], length=1.0)]

        emap = self.build_map(engineers, jobs)
        self.assertEqual(len(emap[1]), 1)
        self.assertEqual(emap[1][0].id, 1)

    def test_multiple_skills_all_required(self):
        """Only engineers with ALL required skills are eligible."""
        engineers = [
            Engineer(id=1, name="Alice", location="A", skills=["repair"]),
            Engineer(id=2, name="Bob", location="B", skills=["repair", "install"]),
        ]
        jobs = [Job(id=1, location="A", time="09:00", required_skills=["repair", "install"], length=1.0)]

        emap = self.build_map(engineers, jobs)
        self.assertEqual(len(emap[1]), 1)
        self.assertEqual(emap[1][0].id, 2)

    def test_no_engineer_qualified(self):
        """Empty list when no engineer has required skills."""
        engineers = [
            Engineer(id=1, name="Alice", location="A", skills=["install"]),
        ]
        jobs = [Job(id=1, location="A", time="09:00", required_skills=["repair"], length=1.0)]

        emap = self.build_map(engineers, jobs)
        self.assertEqual(emap[1], [])

    def test_no_required_skills_all_eligible(self):
        """All engineers eligible when job requires no skills."""
        engineers = [
            Engineer(id=1, name="Alice", location="A", skills=["repair"]),
            Engineer(id=2, name="Bob", location="B", skills=["install"]),
        ]
        jobs = [Job(id=1, location="A", time="09:00", required_skills=[], length=1.0)]

        emap = self.build_map(engineers, jobs)
        self.assertEqual(len(emap[1]), 2)

    def test_multiple_jobs(self):
        """Each job gets its own eligibility list."""
        engineers = [
            Engineer(id=1, name="Alice", location="A", skills=["repair", "install"]),
            Engineer(id=2, name="Bob", location="B", skills=["repair"]),
        ]
        jobs = [
            Job(id=1, location="A", time="09:00", required_skills=["repair"], length=1.0),
            Job(id=2, location="B", time="10:00", required_skills=["install"], length=1.0),
        ]

        emap = self.build_map(engineers, jobs)
        self.assertEqual(len(emap[1]), 2)  # Both can repair
        self.assertEqual(len(emap[2]), 1)  # Only Alice can install
        self.assertEqual(emap[2][0].id, 1)

    def test_empty_engineers(self):
        """Empty eligibility for all jobs when no engineers."""
        engineers = []
        jobs = [Job(id=1, location="A", time="09:00", required_skills=["repair"], length=1.0)]

        emap = self.build_map(engineers, jobs)
        self.assertEqual(emap[1], [])

    def test_empty_jobs(self):
        """Empty map when no jobs."""
        engineers = [Engineer(id=1, name="Alice", location="A", skills=["repair"])]
        jobs = []

        emap = self.build_map(engineers, jobs)
        self.assertEqual(emap, {})


class TestHasCapacity(unittest.TestCase):
    """Unit tests for the _has_capacity helper."""

    def setUp(self):
        """Set up test fixtures."""
        from src.optimization.matching import _has_capacity

        self.has_capacity = _has_capacity
        self.travel_matrix = {
            "A": {"A": 0.0, "B": 1.0, "C": 2.0},
            "B": {"A": 1.0, "B": 0.0, "C": 1.0},
            "C": {"A": 2.0, "B": 1.0, "C": 0.0},
        }

    def test_fits_with_no_existing_jobs(self):
        """New job fits when engineer has plenty of capacity."""
        engineer = Engineer(id=1, name="Alice", location="A", skills=["repair"], working_hours=8.0)
        new_job = Job(id=1, location="A", time="09:00", required_skills=["repair"], length=2.0)

        self.assertTrue(self.has_capacity(engineer, [], new_job, self.travel_matrix))

    def test_exceeds_capacity(self):
        """New job does not fit when it would exceed working hours."""
        engineer = Engineer(id=1, name="Alice", location="A", skills=["repair"], working_hours=3.0)
        existing = [Job(id=1, location="B", time="09:00", required_skills=["repair"], length=2.0)]
        new_job = Job(id=2, location="C", time="10:00", required_skills=["repair"], length=2.0)

        # existing job (2h) + new job (2h) + travel A->B->C->A (1+1+2=4h) = 8h > 3h
        self.assertFalse(self.has_capacity(engineer, existing, new_job, self.travel_matrix))

    def test_exact_capacity(self):
        """Job fits when total equals exactly working hours."""
        engineer = Engineer(id=1, name="Alice", location="A", skills=["repair"], working_hours=4.0)
        # Job at A: 2h job + travel A->A->A = 0h travel. Total = 2h fits in 4h.
        existing = [Job(id=1, location="A", time="09:00", required_skills=["repair"], length=2.0)]
        new_job = Job(id=2, location="A", time="10:00", required_skills=["repair"], length=2.0)

        # 2 + 2 + 0 (all at A) = 4.0 == 4.0
        self.assertTrue(self.has_capacity(engineer, existing, new_job, self.travel_matrix))

    def test_travel_time_counted(self):
        """Travel time prevents job from fitting."""
        engineer = Engineer(id=1, name="Alice", location="A", skills=["repair"], working_hours=4.0)
        # Job at B: 2h job, travel A->B->A = 2h. Total = 4h, exact fit.
        # Adding another at C: 2+2 + travel(A->B->C->A or A->C->B->A) > 4h
        existing = [Job(id=1, location="B", time="09:00", required_skills=["repair"], length=2.0)]
        new_job = Job(id=2, location="C", time="10:00", required_skills=["repair"], length=2.0)

        self.assertFalse(self.has_capacity(engineer, existing, new_job, self.travel_matrix))

    def test_zero_travel_same_location(self):
        """No travel overhead when all jobs are at engineer's location."""
        engineer = Engineer(id=1, name="Alice", location="A", skills=["repair"], working_hours=6.0)
        existing = [Job(id=1, location="A", time="09:00", required_skills=["repair"], length=2.0)]
        new_job = Job(id=2, location="A", time="10:00", required_skills=["repair"], length=2.0)

        # 2 + 2 + 0 = 4.0 <= 6.0
        self.assertTrue(self.has_capacity(engineer, existing, new_job, self.travel_matrix))
