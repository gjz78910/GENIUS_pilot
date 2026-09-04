"""Job-to-engineer assignment logic.

The main entry point is `assign_jobs`, which returns:
- assigned jobs per engineer
- jobs that could not be assigned
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from src.models.engineer import Engineer
from src.models.job import Job


def _cheapest_insertion(
    route: Tuple[str, ...], location: str, travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[int, float]:
    """Find the cheapest position to insert `location` into an existing route.

    `route` is a closed loop (starts and ends at the engineer's home
    location). Returns the insertion index and the extra travel distance
    that inserting there would add. This is O(len(route)) per call, unlike
    recomputing a full optimal route, so it stays cheap even when checking
    many candidate engineers per job across thousands of jobs.
    """
    best_index = 1
    best_added = float("inf")
    for i in range(1, len(route)):
        prev_loc, next_loc = route[i - 1], route[i]
        added = (
            travel_matrix.get(prev_loc, {}).get(location, 0.0)
            + travel_matrix.get(location, {}).get(next_loc, 0.0)
            - travel_matrix.get(prev_loc, {}).get(next_loc, 0.0)
        )
        if added < best_added:
            best_added = added
            best_index = i
    return best_index, best_added


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

    # Cache each engineer's current route (as a closed loop) and its total
    # distance, updated incrementally as jobs are assigned. This avoids
    # recomputing a full route from scratch for every candidate/job pair,
    # which would be far too slow once engineers accumulate many jobs.
    engineer_routes: Dict[int, Tuple[Tuple[str, ...], float]] = {
        e.id: ((e.location, e.location), 0.0) for e in engineers
    }

    def qualified_engineer_count(job: Job) -> int:
        return sum(
            1
            for engineer in engineers
            if all(req_skill in engineer.skills for req_skill in job.required_skills)
        )

    # Assign the most constrained jobs first (fewest qualified engineers).
    # Otherwise a job that only one engineer can do may find that engineer
    # already filled up with jobs a less-constrained engineer could also
    # have done, leaving it unassigned even though a feasible full
    # assignment exists.
    jobs_by_scarcity = sorted(jobs, key=qualified_engineer_count)

    for job in jobs_by_scarcity:
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

            # Estimate travel time if this job is added, via the cheapest
            # insertion point into the engineer's current cached route.
            route, route_distance = engineer_routes[engineer.id]
            insert_index, added_distance = _cheapest_insertion(route, job.location, travel_matrix)
            estimated_travel_time = route_distance + added_distance

            # Check whether total work fits within working hours
            if total_job_time + job.length + estimated_travel_time <= engineer.working_hours:
                assignments[engineer.id].append(job)
                new_route = route[:insert_index] + (job.location,) + route[insert_index:]
                engineer_routes[engineer.id] = (new_route, estimated_travel_time)
                assigned = True
                break
        
        if not assigned:
            unassigned.append(job)

    return assignments, unassigned
