"""Job-to-engineer assignment logic.

The main entry point is `assign_jobs`, which returns:
- assigned jobs per engineer
- jobs that could not be assigned
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

from src.models.engineer import Engineer
from src.models.job import Job


def _distance(a: str, b: str, travel_matrix: Dict[str, Dict[str, float]]) -> float:
    return travel_matrix.get(a, {}).get(b, float("inf"))


def _best_insertion(
    route: Sequence[str], location: str, travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[float, int]:
    """Return (extra_travel, insertion_index) for a closed route."""
    best_delta = float("inf")
    best_pos = 1
    for i in range(len(route) - 1):
        delta = (
            _distance(route[i], location, travel_matrix)
            + _distance(location, route[i + 1], travel_matrix)
            - _distance(route[i], route[i + 1], travel_matrix)
        )
        if delta < best_delta:
            best_delta = delta
            best_pos = i + 1
    return best_delta, best_pos


def _time_to_minutes(value: str) -> int:
    try:
        hour_str, minute_str = value.split(":", 1)
        return int(hour_str) * 60 + int(minute_str)
    except Exception:
        return 24 * 60


def _job_priority(
    job: Job, eligible_count: int, engineers: List[Engineer], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[int, int, float, int]:
    """Sort scarce, earlier and longer jobs first."""
    min_distance = min(
        (_distance(engineer.location, job.location, travel_matrix) for engineer in engineers),
        default=float("inf"),
    )
    distance_rank = int(min_distance * 1000) if min_distance != float("inf") else 10**9
    return (
        eligible_count,
        _time_to_minutes(job.time),
        -job.length,
        distance_rank,
    )


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
    if not engineers:
        return assignments, list(jobs)

    # Track each engineer's evolving workload and an insertion-heuristic route.
    state = {
        engineer.id: {
            "job_hours": 0.0,
            "travel_hours": 0.0,
            "route": [engineer.location, engineer.location],  # closed route
        }
        for engineer in engineers
    }

    eligible_by_job: Dict[int, List[Engineer]] = {}
    for job in jobs:
        eligible_by_job[job.id] = [
            engineer
            for engineer in engineers
            if all(skill in engineer.skills for skill in job.required_skills)
        ]

    # Scarcity-first scheduling avoids consuming exclusive-skill engineers too early.
    ordered_jobs = sorted(
        jobs,
        key=lambda job: _job_priority(
            job, len(eligible_by_job[job.id]), eligible_by_job[job.id], travel_matrix
        ),
    )

    unassigned: List[Job] = []

    def try_assign(job: Job) -> bool:
        candidates = eligible_by_job[job.id]
        if not candidates:
            return False

        best_choice = None
        for engineer in candidates:
            engineer_state = state[engineer.id]
            route = engineer_state["route"]
            if job.location in route:
                delta_travel = 0.0
                insert_pos = -1
            else:
                delta_travel, insert_pos = _best_insertion(route, job.location, travel_matrix)

            projected_travel = engineer_state["travel_hours"] + delta_travel
            projected_total = engineer_state["job_hours"] + job.length + projected_travel
            if projected_total > engineer.working_hours + 1e-9:
                continue

            # Prefer lower projected utilisation and then lower travel increase.
            score = (
                projected_total,
                delta_travel,
                _distance(engineer.location, job.location, travel_matrix),
                engineer.id,
            )
            if best_choice is None or score < best_choice[0]:
                best_choice = (score, engineer, insert_pos, delta_travel)

        if best_choice is None:
            return False

        _, engineer, insert_pos, delta_travel = best_choice
        assignments[engineer.id].append(job)
        engineer_state = state[engineer.id]
        engineer_state["job_hours"] += job.length
        engineer_state["travel_hours"] += delta_travel
        if insert_pos >= 0:
            engineer_state["route"].insert(insert_pos, job.location)
        return True

    for job in ordered_jobs:
        if not try_assign(job):
            unassigned.append(job)

    # Fallback pass: retry previously unassigned jobs after the first allocation wave.
    remaining: List[Job] = []
    for job in unassigned:
        if not try_assign(job):
            remaining.append(job)

    return assignments, remaining
