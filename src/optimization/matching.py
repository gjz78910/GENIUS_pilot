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
    unassigned: List[Job] = []

    def candidate_count(job: Job) -> int:
        return sum(
            1 for e in engineers
            if all(s in e.skills for s in job.required_skills)
        )

    # Most constrained jobs first — prevents generalists being consumed by
    # jobs that other engineers could have handled.
    sorted_jobs = sorted(jobs, key=candidate_count)

    for job in sorted_jobs:
        # Filter engineers who possess all required skills
        skilled_candidates: List[Engineer] = [
            engineer
            for engineer in engineers
            if all(req_skill in engineer.skills for req_skill in job.required_skills)
        ]
        if not skilled_candidates:
            # No engineer has the required skills; mark as unassigned
            unassigned.append(job)
            continue

        best_engineer: Engineer | None = None
        best_score: tuple[float, float] = (float("inf"), float("inf"))

        for engineer in skilled_candidates:
            current_jobs = assignments[engineer.id]
            total_job_time = sum(j.length for j in current_jobs)

            # Pre-filter: skip routing if job time alone already exceeds capacity.
            if total_job_time + job.length > engineer.working_hours:
                continue

            job_locations = [j.location for j in current_jobs + [job]]
            _, travel_time = find_optimal_route(engineer.location, job_locations, travel_matrix)

            total_time = total_job_time + job.length + travel_time
            if total_time > engineer.working_hours:
                continue

            # Primary: minimise travel (proximity). Secondary: minimise remaining
            # capacity (tightest fit) so high-capacity engineers stay free for
            # larger future jobs.
            remaining = engineer.working_hours - total_time
            score = (travel_time, remaining)
            if score < best_score:
                best_score = score
                best_engineer = engineer

        if best_engineer is not None:
            assignments[best_engineer.id].append(job)
        else:
            unassigned.append(job)

    return assignments, unassigned
