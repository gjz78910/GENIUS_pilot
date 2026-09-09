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
    # Initialise assignment mapping with empty lists for each engineer
    assignments: Dict[int, List[Job]] = {e.id: [] for e in engineers}
    unassigned: List[Job] = []

    # Process jobs with fewer qualified engineers first so exclusive-skill jobs
    # are not blocked by engineers who could have handled a shared-skill job instead.
    def _num_skilled(job: Job) -> int:
        return sum(
            1 for e in engineers
            if all(s in e.skills for s in job.required_skills)
        )

    for job in sorted(jobs, key=_num_skilled):
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

        # Score every qualified candidate and pick the best fit with available capacity.
        # Score = estimated_travel_time_with_job + current_job_load (both in hours).
        # This balances travel efficiency against workload distribution: an engineer
        # who is already heavily loaded is penalised even if they are geographically close.
        best_engineer: Engineer | None = None
        best_score: float = float("inf")

        for engineer in skilled_candidates:
            current_jobs = assignments[engineer.id]
            current_load = sum(j.length for j in current_jobs)
            job_locations = [j.location for j in current_jobs] + [job.location]
            _, estimated_travel_time = find_optimal_route(engineer.location, job_locations, travel_matrix)

            if current_load + job.length + estimated_travel_time <= engineer.working_hours:
                score = estimated_travel_time + current_load
                if score < best_score:
                    best_score = score
                    best_engineer = engineer

        if best_engineer is not None:
            assignments[best_engineer.id].append(job)
        else:
            unassigned.append(job)

    return assignments, unassigned
