"""Job-to-engineer assignment logic.

The main entry point is `assign_jobs`, which returns:
- assigned jobs per engineer
- jobs that could not be assigned
"""

from __future__ import annotations

from typing import Dict, List

from src.models.engineer import Engineer
from src.models.job import Job
from src.optimization.routing import find_optimal_route


def assign_jobs(
    engineers: List[Engineer], jobs: List[Job], travel_matrix: Dict[str, Dict[str, float]]
) -> tuple[Dict[int, List[Job]], List[Job]]:
    """Assign jobs to engineers based on skills, distance, and capacity.

    Parameters
    ----------
    engineers : List[Engineer]
        The available field engineers.
    jobs : List[Job]
        The jobs that need to be assigned.
    travel_matrix : Dict[str, Dict[str, float]]
        A dictionary representing the travel time (in hours) between locations.
        The outer keys are starting locations and the inner keys are
        destination locations.

    Returns
    -------
    tuple[Dict[int, List[Job]], List[Job]]
        A tuple containing:
        - A mapping from engineer ID to the list of jobs assigned to that engineer
        - A list of unassigned jobs
    """
    assignments: Dict[int, List[Job]] = {e.id: [] for e in engineers}
    # Cached running totals to avoid recomputing sums on every iteration
    job_time_totals: Dict[int, float] = {e.id: 0.0 for e in engineers}
    # Current travel time per engineer; monotonically non-decreasing as jobs are added,
    # so it serves as a lower bound for any future routing check.
    current_travel: Dict[int, float] = {e.id: 0.0 for e in engineers}
    unassigned: List[Job] = []

    # Process most-constrained jobs first: jobs with fewest qualified engineers are
    # assigned before shared-skill jobs, avoiding the exclusive-skill trap where a
    # generalist engineer's capacity is consumed before the job only they can do.
    def _count_qualified(job: Job) -> int:
        return sum(1 for e in engineers if all(s in e.skills for s in job.required_skills))

    ordered_jobs = sorted(jobs, key=_count_qualified)

    for job in ordered_jobs:
        skilled_candidates: List[Engineer] = [
            e for e in engineers
            if all(s in e.skills for s in job.required_skills)
        ]
        if not skilled_candidates:
            unassigned.append(job)
            continue

        skilled_candidates.sort(
            key=lambda e: travel_matrix.get(e.location, {}).get(job.location, float("inf"))
        )

        assigned = False
        for engineer in skilled_candidates:
            accumulated_job_time = job_time_totals[engineer.id]

            # Fast pre-filter 1: job durations alone exceed capacity — skip routing entirely
            if accumulated_job_time + job.length > engineer.working_hours:
                continue

            # Fast pre-filter 2: even with current (minimum) travel already in use, no room
            if accumulated_job_time + job.length + current_travel[engineer.id] > engineer.working_hours:
                continue

            job_locations = [j.location for j in assignments[engineer.id]] + [job.location]
            _, estimated_travel_time = find_optimal_route(engineer.location, job_locations, travel_matrix)

            if accumulated_job_time + job.length + estimated_travel_time <= engineer.working_hours:
                assignments[engineer.id].append(job)
                job_time_totals[engineer.id] += job.length
                current_travel[engineer.id] = estimated_travel_time
                assigned = True
                break

        if not assigned:
            unassigned.append(job)

    return assignments, unassigned
