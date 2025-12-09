"""Naïve job‑to‑engineer assignment logic.

This module implements a simple matching algorithm that assigns each job to
an engineer based on two criteria:

* **Skill match** – The engineer must possess all the skills required by
  the job.
* **Location proximity** – Among the engineers with suitable skills,
  preference is given to the engineer whose home location is closest to
  the job location according to the provided travel matrix.

The algorithm does not attempt to balance workload evenly across engineers
or take account of job times.  It simply finds the best match on a
per‑job basis (bucket/bin sort) and produces a mapping from engineer IDs
to lists of `Job` instances.
"""

from __future__ import annotations

from typing import Dict, List

from src.models.engineer import Engineer
from src.models.job import Job


def assign_jobs(
    engineers: List[Engineer], jobs: List[Job], travel_matrix: Dict[str, Dict[str, float]]
) -> Dict[int, List[Job]]:
    """Assign jobs to engineers using a simple bucket/bin sort.

    Parameters
    ----------
    engineers : List[Engineer]
        The available field engineers.
    jobs : List[Job]
        The jobs that need to be assigned.
    travel_matrix : Dict[str, Dict[str, float]]
        A dictionary representing the travel distance between locations.  The
        outer keys are starting locations and the inner keys are
        destination locations.

    Returns
    -------
    Dict[int, List[Job]]
        A mapping from engineer ID to the list of jobs assigned to that
        engineer.  Engineers with no assigned jobs will still appear in
        the dictionary with an empty list.
    """
    # Initialise assignment mapping with empty lists for each engineer
    assignments: Dict[int, List[Job]] = {e.id: [] for e in engineers}

    for job in jobs:
        # Filter engineers who possess all required skills
        candidates: List[Engineer] = [
            engineer
            for engineer in engineers
            if all(req_skill in engineer.skills for req_skill in job.required_skills)
        ]
        if not candidates:
            # No engineer can fulfil this job; leave it unassigned
            continue

        # Find the candidate with the minimal travel distance to the job location
        def distance_fn(engineer: Engineer) -> float:
            # Look up travel distance; default to a large number if missing
            return travel_matrix.get(engineer.location, {}).get(job.location, float("inf"))

        best_engineer = min(candidates, key=distance_fn)
        assignments[best_engineer.id].append(job)

    return assignments