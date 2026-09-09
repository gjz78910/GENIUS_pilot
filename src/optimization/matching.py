"""Job-to-engineer assignment logic.

The main entry point is `assign_jobs`, which returns:
- assigned jobs per engineer
- jobs that could not be assigned
"""

from __future__ import annotations

from typing import Dict, List

from src.models.engineer import Engineer
from src.models.job import Job
from src.optimization.routing import nearest_neighbor_tsp


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

    # Process most-constrained jobs first (fewest capable engineers) to avoid
    # rare-skill jobs being left unassigned because all capable engineers filled up.
    def skill_match_count(job: Job) -> int:
        return sum(
            1 for e in engineers
            if all(s in e.skills for s in job.required_skills)
        )

    sorted_jobs = sorted(jobs, key=skill_match_count)

    for job in sorted_jobs:
        skilled_candidates: List[Engineer] = [
            engineer
            for engineer in engineers
            if all(req_skill in engineer.skills for req_skill in job.required_skills)
        ]
        if not skilled_candidates:
            unassigned.append(job)
            continue

        # Sort by direct distance to the job location as a first-pass proximity filter
        def distance_fn(engineer: Engineer) -> float:
            return travel_matrix.get(engineer.location, {}).get(job.location, float("inf"))

        skilled_candidates.sort(key=distance_fn)

        assigned = False
        for engineer in skilled_candidates:
            current_jobs = assignments[engineer.id]
            total_job_time = sum(j.length for j in current_jobs)

            # Cheap pre-check: if job time alone won't fit, skip the expensive TSP call
            if total_job_time + job.length > engineer.working_hours:
                continue

            # One-way travel estimate: the working day ends at the last job,
            # not back at the engineer's base, so return_to_start=False.
            test_locations = [j.location for j in current_jobs] + [job.location]
            _, estimated_travel_time = nearest_neighbor_tsp(
                engineer.location, test_locations, travel_matrix, return_to_start=False
            )

            if total_job_time + job.length + estimated_travel_time <= engineer.working_hours:
                assignments[engineer.id].append(job)
                assigned = True
                break

        if not assigned:
            unassigned.append(job)

    return assignments, unassigned
