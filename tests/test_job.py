"""Unit tests for Job model.

Tests organized by requirement:
- Requirement 2: Working Hours Management (length attribute)
- Model validation and data normalization
"""

from __future__ import annotations

import unittest

from src.models.job import Job


class TestJob(unittest.TestCase):
    """Test cases for Job model."""

    # ========================================
    # Basic Model Functionality
    # ========================================

    def test_job_creation(self):
        """Test basic job creation with all attributes."""
        job = Job(id=1, location="A", time="09:00", required_skills=["repair"], length=2.0)
        self.assertEqual(job.id, 1)
        self.assertEqual(job.location, "A")
        self.assertEqual(job.time, "09:00")
        self.assertEqual(job.required_skills, ["repair"])
        self.assertEqual(job.length, 2.0)

    def test_required_skills_normalized_to_lowercase(self):
        """Test that required skills are automatically normalized to lowercase.
        
        Ensures case-insensitive skill matching.
        """
        job = Job(id=1, location="B", time="10:00", required_skills=["REPAIR", "Install"], length=1.5)
        self.assertEqual(job.required_skills, ["repair", "install"])

    def test_default_required_skills_empty_list(self):
        """Test that default required skills is an empty list."""
        job = Job(id=1, location="C", time="11:00", length=1.0)
        self.assertEqual(job.required_skills, [])

    # ========================================
    # REQUIREMENT 2: Job Length (Duration)
    # ========================================

    def test_default_length(self):
        """Test that default length is 1.0 hour.
        
        Requirement 2: Each job has a length (duration in hours).
        """
        job = Job(id=1, location="D", time="12:00", required_skills=["repair"])
        self.assertEqual(job.length, 1.0)

    def test_custom_length(self):
        """Test job with custom length.
        
        Requirement 2: Job lengths can vary (0.5, 1.0, 1.5, 2.0, 2.5, 3.0).
        """
        job = Job(id=1, location="A", time="09:00", required_skills=["repair"], length=2.5)
        self.assertEqual(job.length, 2.5)

    # ========================================
    # Additional Model Tests
    # ========================================

    def test_job_repr(self):
        """Test job string representation includes all attributes."""
        job = Job(id=1, location="E", time="13:00", required_skills=["repair"], length=2.5)
        repr_str = repr(job)
        self.assertIn("id=1", repr_str)
        self.assertIn("location='E'", repr_str)
        self.assertIn("time='13:00'", repr_str)
        self.assertIn("length=2.5", repr_str)


if __name__ == "__main__":
    unittest.main()
