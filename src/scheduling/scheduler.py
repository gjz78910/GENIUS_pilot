"""High-level scheduler that runs matching and routing.

This module defines a `Scheduler` class that takes a list of engineers,
a list of jobs and a travel matrix. It assigns jobs to engineers and
computes a route for each engineer.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from src.models.engineer import Engineer
from src.models.job import Job
from src.optimization.matching import assign_jobs
from src.optimization.new_alg_route import find_optimal_route


class Scheduler:
    """Coordinate job assignment and route calculation for engineers."""

    def __init__(
        self,
        engineers: List[Engineer],
        jobs: List[Job],
        travel_matrix: Dict[str, Dict[str, float]],
    ) -> None:
        self.engineers = engineers
        self.jobs = jobs
        self.travel_matrix = travel_matrix

    def create_schedule(
        self,
    ) -> Tuple[Dict[int, List[Job]], Dict[int, Tuple[Tuple[str, ...], float]], List[Job]]:
        """Assign jobs and compute routes for each engineer.

        Returns
        -------
        assignments : Dict[int, List[Job]]
            Mapping from engineer ID to the list of jobs assigned to that engineer.
        routes : Dict[int, Tuple[Tuple[str, ...], float]]
            Mapping from engineer ID to a tuple of (route, total distance).  The
            route is represented as a tuple of location strings including the
            starting and ending location.
        unassigned : List[Job]
            List of jobs that could not be assigned to any engineer.
        """
        # Perform the assignment
        assignments, unassigned = assign_jobs(self.engineers, self.jobs, self.travel_matrix)

        routes: Dict[int, Tuple[Tuple[str, ...], float]] = {}
        # Compute route for each engineer based on assigned jobs
        for engineer in self.engineers:
            assigned_jobs: List[Job] = assignments.get(engineer.id, [])
            if not assigned_jobs:
                # No jobs assigned; skip route calculation
                continue
            job_locations: List[str] = [job.location for job in assigned_jobs]
            route, distance = find_optimal_route(engineer.location, job_locations, self.travel_matrix)
            routes[engineer.id] = (route, distance)

        return assignments, routes, unassigned
