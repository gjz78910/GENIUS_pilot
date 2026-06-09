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

    # Sort jobs by constraint degree (most-constrained-first).
    # Jobs with fewer qualified engineers are assigned first so that
    # exclusive-skill jobs don't get starved by shared-skill jobs.
    def _num_qualified(job: Job) -> int:
        return sum(
            1 for e in engineers
            if all(skill in e.skills for skill in job.required_skills)
        )

    sorted_jobs = sorted(jobs, key=_num_qualified)

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

        # Sort by distance to find closest available engineer with capacity
        def distance_fn(engineer: Engineer) -> float:
            return travel_matrix.get(engineer.location, {}).get(job.location, float("inf"))

        skilled_candidates.sort(key=distance_fn)
        
        # Try to assign to the closest engineer with available capacity
        assigned = False
        for engineer in skilled_candidates:
            current_jobs = assignments[engineer.id]
            total_job_time = sum(j.length for j in current_jobs)
            
            # Estimate travel time if this job is added
            test_jobs = current_jobs + [job]
            job_locations = [j.location for j in test_jobs]
            _, estimated_travel_time = find_optimal_route(engineer.location, job_locations, travel_matrix)
            
            # Check whether total work fits within working hours
            if total_job_time + job.length + estimated_travel_time <= engineer.working_hours:
                assignments[engineer.id].append(job)
                assigned = True
                break
        
        if not assigned:
            unassigned.append(job)

    return assignments, unassigned
