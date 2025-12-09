"""Example runner for the scheduling tool experiment.

This module demonstrates how to use the basic scheduling system.  It
loads the hardcoded sample data, assigns jobs to engineers using a
naïve matching algorithm, computes an optimised travel route for each
engineer using a brute‑force travelling‑salesperson algorithm and prints
the resulting assignments and routes to the console.

To run this example, change into the `scheduling_tool` directory and
execute:

    python -m src.main

The output will show which jobs were assigned to each engineer and the
optimal visiting order of job locations for each engineer.
"""

from __future__ import annotations

from typing import List

from data.sample_data import engineers, jobs
from data.travel_matrix import travel_matrix
# Import the scheduler from the src.scheduling package.  When running this
# module as ``python -m src.main`` the top‑level package is ``src``.
from src.scheduling.scheduler import Scheduler


def main() -> None:
    """Run the example scheduling workflow and print the results."""
    scheduler = Scheduler(engineers, jobs, travel_matrix)
    assignments, routes = scheduler.create_schedule()

    print("Job Assignments and Routes:\n")
    for engineer in engineers:
        assigned_jobs = assignments.get(engineer.id, [])
        if assigned_jobs:
            job_ids: List[int] = [job.id for job in assigned_jobs]
            print(f"Engineer {engineer.id} ({engineer.name}) assigned jobs: {job_ids}")
            route, distance = routes.get(engineer.id, ((), 0))
            if route:
                route_str = " -> ".join(route)
                print(f"  Optimal route: {route_str} (total distance {distance})")
            print()
        else:
            print(f"Engineer {engineer.id} ({engineer.name}) has no assigned jobs.\n")


if __name__ == "__main__":
    main()