"""Job-to-engineer assignment logic.

The main entry point is `assign_jobs`, which returns:
- assigned jobs per engineer
- jobs that could not be assigned
"""

from __future__ import annotations

from typing import Dict, List

from src.models.engineer import Engineer
from src.models.job import Job
from src.optimization.routing import nearest_neighbour_route


def _chain_travel_estimate(
    start: str, job_locations: List[str], travel_matrix: Dict[str, Dict[str, float]]
) -> float:
    """Estimate round-trip travel time as a chain: start → job1 → job2 → ... → start.

    This is O(k) and serves as an upper bound on the optimal route travel time,
    making it safe to use for capacity checks without calling a TSP solver.
    """
    if not job_locations:
        return 0.0
    total = 0.0
    current = start
    for loc in job_locations:
        total += travel_matrix.get(current, {}).get(loc, 0.0)
        current = loc
    total += travel_matrix.get(current, {}).get(start, 0.0)
    return total


def _fits_capacity(
    engineer: Engineer,
    jobs: List[Job],
    travel_matrix: Dict[str, Dict[str, float]],
) -> bool:
    """Return True if the engineer can handle these jobs within working hours."""
    job_time = sum(j.length for j in jobs)
    if not jobs:
        return True
    _, travel_time = nearest_neighbour_route(
        engineer.location, [j.location for j in jobs], travel_matrix
    )
    return job_time + travel_time <= engineer.working_hours


def _try_move(
    from_id: int,
    to_id: int,
    assignments: Dict[int, List[Job]],
    engineer_map: Dict[int, Engineer],
    travel_matrix: Dict[str, Dict[str, float]],
) -> bool:
    """Try moving one job from from_id to to_id if it reduces combined travel time.

    Returns True and mutates assignments if a beneficial move is found.
    """
    eng_from = engineer_map[from_id]
    eng_to = engineer_map[to_id]

    for job in assignments[from_id]:
        if not all(s in eng_to.skills for s in job.required_skills):
            continue
        new_from = [j for j in assignments[from_id] if j.id != job.id]
        new_to = assignments[to_id] + [job]

        if not _fits_capacity(eng_from, new_from, travel_matrix):
            continue
        if not _fits_capacity(eng_to, new_to, travel_matrix):
            continue

        old_travel = _chain_travel_estimate(
            eng_from.location, [j.location for j in assignments[from_id]], travel_matrix
        ) + _chain_travel_estimate(
            eng_to.location, [j.location for j in assignments[to_id]], travel_matrix
        )
        new_travel = _chain_travel_estimate(
            eng_from.location, [j.location for j in new_from], travel_matrix
        ) + _chain_travel_estimate(
            eng_to.location, [j.location for j in new_to], travel_matrix
        )

        if new_travel < old_travel - 1e-9:
            assignments[from_id] = new_from
            assignments[to_id] = new_to
            return True

    return False


def _improve_with_swaps(
    assignments: Dict[int, List[Job]],
    engineers: List[Engineer],
    travel_matrix: Dict[str, Dict[str, float]],
    max_passes: int = 3,
) -> None:
    """Improve assignments by moving single jobs between engineers to reduce travel.

    Runs at most max_passes full sweeps over all engineer pairs, stopping early
    if a pass finds no improvements. Each pass is O(E² × k_avg), avoiding the
    restart-per-swap cost of a naive while-improved loop.
    """
    engineer_map: Dict[int, Engineer] = {e.id: e for e in engineers}
    for _ in range(max_passes):
        improved = False
        active_ids = [eid for eid, jobs in assignments.items() if jobs]
        for i in range(len(active_ids)):
            for j in range(i + 1, len(active_ids)):
                eid_a, eid_b = active_ids[i], active_ids[j]
                if _try_move(eid_a, eid_b, assignments, engineer_map, travel_matrix):
                    improved = True
                if _try_move(eid_b, eid_a, assignments, engineer_map, travel_matrix):
                    improved = True
        if not improved:
            break


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

    # Process hardest-to-assign jobs first: fewest qualified engineers, then longest duration
    def _difficulty(job: Job) -> tuple:
        qualified = sum(
            1 for e in engineers
            if all(s in e.skills for s in job.required_skills)
        )
        return (qualified, -job.length)

    for job in sorted(jobs, key=_difficulty):
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
            candidate_jobs = assignments[engineer.id] + [job]
            if _fits_capacity(engineer, candidate_jobs, travel_matrix):
                assignments[engineer.id].append(job)
                assigned = True
                break

        if not assigned:
            unassigned.append(job)

    _improve_with_swaps(assignments, engineers, travel_matrix)

    return assignments, unassigned
