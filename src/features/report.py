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
    """Calculate start/end times for jobs in chronological (job_time) order.

    Jobs are sorted by their scheduled time and visited sequentially; travel
    time between each consecutive pair of stops is taken directly from the
    travel matrix.
    """
    sorted_jobs = sorted(jobs, key=lambda j: j.time)

    current_time_minutes = 0.0
    prev_location = engineer.location
    job_records = []

    for job in sorted_jobs:
        travel_hours = travel_matrix.get(prev_location, {}).get(job.location, 0.0)
        travel_minutes = travel_hours * 60.0
        current_time_minutes += travel_minutes

        job_start = current_time_minutes
        job_duration = job.length * 60.0
        job_end = job_start + job_duration

        job_records.append({
            "job_id": job.id,
            "job_location": job.location,
            "job_time": job.time,
            "required_skills": ",".join(job.required_skills),
            "job_start_time_minutes": job_start,
            "job_end_time_minutes": job_end,
            "job_duration_minutes": job_duration,
            "travel_time_minutes": travel_minutes,
        })

        current_time_minutes = job_end
        prev_location = job.location

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
    The last row of each file is a TOTAL summary aggregating duration, travel, and total time.
    """
    os.makedirs(output_dir, exist_ok=True)

    engineer_lookup = {e.id: e for e in engineers}

    for engineer_id, jobs in assignments.items():
        if not jobs:
            continue

        engineer = engineer_lookup.get(engineer_id)
        if not engineer:
            continue

        route_info = routes.get(engineer_id) if routes else None
        route = route_info[0] if route_info else ()

        if route and travel_matrix:
            job_records = _calculate_job_timings(engineer, jobs, route, travel_matrix)
        else:
            # No route info — assign sequential timings in job_time order, no travel
            current_time = 0.0
            job_records = []
            for job in sorted(jobs, key=lambda j: j.time):
                duration = job.length * 60.0
                job_records.append({
                    "job_id": job.id,
                    "job_location": job.location,
                    "job_time": job.time,
                    "required_skills": ",".join(job.required_skills),
                    "job_start_time_minutes": current_time,
                    "job_end_time_minutes": current_time + duration,
                    "job_duration_minutes": duration,
                    "travel_time_minutes": 0.0,
                })
                current_time += duration

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

        file_path = os.path.join(output_dir, f"engineer_{engineer_id}_schedule.csv")
        with open(file_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            total_duration = 0.0
            total_travel = 0.0
            total_time_sum = 0.0

            for record in job_records:
                row_total = record["travel_time_minutes"] + record["job_duration_minutes"]
                total_duration += record["job_duration_minutes"]
                total_travel += record["travel_time_minutes"]
                total_time_sum += row_total

                writer.writerow({
                    "engineer_id": engineer_id,
                    "engineer_name": engineer.name,
                    "job_id": record["job_id"],
                    "job_location": record["job_location"],
                    "job_time": record["job_time"],
                    "required_skills": record["required_skills"],
                    "job_start_time_minutes": round(record["job_start_time_minutes"], 2),
                    "job_end_time_minutes": round(record["job_end_time_minutes"], 2),
                    "job_duration_minutes": round(record["job_duration_minutes"], 2),
                    "travel_time_minutes": round(record["travel_time_minutes"], 2),
                    "total_time_minutes": round(row_total, 2),
                })

            # Summary row
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
                "total_time_minutes": round(total_time_sum, 2),
            })
