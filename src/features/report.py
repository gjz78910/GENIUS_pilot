"""Stub for job assignment report generation.

This module contains a placeholder for generating reports of job
assignments.  Experiment participants can implement this function to
produce CSV or human‑readable text summarising which engineer is
responsible for which jobs and the computed routes.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from src.models.job import Job


def generate_report(
    assignments: Dict[int, List[Job]],
    routes: Dict[int, Tuple[Tuple[str, ...], float]] | None = None,
    file_path: str | None = None,
) -> None:
    """Generate a report for job assignments.

    Parameters
    ----------
    assignments : Dict[int, List[Job]]
        Mapping from engineer ID to the jobs assigned to that engineer.
    routes : Dict[int, Tuple[Tuple[str, ...], float]], optional
        Mapping from engineer ID to a tuple of (route, total distance).  If
        provided, the report may include routing information.
    file_path : str, optional
        Path to a file where the report should be written.  If omitted,
        the report may be printed to the console.

    Notes
    -----
    This is a stub and does not implement any functionality.  It exists so
    that participants in the experiment can practise feature development
    using AI coding assistants.  Suggested enhancements include writing
    assignments and routes to a CSV file, formatting a text report for
    display in a terminal, or generating JSON outputs.
    """
    # This stub intentionally does nothing.  Implementations may write
    # assignments and routes to a file or print to the console.
    if file_path is not None:
        # Example of how an implementation might inform the caller that
        # this feature is unfinished.  In a real implementation, you would
        # open the file and write the report contents.
        print(f"Report generation stub called. A report would be written to {file_path}.")
    else:
        print("Report generation stub called. No output produced.")