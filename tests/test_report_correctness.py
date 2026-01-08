"""Correctness tests for CSV report generation.

Tests validate:
- Sequential timing (jobs don't overlap)
- Working-hours window (all jobs fit within engineer's capacity)
- No missing/duplicate jobs
- Time calculations (start/end times based on route order)
- CSV format and data types
"""

from __future__ import annotations

import csv
import os
import tempfile
import unittest

from src.features.report import generate_report
from src.models.engineer import Engineer
from src.models.job import Job
from src.scheduling.scheduler import Scheduler


class TestReportCorrectness(unittest.TestCase):
    """Test cases for report correctness validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.travel_matrix = {
            "A": {"A": 0.0, "B": 0.5, "C": 1.0},
            "B": {"A": 0.5, "B": 0.0, "C": 0.5},
            "C": {"A": 1.0, "B": 0.5, "C": 0.0},
        }
        self.engineers = [
            Engineer(id=1, name="Alice", location="A", skills=["repair"], working_hours=8.0),
            Engineer(id=2, name="Bob", location="B", skills=["install"], working_hours=6.0),
        ]
        self.jobs = [
            Job(id=1, location="A", time="09:00", required_skills=["repair"], length=2.0),
            Job(id=2, location="B", time="10:00", required_skills=["install"], length=1.5),
            Job(id=3, location="A", time="11:00", required_skills=["repair"], length=1.0),
        ]

    def test_sequential_timing_no_overlap(self):
        """Test that jobs don't overlap in time."""
        scheduler = Scheduler(self.engineers, self.jobs, self.travel_matrix)
        assignments, routes, unassigned = scheduler.create_schedule()

        with tempfile.TemporaryDirectory() as tmpdir:
            generate_report(
                self.engineers, assignments, routes, self.travel_matrix, output_dir=tmpdir
            )

            # Check engineer 1's report
            file_path = os.path.join(tmpdir, "engineer_1_schedule.csv")
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)

                # Check no overlapping jobs
                for i in range(len(rows) - 1):
                    current_end = float(rows[i]["job_end_time_minutes"])
                    next_start = float(rows[i + 1]["job_start_time_minutes"])
                    self.assertLessEqual(
                        current_end,
                        next_start,
                        f"Job {rows[i]['job_id']} ends after job {rows[i+1]['job_id']} starts",
                    )

    def test_working_hours_window(self):
        """Test that all jobs fit within engineer's working hours."""
        scheduler = Scheduler(self.engineers, self.jobs, self.travel_matrix)
        assignments, routes, unassigned = scheduler.create_schedule()

        with tempfile.TemporaryDirectory() as tmpdir:
            generate_report(
                self.engineers, assignments, routes, self.travel_matrix, output_dir=tmpdir
            )

            for engineer in self.engineers:
                file_path = os.path.join(tmpdir, f"engineer_{engineer.id}_schedule.csv")
                if os.path.exists(file_path):
                    with open(file_path, "r") as f:
                        reader = csv.DictReader(f)
                        rows = list(reader)

                    if rows:
                        # Find last job end time
                        last_end_time = max(float(row["job_end_time_minutes"]) for row in rows)
                        working_hours_minutes = engineer.working_hours * 60.0

                        self.assertLessEqual(
                            last_end_time,
                            working_hours_minutes,
                            f"Engineer {engineer.id} exceeds working hours: "
                            f"{last_end_time/60:.2f}h > {engineer.working_hours}h",
                        )

    def test_no_missing_jobs(self):
        """Test that all assigned jobs appear in the report."""
        scheduler = Scheduler(self.engineers, self.jobs, self.travel_matrix)
        assignments, routes, unassigned = scheduler.create_schedule()

        with tempfile.TemporaryDirectory() as tmpdir:
            generate_report(
                self.engineers, assignments, routes, self.travel_matrix, output_dir=tmpdir
            )

            for engineer_id, assigned_jobs in assignments.items():
                if not assigned_jobs:
                    continue

                file_path = os.path.join(tmpdir, f"engineer_{engineer_id}_schedule.csv")
                self.assertTrue(os.path.exists(file_path), f"Report file missing for engineer {engineer_id}")

                with open(file_path, "r") as f:
                    reader = csv.DictReader(f)
                    reported_job_ids = {int(row["job_id"]) for row in reader}

                assigned_job_ids = {job.id for job in assigned_jobs}
                self.assertEqual(
                    reported_job_ids,
                    assigned_job_ids,
                    f"Reported jobs don't match assigned jobs for engineer {engineer_id}",
                )

    def test_no_duplicate_jobs(self):
        """Test that no job appears twice in a report."""
        scheduler = Scheduler(self.engineers, self.jobs, self.travel_matrix)
        assignments, routes, unassigned = scheduler.create_schedule()

        with tempfile.TemporaryDirectory() as tmpdir:
            generate_report(
                self.engineers, assignments, routes, self.travel_matrix, output_dir=tmpdir
            )

            for engineer_id, assigned_jobs in assignments.items():
                if not assigned_jobs:
                    continue

                file_path = os.path.join(tmpdir, f"engineer_{engineer_id}_schedule.csv")
                if os.path.exists(file_path):
                    with open(file_path, "r") as f:
                        reader = csv.DictReader(f)
                        job_ids = [int(row["job_id"]) for row in reader]

                    self.assertEqual(
                        len(job_ids),
                        len(set(job_ids)),
                        f"Duplicate jobs found in report for engineer {engineer_id}",
                    )

    def test_time_calculations(self):
        """Test that time calculations are correct (end = start + duration)."""
        scheduler = Scheduler(self.engineers, self.jobs, self.travel_matrix)
        assignments, routes, unassigned = scheduler.create_schedule()

        with tempfile.TemporaryDirectory() as tmpdir:
            generate_report(
                self.engineers, assignments, routes, self.travel_matrix, output_dir=tmpdir
            )

            for engineer_id in assignments.keys():
                file_path = os.path.join(tmpdir, f"engineer_{engineer_id}_schedule.csv")
                if os.path.exists(file_path):
                    with open(file_path, "r") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            start = float(row["job_start_time_minutes"])
                            end = float(row["job_end_time_minutes"])
                            duration = float(row["job_duration_minutes"])

                            self.assertAlmostEqual(
                                end,
                                start + duration,
                                places=2,
                                msg=f"Time calculation error: end ({end}) != start ({start}) + duration ({duration})",
                            )

    def test_csv_format(self):
        """Test that CSV files have correct format and data types."""
        scheduler = Scheduler(self.engineers, self.jobs, self.travel_matrix)
        assignments, routes, unassigned = scheduler.create_schedule()

        with tempfile.TemporaryDirectory() as tmpdir:
            generate_report(
                self.engineers, assignments, routes, self.travel_matrix, output_dir=tmpdir
            )

            expected_columns = [
                "engineer_id",
                "engineer_name",
                "job_id",
                "job_location",
                "job_time",
                "required_skills",
                "job_start_time_minutes",
                "job_end_time_minutes",
                "job_duration_minutes",
                "travel_time_minutes",
                "total_time_minutes",
            ]

            for engineer_id in assignments.keys():
                file_path = os.path.join(tmpdir, f"engineer_{engineer_id}_schedule.csv")
                if os.path.exists(file_path):
                    with open(file_path, "r") as f:
                        reader = csv.DictReader(f)
                        columns = reader.fieldnames

                        self.assertEqual(
                            columns,
                            expected_columns,
                            f"CSV columns don't match expected format for engineer {engineer_id}",
                        )

                        # Check data types
                        for row in reader:
                            # Numeric fields should be parseable as float
                            for col in [
                                "job_start_time_minutes",
                                "job_end_time_minutes",
                                "job_duration_minutes",
                                "travel_time_minutes",
                                "total_time_minutes",
                            ]:
                                try:
                                    float(row[col])
                                except ValueError:
                                    self.fail(f"Non-numeric value in {col} for engineer {engineer_id}")


if __name__ == "__main__":
    unittest.main()
