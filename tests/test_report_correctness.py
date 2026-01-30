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
                    rows = [r for r in reader if r["job_id"] != "TOTAL"]

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

                    job_rows = [r for r in rows if r["job_id"] != "TOTAL"]
                    if job_rows:
                        # Find last job end time
                        last_end_time = max(float(row["job_end_time_minutes"]) for row in job_rows)
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
                    reported_job_ids = {int(row["job_id"]) for row in reader if row["job_id"] != "TOTAL"}

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
                        job_ids = [int(row["job_id"]) for row in reader if row["job_id"] != "TOTAL"]

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
                            if row["job_id"] == "TOTAL":
                                continue
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
                            if row["job_id"] == "TOTAL":
                                continue
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


    def test_travel_time_between_jobs(self):
        """Test that travel_time_minutes > 0 when consecutive jobs are at different locations."""
        # Use a setup where one engineer has jobs at multiple locations
        engineers = [
            Engineer(id=1, name="Alice", location="A", skills=["repair", "install"], working_hours=8.0),
        ]
        jobs = [
            Job(id=1, location="A", time="09:00", required_skills=["repair"], length=1.0),
            Job(id=2, location="B", time="10:00", required_skills=["install"], length=1.0),
        ]
        scheduler = Scheduler(engineers, jobs, self.travel_matrix)
        assignments, routes, unassigned = scheduler.create_schedule()

        # Verify Alice got both jobs at different locations
        self.assertIn(1, assignments)
        self.assertEqual(len(assignments[1]), 2)

        with tempfile.TemporaryDirectory() as tmpdir:
            generate_report(
                engineers, assignments, routes, self.travel_matrix, output_dir=tmpdir
            )

            file_path = os.path.join(tmpdir, "engineer_1_schedule.csv")
            self.assertTrue(os.path.exists(file_path))

            with open(file_path, "r") as f:
                reader = csv.DictReader(f)
                rows = [r for r in reader if r["job_id"] != "TOTAL"]

            # At least one row should have travel_time > 0
            travel_times = [float(row["travel_time_minutes"]) for row in rows]
            self.assertTrue(
                any(t > 0 for t in travel_times),
                f"Engineer has jobs at A and B but all travel_time_minutes are 0: {travel_times}",
            )

    def test_total_time_is_duration_plus_travel(self):
        """Test that total_time_minutes = job_duration_minutes + travel_time_minutes."""
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
                            if row["job_id"] == "TOTAL":
                                continue
                            duration = float(row["job_duration_minutes"])
                            travel = float(row["travel_time_minutes"])
                            total = float(row["total_time_minutes"])

                            self.assertAlmostEqual(
                                total,
                                duration + travel,
                                places=2,
                                msg=f"Engineer {engineer_id}, job {row['job_id']}: "
                                f"total ({total}) != duration ({duration}) + travel ({travel})",
                            )

    def test_summary_row(self):
        """Test that each CSV ends with a TOTAL summary row with correct aggregates."""
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
                self.assertTrue(os.path.exists(file_path))

                with open(file_path, "r") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)

                # Last row should be the summary
                self.assertGreater(len(rows), 0, f"No rows for engineer {engineer_id}")
                summary = rows[-1]
                self.assertEqual(
                    summary["job_id"],
                    "TOTAL",
                    f"Last row for engineer {engineer_id} should have job_id='TOTAL'",
                )

                # Verify aggregates match sum of detail rows
                detail_rows = rows[:-1]
                expected_duration = sum(float(r["job_duration_minutes"]) for r in detail_rows)
                expected_travel = sum(float(r["travel_time_minutes"]) for r in detail_rows)
                expected_total = sum(float(r["total_time_minutes"]) for r in detail_rows)

                self.assertAlmostEqual(
                    float(summary["job_duration_minutes"]),
                    expected_duration,
                    places=2,
                    msg=f"Summary duration mismatch for engineer {engineer_id}",
                )
                self.assertAlmostEqual(
                    float(summary["travel_time_minutes"]),
                    expected_travel,
                    places=2,
                    msg=f"Summary travel mismatch for engineer {engineer_id}",
                )
                self.assertAlmostEqual(
                    float(summary["total_time_minutes"]),
                    expected_total,
                    places=2,
                    msg=f"Summary total mismatch for engineer {engineer_id}",
                )


    def test_jobs_ordered_by_time(self):
        """Test that jobs in the CSV are ordered by job_time (chronological)."""
        # Travel matrix where TSP route D->B->A->C->D is optimal (distance 4.0)
        # but job_time order is A(09:00), B(10:00), C(11:00)
        # So TSP visits B(10:00) before A(09:00) — violating chronological order
        travel_matrix = {
            "A": {"A": 0.0, "B": 1.0, "C": 1.0, "D": 5.0},
            "B": {"A": 1.0, "B": 0.0, "C": 5.0, "D": 1.0},
            "C": {"A": 1.0, "B": 5.0, "C": 0.0, "D": 1.0},
            "D": {"A": 5.0, "B": 1.0, "C": 1.0, "D": 0.0},
        }
        engineers = [
            Engineer(
                id=1, name="Alice", location="D",
                skills=["repair", "install", "maintain"], working_hours=12.0,
            ),
        ]
        jobs = [
            Job(id=1, location="A", time="09:00", required_skills=["repair"], length=1.0),
            Job(id=2, location="B", time="10:00", required_skills=["install"], length=1.0),
            Job(id=3, location="C", time="11:00", required_skills=["maintain"], length=1.0),
        ]
        scheduler = Scheduler(engineers, jobs, travel_matrix)
        assignments, routes, unassigned = scheduler.create_schedule()

        self.assertEqual(len(assignments[1]), 3, "Alice should get all 3 jobs")

        with tempfile.TemporaryDirectory() as tmpdir:
            generate_report(
                engineers, assignments, routes, travel_matrix, output_dir=tmpdir
            )

            file_path = os.path.join(tmpdir, "engineer_1_schedule.csv")
            self.assertTrue(os.path.exists(file_path))

            with open(file_path, "r") as f:
                reader = csv.DictReader(f)
                rows = [r for r in reader if r["job_id"] != "TOTAL"]

            # Jobs should be ordered by job_time (chronological)
            job_times = [row["job_time"] for row in rows]
            self.assertEqual(
                job_times,
                sorted(job_times),
                f"Jobs should be in chronological order by job_time, got: {job_times}",
            )


if __name__ == "__main__":
    unittest.main()
