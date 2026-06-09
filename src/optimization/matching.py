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


def _build_eligibility_map(
    engineers: List[Engineer], jobs: List[Job]
) -> Dict[int, List[Engineer]]:
    """Map each job ID to the list of engineers qualified to perform it.

    An engineer is qualified if they possess ALL of the job's required skills.
    If a job requires no skills, all engineers are eligible.

    Parameters
    ----------
    engineers : List[Engineer]
        The available field engineers.
    jobs : List[Job]
        The jobs that need to be assigned.

    Returns
    -------
    Dict[int, List[Engineer]]
        A mapping from job ID to the list of qualified engineers.
    """
    eligibility: Dict[int, List[Engineer]] = {}
    for job in jobs:
        if not job.required_skills:
            eligibility[job.id] = list(engineers)
        else:
            eligibility[job.id] = [
                engineer
                for engineer in engineers
                if all(skill in engineer.skills for skill in job.required_skills)
            ]
    return eligibility


def _has_capacity(
    engineer: Engineer,
    current_jobs: List[Job],
    new_job: Job,
    travel_matrix: Dict[str, Dict[str, float]],
) -> bool:
    """Check if adding new_job to engineer's current jobs fits within working hours.

    Total load is computed as the sum of all job durations plus the estimated
    travel time for the complete route (including the new job).

    Uses nearest-neighbor routing for fast travel estimation during capacity
    checks. The full optimized route is computed later for final scheduling.

    Parameters
    ----------
    engineer : Engineer
        The engineer to check capacity for.
    current_jobs : List[Job]
        Jobs already assigned to this engineer.
    new_job : Job
        The candidate job to add.
    travel_matrix : Dict[str, Dict[str, float]]
        Travel time matrix between locations.

    Returns
    -------
    bool
        True if the new job fits within the engineer's working hours.
    """
    from src.optimization.routing import nearest_neighbor_tsp

    test_jobs = current_jobs + [new_job]
    total_job_time = sum(j.length for j in test_jobs)

    job_locations = [j.location for j in test_jobs]
    if not job_locations:
        return total_job_time <= engineer.working_hours

    _, estimated_travel = nearest_neighbor_tsp(engineer.location, job_locations, travel_matrix)

    return total_job_time + estimated_travel <= engineer.working_hours


def assign_jobs(
    engineers: List[Engineer], jobs: List[Job], travel_matrix: Dict[str, Dict[str, float]]
) -> tuple[Dict[int, List[Job]], List[Job]]:
    """Assign jobs to engineers based on skills, distance, and capacity.

    Uses a two-pass strategy:
    - Pass 1: Assign exclusive jobs (those with very few qualified engineers) first,
      sorted by most constrained (fewest options) first.
    - Pass 2: Assign remaining jobs greedily by proximity to the closest
      engineer with capacity.

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

    # Step 1: Build eligibility map
    eligibility_map = _build_eligibility_map(engineers, jobs)

    # Immediately classify impossible jobs (no qualified engineer)
    assignable_jobs: List[Job] = []
    for job in jobs:
        if not eligibility_map[job.id]:
            unassigned.append(job)
        else:
            assignable_jobs.append(job)

    # Step 2: Pass 1 — Exclusive assignments (most constrained first)
    exclusivity_threshold = 1
    exclusive_jobs = [
        j for j in assignable_jobs
        if len(eligibility_map[j.id]) <= exclusivity_threshold
    ]
    exclusive_jobs.sort(key=lambda j: len(eligibility_map[j.id]))

    remaining_after_pass1: List[Job] = []
    for job in exclusive_jobs:
        # Sort eligible engineers by distance to job
        candidates = sorted(
            eligibility_map[job.id],
            key=lambda e: travel_matrix.get(e.location, {}).get(job.location, float("inf"))
        )
        assigned = False
        for engineer in candidates:
            if _has_capacity(engineer, assignments[engineer.id], job, travel_matrix):
                assignments[engineer.id].append(job)
                assigned = True
                break
        if not assigned:
            remaining_after_pass1.append(job)

    # Step 3: Pass 2 — Greedy closest-first assignment
    non_exclusive_jobs = [
        j for j in assignable_jobs
        if len(eligibility_map[j.id]) > exclusivity_threshold
    ]
    pass2_jobs = remaining_after_pass1 + non_exclusive_jobs

    for job in pass2_jobs:
        candidates = sorted(
            eligibility_map[job.id],
            key=lambda e: travel_matrix.get(e.location, {}).get(job.location, float("inf"))
        )
        assigned = False
        for engineer in candidates:
            if _has_capacity(engineer, assignments[engineer.id], job, travel_matrix):
                assignments[engineer.id].append(job)
                assigned = True
                break
        if not assigned:
            unassigned.append(job)

    return assignments, unassigned
