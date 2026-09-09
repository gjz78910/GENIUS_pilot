"""Job-to-engineer assignment logic.

The main entry point is `assign_jobs`, which returns:
- assigned jobs per engineer
- jobs that could not be assigned
"""

from __future__ import annotations

from typing import Dict, List

from src.models.engineer import Engineer
from src.models.job import Job
from src.optimization.routing import estimate_route_cost


def _fits_capacity(
    engineer: Engineer,
    jobs: List[Job],
    travel_matrix: Dict[str, Dict[str, float]],
) -> bool:
    """Check whether a list of jobs fits within an engineer's working hours.

    Uses the O(n^2) nearest-neighbor estimate for travel time rather than
    exact routing, since this is a feasibility check called thousands of
    times during matching.
    """
    if not jobs:
        return True
    total_job_time = sum(j.length for j in jobs)
    job_locations = [j.location for j in jobs]
    travel_time = estimate_route_cost(engineer.location, job_locations, travel_matrix)
    return total_job_time + travel_time <= engineer.working_hours


def _skilled_candidates_sorted(
    job: Job,
    engineers: List[Engineer],
    travel_matrix: Dict[str, Dict[str, float]],
) -> List[Engineer]:
    """Return engineers qualified for a job, sorted by distance (closest first)."""
    candidates = [
        e for e in engineers
        if all(skill in e.skills for skill in job.required_skills)
    ]
    candidates.sort(
        key=lambda e: travel_matrix.get(e.location, {}).get(job.location, float("inf"))
    )
    return candidates


def _try_greedy_assign(
    job: Job,
    engineers: List[Engineer],
    assignments: Dict[int, List[Job]],
    travel_matrix: Dict[str, Dict[str, float]],
) -> bool:
    """Try to assign a job to the closest qualified engineer with capacity."""
    for engineer in _skilled_candidates_sorted(job, engineers, travel_matrix):
        if _fits_capacity(engineer, assignments[engineer.id] + [job], travel_matrix):
            assignments[engineer.id].append(job)
            return True
    return False


def _try_backtrack_assign(
    job: Job,
    engineers: List[Engineer],
    engineer_map: Dict[int, Engineer],
    assignments: Dict[int, List[Job]],
    travel_matrix: Dict[str, Dict[str, float]],
) -> bool:
    """Try to assign a job by displacing one existing assignment."""
    for candidate in _skilled_candidates_sorted(job, engineers, travel_matrix):
        current_jobs = assignments[candidate.id]
        for i, existing_job in enumerate(current_jobs):
            # Would swapping existing_job for job fit the candidate?
            replaced_jobs = current_jobs[:i] + current_jobs[i + 1:] + [job]
            if not _fits_capacity(candidate, replaced_jobs, travel_matrix):
                continue

            # Can existing_job be reassigned to a different engineer?
            for other in engineers:
                if other.id == candidate.id:
                    continue
                if not all(s in other.skills for s in existing_job.required_skills):
                    continue
                if _fits_capacity(other, assignments[other.id] + [existing_job], travel_matrix):
                    # Perform the swap
                    assignments[candidate.id] = current_jobs[:i] + current_jobs[i + 1:]
                    assignments[candidate.id].append(job)
                    assignments[other.id].append(existing_job)
                    return True
    return False


def assign_jobs(
    engineers: List[Engineer], jobs: List[Job], travel_matrix: Dict[str, Dict[str, float]]
) -> tuple[Dict[int, List[Job]], List[Job]]:
    """Assign jobs to engineers based on skills, distance, and capacity.

    Uses a greedy closest-first strategy with single-level backtracking:
    when greedy assignment fails, attempts to displace one existing
    assignment to make room.

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
    engineer_map: Dict[int, Engineer] = {e.id: e for e in engineers}
    unassigned: List[Job] = []

    for job in jobs:
        # Step 1: greedy — closest qualified engineer with capacity
        if _try_greedy_assign(job, engineers, assignments, travel_matrix):
            continue

        # Step 2: backtrack — displace one existing job to make room
        if _try_backtrack_assign(job, engineers, engineer_map, assignments, travel_matrix):
            continue

        # Step 3: no option found
        unassigned.append(job)

    return assignments, unassigned
