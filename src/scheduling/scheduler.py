"""High‑level scheduler that orchestrates matching and routing.

This module defines a `Scheduler` class that takes a list of engineers,
a list of jobs and a travel matrix.  It coordinates assigning jobs to
engineers and computing an optimised travel route for each engineer.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from src.models.engineer import Engineer
from src.models.job import Job
from src.optimization.matching import assign_jobs
from src.optimization.routing import brute_force_tsp


class Scheduler:
    """Coordinate job assignment and route optimisation for engineers."""

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
    ) -> Tuple[Dict[int, List[Job]], Dict[int, Tuple[Tuple[str, ...], float]]]:
        """Assign jobs and compute routes for each engineer.

        Returns
        -------
        assignments : Dict[int, List[Job]]
            Mapping from engineer ID to the list of jobs assigned to that engineer.
        routes : Dict[int, Tuple[Tuple[str, ...], float]]
            Mapping from engineer ID to a tuple of (route, total distance).  The
            route is represented as a tuple of location strings including the
            starting and ending location.
        """
        # Perform the assignment
        assignments: Dict[int, List[Job]] = assign_jobs(self.engineers, self.jobs, self.travel_matrix)

        routes: Dict[int, Tuple[Tuple[str, ...], float]] = {}
        # Compute the optimal route for each engineer based on their assigned jobs
        for engineer in self.engineers:
            assigned_jobs: List[Job] = assignments.get(engineer.id, [])
            if not assigned_jobs:
                # No jobs assigned; skip route optimisation
                continue
            job_locations: List[str] = [job.location for job in assigned_jobs]
            route, distance = brute_force_tsp(engineer.location, job_locations, self.travel_matrix)
            routes[engineer.id] = (route, distance)

        return assignments, routes