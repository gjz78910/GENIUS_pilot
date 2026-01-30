"""Tests for external data loader.

Tests loading valid JSON files, error handling, data validation,
and integration with scheduler.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest

from src.features.data_loader import load_data
from src.scheduling.scheduler import Scheduler


class TestDataLoader(unittest.TestCase):
    """Test cases for data loader."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_data = {
            "engineers": [
                {
                    "id": 1,
                    "name": "Alice",
                    "location": "A",
                    "skills": ["repair"],
                    "working_hours": 8.0,
                }
            ],
            "jobs": [
                {"id": 1, "location": "A", "time": "09:00", "required_skills": ["repair"], "length": 2.0}
            ],
            "travel_matrix": {"A": {"A": 0.0}},
        }

    def test_load_valid_json_file(self):
        """Test loading a valid JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(self.valid_data, f)
            file_path = f.name

        try:
            engineers, jobs, travel_matrix = load_data(file_path)
            self.assertEqual(len(engineers), 1)
            self.assertEqual(len(jobs), 1)
            self.assertEqual(engineers[0].id, 1)
            self.assertEqual(engineers[0].name, "Alice")
            self.assertEqual(jobs[0].id, 1)
            self.assertIn("A", travel_matrix)
        finally:
            os.unlink(file_path)

    def test_load_missing_required_fields(self):
        """Test error handling for missing required fields."""
        # Missing engineers
        invalid_data = {"jobs": [], "travel_matrix": {}}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_data, f)
            file_path = f.name

        try:
            with self.assertRaises(ValueError) as cm:
                load_data(file_path)
            self.assertIn("engineers", str(cm.exception))
        finally:
            os.unlink(file_path)

        # Missing engineer id
        invalid_data = {
            "engineers": [{"name": "Alice", "location": "A"}],
            "jobs": [],
            "travel_matrix": {"A": {"A": 0.0}},
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_data, f)
            file_path = f.name

        try:
            with self.assertRaises(ValueError) as cm:
                load_data(file_path)
            self.assertIn("id", str(cm.exception))
        finally:
            os.unlink(file_path)

    def test_load_invalid_location(self):
        """Test error handling for locations not in travel matrix."""
        invalid_data = {
            "engineers": [{"id": 1, "name": "Alice", "location": "Z"}],
            "jobs": [],
            "travel_matrix": {"A": {"A": 0.0}},
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_data, f)
            file_path = f.name

        try:
            with self.assertRaises(ValueError) as cm:
                load_data(file_path)
            self.assertIn("location", str(cm.exception))
        finally:
            os.unlink(file_path)

    def test_load_duplicate_ids(self):
        """Test error handling for duplicate IDs."""
        invalid_data = {
            "engineers": [
                {"id": 1, "name": "Alice", "location": "A"},
                {"id": 1, "name": "Bob", "location": "A"},
            ],
            "jobs": [],
            "travel_matrix": {"A": {"A": 0.0}},
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_data, f)
            file_path = f.name

        try:
            with self.assertRaises(ValueError) as cm:
                load_data(file_path)
            self.assertIn("Duplicate", str(cm.exception))
        finally:
            os.unlink(file_path)

    def test_load_default_values(self):
        """Test that default values are applied correctly."""
        data_with_defaults = {
            "engineers": [{"id": 1, "name": "Alice", "location": "A"}],
            "jobs": [{"id": 1, "location": "A", "time": "09:00"}],
            "travel_matrix": {"A": {"A": 0.0}},
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data_with_defaults, f)
            file_path = f.name

        try:
            engineers, jobs, _ = load_data(file_path)
            self.assertEqual(engineers[0].working_hours, 8.0)  # Default
            self.assertEqual(engineers[0].skills, [])  # Default
            self.assertEqual(jobs[0].length, 1.0)  # Default
            self.assertEqual(jobs[0].required_skills, [])  # Default
        finally:
            os.unlink(file_path)

    def test_integration_with_scheduler(self):
        """Test integration with scheduler."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(self.valid_data, f)
            file_path = f.name

        try:
            engineers, jobs, travel_matrix = load_data(file_path)
            scheduler = Scheduler(engineers, jobs, travel_matrix)
            assignments, routes, unassigned = scheduler.create_schedule()

            self.assertGreaterEqual(len(assignments), 0)
            self.assertIsInstance(unassigned, list)
        finally:
            os.unlink(file_path)

    def test_load_invalid_job_location(self):
        """Test error handling for job locations not in travel matrix."""
        invalid_data = {
            "engineers": [{"id": 1, "name": "Alice", "location": "A", "skills": ["repair"]}],
            "jobs": [{"id": 1, "location": "Z", "time": "09:00", "required_skills": ["repair"]}],
            "travel_matrix": {"A": {"A": 0.0}},
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_data, f)
            file_path = f.name

        try:
            with self.assertRaises(ValueError) as cm:
                load_data(file_path)
            self.assertIn("location", str(cm.exception).lower())
        finally:
            os.unlink(file_path)

    def test_load_invalid_time_format(self):
        """Test error handling for invalid job time format."""
        # Time "25:00" is not a valid HH:MM time
        invalid_data = {
            "engineers": [{"id": 1, "name": "Alice", "location": "A"}],
            "jobs": [{"id": 1, "location": "A", "time": "25:00"}],
            "travel_matrix": {"A": {"A": 0.0}},
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_data, f)
            file_path = f.name

        try:
            with self.assertRaises(ValueError) as cm:
                load_data(file_path)
            self.assertIn("time", str(cm.exception).lower())
        finally:
            os.unlink(file_path)

        # Non-numeric time string
        invalid_data["jobs"][0]["time"] = "abc"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_data, f)
            file_path = f.name

        try:
            with self.assertRaises(ValueError) as cm:
                load_data(file_path)
            self.assertIn("time", str(cm.exception).lower())
        finally:
            os.unlink(file_path)

    def test_load_asymmetric_travel_matrix(self):
        """Test error handling for asymmetric travel matrix."""
        invalid_data = {
            "engineers": [{"id": 1, "name": "Alice", "location": "A"}],
            "jobs": [{"id": 1, "location": "B", "time": "09:00"}],
            "travel_matrix": {
                "A": {"A": 0.0, "B": 0.5},
                "B": {"A": 1.0, "B": 0.0},  # B->A != A->B (asymmetric)
            },
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_data, f)
            file_path = f.name

        try:
            with self.assertRaises(ValueError) as cm:
                load_data(file_path)
            self.assertIn("symmetric", str(cm.exception).lower())
        finally:
            os.unlink(file_path)

    def test_load_nonzero_diagonal(self):
        """Test error handling for non-zero diagonal in travel matrix."""
        invalid_data = {
            "engineers": [{"id": 1, "name": "Alice", "location": "A"}],
            "jobs": [{"id": 1, "location": "A", "time": "09:00"}],
            "travel_matrix": {
                "A": {"A": 1.0},  # Diagonal should be 0.0
            },
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_data, f)
            file_path = f.name

        try:
            with self.assertRaises(ValueError) as cm:
                load_data(file_path)
            self.assertIn("diagonal", str(cm.exception).lower())
        finally:
            os.unlink(file_path)

    def test_load_invalid_working_hours(self):
        """Test error handling for invalid working hours."""
        # Negative working hours
        invalid_data = {
            "engineers": [{"id": 1, "name": "Alice", "location": "A", "working_hours": -1.0}],
            "jobs": [],
            "travel_matrix": {"A": {"A": 0.0}},
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_data, f)
            file_path = f.name

        try:
            with self.assertRaises(ValueError) as cm:
                load_data(file_path)
            self.assertIn("working_hours", str(cm.exception).lower())
        finally:
            os.unlink(file_path)

        # Excessively large working hours (> 24)
        invalid_data["engineers"][0]["working_hours"] = 25.0
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_data, f)
            file_path = f.name

        try:
            with self.assertRaises(ValueError) as cm:
                load_data(file_path)
            self.assertIn("working_hours", str(cm.exception).lower())
        finally:
            os.unlink(file_path)

    def test_load_benchmark_file(self):
        """Test loading one of the benchmark files."""
        benchmark_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "benchmarks"
        )
        benchmark_file = os.path.join(benchmark_dir, "benchmark_small_01.json")

        if os.path.exists(benchmark_file):
            engineers, jobs, travel_matrix = load_data(benchmark_file)
            self.assertGreater(len(engineers), 0)
            self.assertGreater(len(jobs), 0)
            self.assertIn("A", travel_matrix)


if __name__ == "__main__":
    unittest.main()
