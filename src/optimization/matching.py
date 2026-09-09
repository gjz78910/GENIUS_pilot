"""Job-to-engineer assignment logic.

The main entry point is `assign_jobs`, which returns:
- assigned jobs per engineer
- jobs that could not be assigned
"""

from __future__ import annotations

from typing import Dict, List

from src.models.engineer import Engineer
from src.models.job import Job


def _nn_travel_estimate(
    start: str, locations: List[str], travel_matrix: Dict[str, Dict[str, float]]
) -> float:
    """Nearest-neighbour travel estimate — O(n²), used for capacity checks."""
    if not locations:
        return 0.0
    n = len(locations)
    visited = [False] * n
    current = start
    total = 0.0
    for _ in range(n):
        row = travel_matrix.get(current, {})
        best_d = float("inf")
        best_i = 0
        for i in range(n):
            if not visited[i]:
                d = row.get(locations[i], float("inf"))
                if d < best_d:
                    best_d = d
                    best_i = i
        total += best_d
        visited[best_i] = True
        current = locations[best_i]
    total += travel_matrix.get(current, {}).get(start, 0.0)
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

    # Cached accumulated job time — avoids O(n) sum recomputation per candidate.
    job_time: Dict[int, float] = {e.id: 0.0 for e in engineers}

    # Frozensets for O(1) skill membership tests instead of O(n) list scan.
    eng_skills: Dict[int, frozenset] = {e.id: frozenset(e.skills) for e in engineers}

    def qualified(e: Engineer, req) -> bool:
        return all(s in eng_skills[e.id] for s in req)

    # Process exclusive-skill jobs first so scarce engineers aren't filled with
    # shared-skill work before the only job they can do gets a chance.
    jobs_sorted = sorted(
        jobs,
        key=lambda j: sum(1 for e in engineers if qualified(e, j.required_skills)),
    )

    for job in jobs_sorted:
        req = job.required_skills
        skilled_candidates: List[Engineer] = [
            e for e in engineers if qualified(e, req)
        ]
        if not skilled_candidates:
            unassigned.append(job)
            continue

        skilled_candidates.sort(
            key=lambda e: travel_matrix.get(e.location, {}).get(job.location, float("inf"))
        )

        assigned = False
        for engineer in skilled_candidates:
            eid = engineer.id
            # Skip expensive travel estimate when job time alone won't fit.
            if job_time[eid] + job.length > engineer.working_hours:
                continue

            current_locs = [j.location for j in assignments[eid]] + [job.location]
            estimated_travel = _nn_travel_estimate(
                engineer.location, current_locs, travel_matrix
            )
            if job_time[eid] + job.length + estimated_travel <= engineer.working_hours:
                assignments[eid].append(job)
                job_time[eid] += job.length
                assigned = True
                break

        if not assigned:
            unassigned.append(job)

    return assignments, unassigned
