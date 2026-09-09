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
    """Calculate start/end times for jobs based on route order.

    Returns list of job records with timing information in minutes.
    """
    # Create mapping from location to jobs at that location
    location_to_jobs: Dict[str, List[Job]] = {}
    for job in jobs:
        if job.location not in location_to_jobs:
            location_to_jobs[job.location] = []
        location_to_jobs[job.location].append(job)

    # Sort jobs by their scheduled time so the report is chronological
    sorted_jobs = sorted(jobs, key=lambda j: j.time)

    # Build a lookup from each job to its travel time from the previous stop
    # by walking the route in TSP order, then attach those costs to the
    # chronologically-sorted records.
    travel_cost_for_job: Dict[int, float] = {}
    processed_jobs: set[int] = set()
    prev_loc = route[0]  # engineer home
    for i in range(1, len(route) - 1):
        current_loc = route[i]
        travel_hours = travel_matrix.get(prev_loc, {}).get(current_loc, 0.0)
        travel_minutes = travel_hours * 60.0

        if current_loc in location_to_jobs:
            for job in location_to_jobs[current_loc]:
                if job.id in processed_jobs:
                    continue
                processed_jobs.add(job.id)
                travel_cost_for_job[job.id] = travel_minutes
                break

        prev_loc = current_loc

    # Build records in chronological order with cumulative timing
    current_time_minutes = 0.0
    job_records = []

    for job in sorted_jobs:
        travel_minutes = travel_cost_for_job.get(job.id, 0.0)
        current_time_minutes += travel_minutes

        job_start_minutes = current_time_minutes
        job_duration_minutes = job.length * 60.0
        job_end_minutes = job_start_minutes + job_duration_minutes

        job_records.append({
            "job_id": job.id,
            "job_location": job.location,
            "job_time": job.time,
            "required_skills": ",".join(job.required_skills),
            "job_start_time_minutes": job_start_minutes,
            "job_end_time_minutes": job_end_minutes,
            "job_duration_minutes": job_duration_minutes,
            "travel_time_minutes": travel_minutes,
        })

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
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Create engineer lookup
    engineer_lookup = {e.id: e for e in engineers}

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
        if route and travel_matrix:
            job_records = _calculate_job_timings(engineer, jobs, route, travel_matrix)
        else:
            # No route info, create basic records without timing
            job_records = []
            for job in jobs:
                job_records.append({
                    "job_id": job.id,
                    "job_location": job.location,
                    "job_time": job.time,
                    "required_skills": ",".join(job.required_skills),
                    "job_start_time_minutes": 0.0,
                    "job_end_time_minutes": job.length * 60.0,
                    "job_duration_minutes": job.length * 60.0,
                    "travel_time_minutes": 0.0,
                })

        # Write CSV file
        file_path = os.path.join(output_dir, f"engineer_{engineer_id}_schedule.csv")
        with open(file_path, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
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
                ],
            )
            writer.writeheader()

            sum_duration = 0.0
            sum_travel = 0.0
            sum_total = 0.0

            for record in job_records:
                total_time = record["job_duration_minutes"] + record["travel_time_minutes"]
                sum_duration += record["job_duration_minutes"]
                sum_travel += record["travel_time_minutes"]
                sum_total += total_time

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
                    "total_time_minutes": round(total_time, 2),
                })

            writer.writerow({
                "engineer_id": engineer_id,
                "engineer_name": engineer.name,
                "job_id": "TOTAL",
                "job_location": "",
                "job_time": "",
                "required_skills": "",
                "job_start_time_minutes": "",
                "job_end_time_minutes": "",
                "job_duration_minutes": round(sum_duration, 2),
                "travel_time_minutes": round(sum_travel, 2),
                "total_time_minutes": round(sum_total, 2),
            })
