"""Unit tests for the Engineer and Job models."""

import unittest

from src.models.engineer import Engineer
from src.models.job import Job


class TestModels(unittest.TestCase):
    """Simple tests for data models."""

    def test_engineer_initialisation(self) -> None:
        engineer = Engineer(id=42, name="Test", location="X", skills=["Repair", "Install"])
        # Attributes should be set correctly
        self.assertEqual(engineer.id, 42)
        self.assertEqual(engineer.name, "Test")
        self.assertEqual(engineer.location, "X")
        # Skills should be normalised to lower case
        self.assertEqual(engineer.skills, ["repair", "install"])

    def test_job_initialisation(self) -> None:
        job = Job(id=7, location="Y", time="14:00", required_skills=["Maintain", "Repair"])
        self.assertEqual(job.id, 7)
        self.assertEqual(job.location, "Y")
        self.assertEqual(job.time, "14:00")
        # Required skills should be normalised to lower case
        self.assertEqual(job.required_skills, ["maintain", "repair"])


if __name__ == "__main__":
    unittest.main()