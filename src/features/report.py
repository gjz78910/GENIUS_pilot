"""CSV report generation for job assignments.

Generates per-engineer CSV reports with timing details in minutes.
"""

from __future__ import annotations

import csv
import os
from typing import Any, Dict, List, Tuple

from src.models.engineer import Engineer
from src.models.job import Job


def _calculate_job_timings(
    engineer: Engineer,
    jobs: List[Job],
    route: Tuple[str, ...],
    travel_matrix: Dict[str, Dict[str, float]],
) -> List[Dict[str, Any]]:
    """Calculate start/end times for jobs ordered chronologically by job_time.

    Jobs are sorted by their scheduled time (job.time) and travel time is
    computed sequentially: engineer home -> first job -> second job -> ...

    Returns list of job records with timing information in minutes.
    """
    # Sort jobs by scheduled time (chronological order)
    sorted_jobs = sorted(jobs, key=lambda j: j.time)

    # Track current time in minutes (start at 0 = beginning of day)
    current_time_minutes = 0.0
    current_location = engineer.location
    job_records = []

    for job in sorted_jobs:
        # Travel time from current location to this job (convert hours to minutes)
        travel_hours = travel_matrix.get(current_location, {}).get(job.location, 0.0)
        travel_minutes = travel_hours * 60.0

        # Add travel time to reach the job
        current_time_minutes += travel_minutes

        job_start_minutes = current_time_minutes
        job_duration_minutes = job.length * 60.0
        job_end_minutes = job_start_minutes + job_duration_minutes
        total_time_minutes = job_duration_minutes + travel_minutes

        job_records.append({
            "job_id": job.id,
            "job_location": job.location,
            "job_time": job.time,
            "required_skills": ",".join(job.required_skills),
            "job_start_time_minutes": job_start_minutes,
            "job_end_time_minutes": job_end_minutes,
            "job_duration_minutes": job_duration_minutes,
            "travel_time_minutes": travel_minutes,
            "total_time_minutes": total_time_minutes,
        })

        # Update current location and time after job completion
        current_location = job.location
        current_time_minutes = job_end_minutes

    return job_records


def generate_report(
    engineers: List[Engineer],
    assignments: Dict[int, List[Job]],
    routes: Dict[int, Tuple[Tuple[str, ...], float]] | None = None,
    travel_matrix: Dict[str, Dict[str, float]] | None = None,
    output_dir: str = "reports",
) -> None:
    """Generate per-engineer CSV reports for job assignments.

    Parameters
    ----------
    engineers : List[Engineer]
        List of all engineers (needed for names).
    assignments : Dict[int, List[Job]]
        Mapping from engineer ID to the jobs assigned to that engineer.
    routes : Dict[int, Tuple[Tuple[str, ...], float]], optional
        Mapping from engineer ID to a tuple of (route, total travel time in hours).
        If not provided, routes will be empty.
    travel_matrix : Dict[str, Dict[str, float]], optional
        Travel time matrix (in hours) between locations. Required if routes provided.
    output_dir : str, default "reports"
        Directory where CSV files will be written.

    Notes
    -----
    Each engineer gets a separate CSV file: `{output_dir}/engineer_{id}_schedule.csv`
    with columns: engineer_id, engineer_name, job_id, job_location, job_time,
    required_skills, job_start_time_minutes, job_end_time_minutes, job_duration_minutes,
    travel_time_minutes, total_time_minutes.

    Jobs are ordered chronologically by job_time. A TOTAL summary row is appended
    at the end with aggregate values for duration, travel, and total time.
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Create engineer lookup
    engineer_lookup = {e.id: e for e in engineers}

    fieldnames = [
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

    for engineer_id, jobs in assignments.items():
        if not jobs:
            continue  # Skip engineers with no jobs

        engineer = engineer_lookup.get(engineer_id)
        if not engineer:
            continue

        # Get route for this engineer
        route_info = routes.get(engineer_id) if routes else None
        route = route_info[0] if route_info else ()

        # Calculate job timings
        if travel_matrix:
            job_records = _calculate_job_timings(engineer, jobs, route, travel_matrix)
        else:
            # No travel matrix, create basic records without timing
            sorted_jobs = sorted(jobs, key=lambda j: j.time)
            job_records = []
            for job in sorted_jobs:
                duration = job.length * 60.0
                job_records.append({
                    "job_id": job.id,
                    "job_location": job.location,
                    "job_time": job.time,
                    "required_skills": ",".join(job.required_skills),
                    "job_start_time_minutes": 0.0,
                    "job_end_time_minutes": duration,
                    "job_duration_minutes": duration,
                    "travel_time_minutes": 0.0,
                    "total_time_minutes": duration,
                })

        # Write CSV file
        file_path = os.path.join(output_dir, f"engineer_{engineer_id}_schedule.csv")
        with open(file_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            # Write detail rows
            total_duration = 0.0
            total_travel = 0.0
            total_total = 0.0

            for record in job_records:
                duration = record["job_duration_minutes"]
                travel = record["travel_time_minutes"]
                total = record["total_time_minutes"]

                total_duration += duration
                total_travel += travel
                total_total += total

                writer.writerow({
                    "engineer_id": engineer_id,
                    "engineer_name": engineer.name,
                    "job_id": record["job_id"],
                    "job_location": record["job_location"],
                    "job_time": record["job_time"],
                    "required_skills": record["required_skills"],
                    "job_start_time_minutes": round(record["job_start_time_minutes"], 2),
                    "job_end_time_minutes": round(record["job_end_time_minutes"], 2),
                    "job_duration_minutes": round(duration, 2),
                    "travel_time_minutes": round(travel, 2),
                    "total_time_minutes": round(total, 2),
                })

            # Write TOTAL summary row
            writer.writerow({
                "engineer_id": engineer_id,
                "engineer_name": engineer.name,
                "job_id": "TOTAL",
                "job_location": "",
                "job_time": "",
                "required_skills": "",
                "job_start_time_minutes": "",
                "job_end_time_minutes": "",
                "job_duration_minutes": round(total_duration, 2),
                "travel_time_minutes": round(total_travel, 2),
                "total_time_minutes": round(total_total, 2),
            })
