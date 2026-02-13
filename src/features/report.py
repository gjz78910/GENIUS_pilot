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
    """Calculate per-job timing fields in chronological job order.

    Returns list of job records with timing information in minutes.
    """
    del route  # Route can be optimal for travel but report requires chronological rows.

    # Chronological order is required by report correctness tests.
    def sort_key(job: Job) -> Tuple[int, int]:
        try:
            hours, minutes = job.time.split(":", 1)
            as_minutes = int(hours) * 60 + int(minutes)
        except Exception:
            as_minutes = 24 * 60
        return as_minutes, job.id

    ordered_jobs = sorted(jobs, key=sort_key)

    current_time_minutes = 0.0
    previous_location = engineer.location
    job_records: List[Dict[str, Any]] = []

    for job in ordered_jobs:
        travel_hours = travel_matrix.get(previous_location, {}).get(job.location, 0.0)
        travel_minutes = travel_hours * 60.0
        job_start_minutes = current_time_minutes + travel_minutes
        job_duration_minutes = job.length * 60.0
        job_end_minutes = job_start_minutes + job_duration_minutes
        total_time_minutes = job_duration_minutes + travel_minutes

        job_records.append(
            {
                "job_id": job.id,
                "job_location": job.location,
                "job_time": job.time,
                "required_skills": ",".join(job.required_skills),
                "job_start_time_minutes": job_start_minutes,
                "job_end_time_minutes": job_end_minutes,
                "job_duration_minutes": job_duration_minutes,
                "travel_time_minutes": travel_minutes,
                "total_time_minutes": total_time_minutes,
            }
        )

        current_time_minutes = job_end_minutes
        previous_location = job.location

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
            # No route info, still create rows chronologically with local travel.
            job_records = []
            current_time_minutes = 0.0
            previous_location = engineer.location
            for job in sorted(jobs, key=lambda value: (value.time, value.id)):
                travel_minutes = (
                    travel_matrix.get(previous_location, {}).get(job.location, 0.0) * 60.0
                    if travel_matrix
                    else 0.0
                )
                start_minutes = current_time_minutes + travel_minutes
                duration_minutes = job.length * 60.0
                end_minutes = start_minutes + duration_minutes
                total_minutes = duration_minutes + travel_minutes
                job_records.append({
                    "job_id": job.id,
                    "job_location": job.location,
                    "job_time": job.time,
                    "required_skills": ",".join(job.required_skills),
                    "job_start_time_minutes": start_minutes,
                    "job_end_time_minutes": end_minutes,
                    "job_duration_minutes": duration_minutes,
                    "travel_time_minutes": travel_minutes,
                    "total_time_minutes": total_minutes,
                })
                current_time_minutes = end_minutes
                previous_location = job.location

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

            total_duration = 0.0
            total_travel = 0.0
            total_total = 0.0
            for record in job_records:
                row_duration = float(record["job_duration_minutes"])
                row_travel = float(record["travel_time_minutes"])
                row_total = float(record.get("total_time_minutes", row_duration + row_travel))
                total_duration += row_duration
                total_travel += row_travel
                total_total += row_total
                writer.writerow({
                    "engineer_id": engineer_id,
                    "engineer_name": engineer.name,
                    "job_id": record["job_id"],
                    "job_location": record["job_location"],
                    "job_time": record["job_time"],
                    "required_skills": record["required_skills"],
                    "job_start_time_minutes": round(record["job_start_time_minutes"], 2),
                    "job_end_time_minutes": round(record["job_end_time_minutes"], 2),
                    "job_duration_minutes": round(row_duration, 2),
                    "travel_time_minutes": round(row_travel, 2),
                    "total_time_minutes": round(row_total, 2),
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
                "job_duration_minutes": round(total_duration, 2),
                "travel_time_minutes": round(total_travel, 2),
                "total_time_minutes": round(total_total, 2),
            })
