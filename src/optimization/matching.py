"""Job-to-engineer assignment logic.

The main entry point is `assign_jobs`, which returns:
- assigned jobs per engineer
- jobs that could not be assigned

Jobs are prioritised before assignment so that harder-to-place jobs
(fewer qualified engineers, more skill requirements, longer duration)
are assigned first while capacity is most available.

Performance strategy:
- During the greedy matching loop, use a cheap O(n) travel estimate
  (nearest-neighbor without 2-opt) to keep the inner loop fast.
- Full route optimisation happens only once per engineer at the end
  via the scheduler's route computation.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from src.models.engineer import Engineer
from src.models.job import Job


def _cheap_travel_estimate(
    start: str,
    job_locations: List[str],
    travel_matrix: Dict[str, Dict[str, float]],
) -> float:
    """Fast O(n) travel estimate using nearest-neighbor (no 2-opt).

    This is used during the matching loop where we need thousands of
    quick capacity checks. It slightly overestimates compared to
    the optimal route, which is conservative (avoids over-filling).
    """
    if not job_locations:
        return 0.0

    total = 0.0
    current = start
    remaining = list(job_locations)

    while remaining:
        # Find nearest unvisited
        best_idx = 0
        best_dist = travel_matrix[current][remaining[0]]
        for idx in range(1, len(remaining)):
            d = travel_matrix[current][remaining[idx]]
            if d < best_dist:
                best_dist = d
                best_idx = idx
        total += best_dist
        current = remaining[best_idx]
        # Swap-remove for O(1) removal
        remaining[best_idx] = remaining[-1]
        remaining.pop()

    # Return to start
    total += travel_matrix[current][start]
    return total


def _count_qualified_engineers(job: Job, engineer_skill_sets: Dict[int, frozenset]) -> int:
    """Count how many engineers are qualified to perform a job."""
    required = frozenset(job.required_skills)
    return sum(1 for skills in engineer_skill_sets.values() if required <= skills)


def _job_priority_key(job: Job, engineer_skill_sets: Dict[int, frozenset]) -> tuple:
    """Compute a sorting key that places hardest-to-assign jobs first.

    Priority criteria (ascending sort, so lower = higher priority):
    1. Fewer qualified engineers → harder to place, assign first.
    2. More required skills → more constrained, assign first.
    3. Longer duration → consumes more capacity, assign first.
    """
    qualified_count = _count_qualified_engineers(job, engineer_skill_sets)
    return (qualified_count, -len(job.required_skills), -job.length)


def assign_jobs(
    engineers: List[Engineer], jobs: List[Job], travel_matrix: Dict[str, Dict[str, float]]
) -> tuple[Dict[int, List[Job]], List[Job]]:
    """Assign jobs to engineers based on skills, distance, and capacity.

    Jobs are processed in priority order: hardest-to-assign jobs (fewest
    qualified engineers, most skills required, longest duration) are
    assigned first to reduce the chance of leaving them unassigned.

    Uses a fast nearest-neighbor travel estimate during matching to keep
    the assignment loop efficient for large inputs.

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
    # Initialise assignment mapping with empty lists for each engineer
    assignments: Dict[int, List[Job]] = {e.id: [] for e in engineers}
    unassigned: List[Job] = []

    # Pre-compute skill sets for faster lookup
    engineer_skill_sets: Dict[int, frozenset] = {
        e.id: frozenset(e.skills) for e in engineers
    }

    # Track cumulative job time per engineer to avoid recomputing
    engineer_job_time: Dict[int, float] = {e.id: 0.0 for e in engineers}

    # Sort jobs by priority: hardest-to-assign first
    prioritised_jobs = sorted(
        jobs, key=lambda job: _job_priority_key(job, engineer_skill_sets)
    )

    for job in prioritised_jobs:
        required = frozenset(job.required_skills)

        # Filter engineers who possess all required skills
        skilled_candidates: List[Engineer] = [
            engineer
            for engineer in engineers
            if required <= engineer_skill_sets[engineer.id]
        ]
        if not skilled_candidates:
            unassigned.append(job)
            continue

        # Sort by distance to find closest available engineer with capacity
        skilled_candidates.sort(
            key=lambda eng: travel_matrix.get(eng.location, {}).get(job.location, float("inf"))
        )

        # Try to assign to the closest engineer with available capacity
        assigned = False
        for engineer in skilled_candidates:
            current_jobs = assignments[engineer.id]
            total_job_time = engineer_job_time[engineer.id] + job.length

            # Quick capacity pre-check: if job time alone exceeds hours, skip
            if total_job_time > engineer.working_hours:
                continue

            # Estimate travel time with the new job included
            job_locations = [j.location for j in current_jobs] + [job.location]
            estimated_travel = _cheap_travel_estimate(
                engineer.location, job_locations, travel_matrix
            )

            if total_job_time + estimated_travel <= engineer.working_hours:
                assignments[engineer.id].append(job)
                engineer_job_time[engineer.id] = total_job_time
                assigned = True
                break

        if not assigned:
            unassigned.append(job)

    # --- Reassignment pass (lightweight) ---
    # Try to rescue unassigned jobs via direct insertion only.
    # Skip expensive displacement/swap for large instances.
    still_unassigned: List[Job] = []
    for job in unassigned:
        rescued = False
        required = frozenset(job.required_skills)

        for engineer in engineers:
            if not required <= engineer_skill_sets[engineer.id]:
                continue

            current_jobs = assignments[engineer.id]
            total_job_time = engineer_job_time[engineer.id] + job.length

            if total_job_time > engineer.working_hours:
                continue

            job_locations = [j.location for j in current_jobs] + [job.location]
            estimated_travel = _cheap_travel_estimate(
                engineer.location, job_locations, travel_matrix
            )

            if total_job_time + estimated_travel <= engineer.working_hours:
                assignments[engineer.id].append(job)
                engineer_job_time[engineer.id] = total_job_time
                rescued = True
                break

        if not rescued:
            still_unassigned.append(job)

    return assignments, still_unassigned
