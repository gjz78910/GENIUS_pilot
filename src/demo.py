"""Example runner for the scheduling tool experiment.

This module demonstrates how to use the basic scheduling system.  It
loads the hardcoded sample data, assigns jobs to engineers using a
naïve matching algorithm, computes an optimised travel route for each
engineer using a brute‑force travelling‑salesperson algorithm and prints
the resulting assignments and routes to the console.

To run this example, change into the project directory and
execute:

    python -m src.demo

The output will show which jobs are assigned to each engineer and the
optimal visiting order of job locations for each engineer.
"""

from __future__ import annotations

from typing import List

from data.sample_data import engineers, jobs
from data.travel_matrix import travel_matrix
# Import the scheduler from the src.scheduling package.  When running this
# module as ``python -m src.demo`` the top‑level package is ``src``.
from src.scheduling.scheduler import Scheduler


def main() -> None:
    """Run the example scheduling workflow and print the results."""
    scheduler = Scheduler(engineers, jobs, travel_matrix)
    assignments, routes, unassigned = scheduler.create_schedule()

    print("Job Assignments and Routes:\n")
    for engineer in engineers:
        assigned_jobs = assignments.get(engineer.id, [])
        if assigned_jobs:
            job_ids: List[int] = [job.id for job in assigned_jobs]
            job_lengths = [job.length for job in assigned_jobs]
            total_job_hours = sum(job_lengths)
            
            # Get optimized route and travel time
            route, optimal_travel_time = routes.get(engineer.id, ((), 0.0))
            total_hours = total_job_hours + optimal_travel_time
            
            print(f"Engineer {engineer.id} ({engineer.name}) assigned jobs: {job_ids}")
            print(f"  Job time: {total_job_hours:.1f}h, Travel time: {optimal_travel_time:.1f}h")
            print(f"  Total: {total_hours:.1f}h / {engineer.working_hours}h working hours")
            if route:
                route_str = " -> ".join(route)
                print(f"  Optimal route: {route_str} (total travel time {optimal_travel_time:.1f}h)")
            print()
        else:
            print(f"Engineer {engineer.id} ({engineer.name}) has no assigned jobs.\n")
    
    if unassigned:
        print("\n⚠️  WARNING: UNASSIGNED JOBS ⚠️")
        print(f"The following {len(unassigned)} job(s) could not be assigned:\n")
        for job in unassigned:
            print(f"  Job {job.id}: location={job.location}, length={job.length}h, skills={job.required_skills}")
        print()


if __name__ == "__main__":
    main()
