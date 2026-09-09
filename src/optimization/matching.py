"""Job-to-engineer assignment logic.

The main entry point is `assign_jobs`, which returns:
- assigned jobs per engineer
- jobs that could not be assigned
"""

from __future__ import annotations

from typing import Dict, List

from src.models.engineer import Engineer
from src.models.job import Job


def _sequential_travel(
    start: str, locations: List[str], travel_matrix: Dict[str, Dict[str, float]]
) -> float:
    """Cheap O(n) travel estimate: drive through locations in given order and return."""
    if not locations:
        return 0.0
    total = travel_matrix.get(start, {}).get(locations[0], float("inf"))
    for i in range(len(locations) - 1):
        total += travel_matrix.get(locations[i], {}).get(locations[i + 1], float("inf"))
    total += travel_matrix.get(locations[-1], {}).get(start, float("inf"))
    return total


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

    Returns
    -------
    tuple[Dict[int, List[Job]], List[Job]]
        A tuple containing:
        - A mapping from engineer ID to the list of jobs assigned to that engineer
        - A list of unassigned jobs
    """
    assignments: Dict[int, List[Job]] = {e.id: [] for e in engineers}
    unassigned: List[Job] = []

    # Process most-constrained jobs first: jobs with fewer capable engineers
    # get priority so exclusive engineers aren't pre-filled by shared-skill jobs.
    def _num_capable(job: Job) -> int:
        return sum(
            1 for e in engineers
            if all(s in e.skills for s in job.required_skills)
        )

    sorted_jobs = sorted(jobs, key=_num_capable)

    for job in sorted_jobs:
        skilled_candidates: List[Engineer] = [
            engineer
            for engineer in engineers
            if all(req_skill in engineer.skills for req_skill in job.required_skills)
        ]
        if not skilled_candidates:
            unassigned.append(job)
            continue

        skilled_candidates.sort(
            key=lambda e: travel_matrix.get(e.location, {}).get(job.location, float("inf"))
        )

        assigned = False
        for engineer in skilled_candidates:
            current_jobs = assignments[engineer.id]
            total_job_time = sum(j.length for j in current_jobs)

            # Use a sequential travel estimate instead of running full TSP on every
            # candidate — this is O(n) vs O(n!) and avoids expensive routing calls
            # during the assignment loop.
            job_locations = [j.location for j in current_jobs] + [job.location]
            estimated_travel_time = _sequential_travel(
                engineer.location, job_locations, travel_matrix
            )

            if total_job_time + job.length + estimated_travel_time <= engineer.working_hours:
                assignments[engineer.id].append(job)
                assigned = True
                break

        if not assigned:
            unassigned.append(job)

    return assignments, unassigned
