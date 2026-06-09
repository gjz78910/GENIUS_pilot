"""Load engineers, jobs, and travel matrix from a JSON file.

Expected top-level keys:
- `engineers`
- `jobs`
- `travel_matrix`
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Tuple

from src.models.engineer import Engineer
from src.models.job import Job

# Regex for valid HH:MM time (00:00 - 23:59)
_TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _validate_time_format(time_str: str) -> None:
    """Validate that a time string is in HH:MM format (00:00-23:59).

    Raises
    ------
    ValueError
        If the time format is invalid.
    """
    if not isinstance(time_str, str) or not _TIME_PATTERN.match(time_str):
        raise ValueError(
            f"Invalid time format '{time_str}'. "
            "Time must be in HH:MM format (00:00-23:59)."
        )


def _validate_travel_matrix(travel_matrix: Dict[str, Dict[str, float]]) -> None:
    """Validate travel matrix constraints.

    Checks:
    - Non-zero diagonal entries (distance from a location to itself must be 0)
    - Asymmetric entries (distance A->B must equal B->A)

    Raises
    ------
    ValueError
        If the travel matrix violates constraints.
    """
    # Check diagonal is zero
    for loc, destinations in travel_matrix.items():
        if loc in destinations and destinations[loc] != 0.0:
            raise ValueError(
                f"Non-zero diagonal in travel_matrix: "
                f"travel_matrix['{loc}']['{loc}'] = {destinations[loc]} (must be 0.0)."
            )

    # Check symmetry
    for src, destinations in travel_matrix.items():
        for dst, dist in destinations.items():
            if dst in travel_matrix and src in travel_matrix[dst]:
                reverse_dist = travel_matrix[dst][src]
                if abs(dist - reverse_dist) > 1e-9:
                    raise ValueError(
                        f"Asymmetric travel_matrix: "
                        f"travel_matrix['{src}']['{dst}'] = {dist} but "
                        f"travel_matrix['{dst}']['{src}'] = {reverse_dist}. "
                        f"Matrix must be symmetric."
                    )


def load_data(file_path: str) -> Tuple[List[Engineer], List[Job], Dict[str, Dict[str, float]]]:
    """Load engineers, jobs and travel matrix from a JSON file.

    Parameters
    ----------
    file_path : str
        Path to the JSON file containing the data.

    Returns
    -------
    Tuple[List[Engineer], List[Job], Dict[str, Dict[str, float]]]
        A tuple containing:
        - List of Engineer objects
        - List of Job objects
        - Travel matrix (nested dict: location -> location -> hours)

    Raises
    ------
    FileNotFoundError
        If the file doesn't exist.
    json.JSONDecodeError
        If the file is not valid JSON.
    ValueError
        If the data format is invalid or missing required fields.
    """
    with open(file_path, "r") as f:
        data = json.load(f)

    # Validate structure
    if not isinstance(data, dict):
        raise ValueError("JSON file must contain a single object")
    if "engineers" not in data:
        raise ValueError("Missing 'engineers' key in JSON file")
    if "jobs" not in data:
        raise ValueError("Missing 'jobs' key in JSON file")
    if "travel_matrix" not in data:
        raise ValueError("Missing 'travel_matrix' key in JSON file")

    # Load travel matrix
    travel_matrix = data["travel_matrix"]
    if not isinstance(travel_matrix, dict):
        raise ValueError("travel_matrix must be a dictionary")

    # Validate travel matrix structure
    all_locations = set()
    for source, destinations in travel_matrix.items():
        if not isinstance(destinations, dict):
            raise ValueError(f"travel_matrix[{source}] must be a dictionary")
        all_locations.add(source)
        all_locations.update(destinations.keys())
        for dest, time in destinations.items():
            if not isinstance(time, (int, float)) or time < 0:
                raise ValueError(f"travel_matrix[{source}][{dest}] must be a non-negative number")

    # Validate diagonal and symmetry
    _validate_travel_matrix(travel_matrix)

    # Load engineers
    engineers = []
    engineer_ids = set()
    for e_data in data["engineers"]:
        if not isinstance(e_data, dict):
            raise ValueError("Each engineer must be a dictionary")

        # Required fields
        if "id" not in e_data:
            raise ValueError("Engineer missing 'id' field")
        if "name" not in e_data:
            raise ValueError("Engineer missing 'name' field")
        if "location" not in e_data:
            raise ValueError("Engineer missing 'location' field")

        eng_id = e_data["id"]
        if eng_id in engineer_ids:
            raise ValueError(f"Duplicate engineer ID: {eng_id}")
        engineer_ids.add(eng_id)

        location = e_data["location"]
        if location not in all_locations:
            raise ValueError(f"Engineer location '{location}' not found in travel_matrix")

        # Validate working_hours
        working_hours = e_data.get("working_hours", 8.0)
        if not isinstance(working_hours, (int, float)) or working_hours <= 0 or working_hours > 24:
            raise ValueError(
                f"Invalid working_hours ({working_hours}) for engineer '{e_data['name']}'. "
                "working_hours must be > 0 and <= 24."
            )

        engineer = Engineer(
            id=eng_id,
            name=e_data["name"],
            location=location,
            skills=e_data.get("skills", []),
            working_hours=working_hours,
        )
        engineers.append(engineer)

    # Load jobs
    jobs = []
    job_ids = set()
    for j_data in data["jobs"]:
        if not isinstance(j_data, dict):
            raise ValueError("Each job must be a dictionary")

        # Required fields
        if "id" not in j_data:
            raise ValueError("Job missing 'id' field")
        if "location" not in j_data:
            raise ValueError("Job missing 'location' field")
        if "time" not in j_data:
            raise ValueError("Job missing 'time' field")

        job_id = j_data["id"]
        if job_id in job_ids:
            raise ValueError(f"Duplicate job ID: {job_id}")
        job_ids.add(job_id)

        # Validate time format
        _validate_time_format(j_data["time"])

        # Validate job location is in travel matrix
        location = j_data["location"]
        if location not in all_locations:
            raise ValueError(
                f"Job location '{location}' not found in travel_matrix"
            )

        job = Job(
            id=job_id,
            location=location,
            time=j_data["time"],
            required_skills=j_data.get("required_skills", []),
            length=j_data.get("length", 1.0),
        )
        jobs.append(job)

    return engineers, jobs, travel_matrix
