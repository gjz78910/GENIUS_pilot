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


def _estimate_travel_with_job(
    engineer_location: str,
    current_jobs: List[Job],
    new_job: Job,
    travel_matrix: Dict[str, Dict[str, float]],
) -> float:
    """Estimate total travel time if a new job is added using cheapest insertion.

    Returns the estimated total route travel (not just the marginal increase).
    This is a fast O(n) heuristic that slightly overestimates, making it
    conservative for capacity checks.
    """
    if not current_jobs:
        return (
            travel_matrix[engineer_location][new_job.location]
            + travel_matrix[new_job.location][engineer_location]
        )

    # Build current route: engineer -> jobs in order -> engineer
    stops = [engineer_location] + [j.location for j in current_jobs] + [engineer_location]

    # Current total travel
    current_travel = sum(
        travel_matrix[stops[i]][stops[i + 1]] for i in range(len(stops) - 1)
    )

    # Find cheapest insertion position
    best_increase = float("inf")
    for i in range(len(stops) - 1):
        increase = (
            travel_matrix[stops[i]][new_job.location]
            + travel_matrix[new_job.location][stops[i + 1]]
            - travel_matrix[stops[i]][stops[i + 1]]
        )
        if increase < best_increase:
            best_increase = increase

    return current_travel + best_increase


def assign_jobs(
    engineers: List[Engineer], jobs: List[Job], travel_matrix: Dict[str, Dict[str, float]]
) -> tuple[Dict[int, List[Job]], List[Job]]:
    """Assign jobs to engineers based on skills, distance, and capacity.

    Strategy:
    1. Sort jobs by scarcity (fewest qualified engineers first) to avoid
       the exclusive-skill trap where greedy fills capacity with shared jobs.
    2. Use a fast insertion-cost estimate for capacity checks during the
       main assignment loop (O(n) per check, good enough for scalability).
    3. Validate with the actual optimised route and shed overcommitted jobs.
    4. Retry shed/unassigned jobs with accurate routing.

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

    engineer_by_id: Dict[int, Engineer] = {e.id: e for e in engineers}

    # Pre-compute candidate count per job for scarcity sorting
    candidate_counts: Dict[int, int] = {}
    for job in jobs:
        candidate_counts[job.id] = sum(
            1 for e in engineers
            if all(s in e.skills for s in job.required_skills)
        )

    # Sort jobs by scarcity (fewest candidates first)
    sorted_jobs = sorted(jobs, key=lambda j: candidate_counts[j.id])

    # Main assignment pass with cheap insertion estimate
    for job in sorted_jobs:
        skilled_candidates: List[Engineer] = [
            engineer
            for engineer in engineers
            if all(req_skill in engineer.skills for req_skill in job.required_skills)
        ]
        if not skilled_candidates:
            unassigned.append(job)
            continue

        def distance_fn(engineer: Engineer) -> float:
            return travel_matrix.get(engineer.location, {}).get(job.location, float("inf"))

        skilled_candidates.sort(key=distance_fn)

        assigned = False
        for engineer in skilled_candidates:
            current_jobs = assignments[engineer.id]
            total_job_time = sum(j.length for j in current_jobs) + job.length

            # Fast capacity check using insertion estimate
            estimated_travel = _estimate_travel_with_job(
                engineer.location, current_jobs, job, travel_matrix
            )

            if total_job_time + estimated_travel <= engineer.working_hours:
                assignments[engineer.id].append(job)
                assigned = True
                break

        if not assigned:
            unassigned.append(job)

    # Validation pass: check actual routes and shed overcommitted jobs
    for engineer in engineers:
        current_jobs = assignments[engineer.id]
        if not current_jobs:
            continue

        job_locations = [j.location for j in current_jobs]
        _, actual_travel = find_optimal_route(
            engineer.location, job_locations, travel_matrix
        )
        total_job_time = sum(j.length for j in current_jobs)

        # If within capacity, nothing to shed
        if total_job_time + actual_travel <= engineer.working_hours:
            continue

        # Shed jobs from the end (least-scarce jobs were added last due to sorting)
        # until we fit within capacity
        while current_jobs and total_job_time + actual_travel > engineer.working_hours:
            shed_job = current_jobs.pop()
            unassigned.append(shed_job)
            total_job_time = sum(j.length for j in current_jobs)
            if current_jobs:
                job_locations = [j.location for j in current_jobs]
                _, actual_travel = find_optimal_route(
                    engineer.location, job_locations, travel_matrix
                )
            else:
                actual_travel = 0.0

    # Retry pass: try to place unassigned jobs using actual routing
    if unassigned:
        still_unassigned: List[Job] = []
        # Re-sort by scarcity
        unassigned.sort(key=lambda j: candidate_counts.get(j.id, 0))

        for job in unassigned:
            skilled_candidates = [
                e for e in engineers
                if all(s in e.skills for s in job.required_skills)
            ]
            if not skilled_candidates:
                still_unassigned.append(job)
                continue

            def dist_fn(engineer: Engineer) -> float:
                return travel_matrix.get(engineer.location, {}).get(job.location, float("inf"))

            skilled_candidates.sort(key=dist_fn)

            assigned = False
            for engineer in skilled_candidates:
                current_jobs = assignments[engineer.id]
                total_job_time = sum(j.length for j in current_jobs) + job.length

                test_locations = [j.location for j in current_jobs] + [job.location]
                _, actual_travel = find_optimal_route(
                    engineer.location, test_locations, travel_matrix
                )

                if total_job_time + actual_travel <= engineer.working_hours:
                    assignments[engineer.id].append(job)
                    assigned = True
                    break

            if not assigned:
                still_unassigned.append(job)

        unassigned = still_unassigned

    return assignments, unassigned
