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


_TIME_PATTERN = re.compile(r"^\d{2}:\d{2}$")


def _validate_time_value(time_value: Any) -> None:
    """Validate time format HH:MM and range."""
    if not isinstance(time_value, str) or not _TIME_PATTERN.match(time_value):
        raise ValueError(f"Invalid time format: {time_value!r}. Expected HH:MM")
    hour_str, minute_str = time_value.split(":", 1)
    hour = int(hour_str)
    minute = int(minute_str)
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise ValueError(f"Invalid time value: {time_value!r}")


def _validate_travel_matrix(
    travel_matrix: Dict[str, Dict[str, float]]
) -> set[str]:
    """Validate shape, values, symmetry and diagonal constraints."""
    if not isinstance(travel_matrix, dict):
        raise ValueError("travel_matrix must be a dictionary")

    all_locations = set(travel_matrix.keys())
    for source, destinations in travel_matrix.items():
        if not isinstance(destinations, dict):
            raise ValueError(f"travel_matrix[{source}] must be a dictionary")
        all_locations.update(destinations.keys())
        for dest, travel_time in destinations.items():
            if not isinstance(travel_time, (int, float)) or travel_time < 0:
                raise ValueError(
                    f"travel_matrix[{source}][{dest}] must be a non-negative number"
                )

    # Ensure all locations have full rows/columns.
    for source in all_locations:
        if source not in travel_matrix:
            raise ValueError(
                f"travel_matrix missing row for location '{source}'"
            )
        row = travel_matrix[source]
        for dest in all_locations:
            if dest not in row:
                raise ValueError(
                    f"travel_matrix missing value for pair '{source}' -> '{dest}'"
                )

    # Diagonal must be zero.
    for location in all_locations:
        diagonal = float(travel_matrix[location][location])
        if abs(diagonal) > 1e-12:
            raise ValueError(
                f"travel_matrix diagonal at '{location}' must be 0.0"
            )

    # Matrix must be symmetric.
    for source in all_locations:
        for dest in all_locations:
            a_to_b = float(travel_matrix[source][dest])
            b_to_a = float(travel_matrix[dest][source])
            if abs(a_to_b - b_to_a) > 1e-9:
                raise ValueError(
                    "travel_matrix must be symmetric"
                )

    return all_locations


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

    travel_matrix = data["travel_matrix"]
    all_locations = _validate_travel_matrix(travel_matrix)

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

        working_hours = e_data.get("working_hours", 8.0)
        if not isinstance(working_hours, (int, float)) or working_hours <= 0 or working_hours > 24:
            raise ValueError(
                f"Invalid working_hours for engineer {eng_id}: {working_hours!r}"
            )

        engineer = Engineer(
            id=eng_id,
            name=e_data["name"],
            location=location,
            skills=e_data.get("skills", []),
            working_hours=float(working_hours),
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

        location = j_data["location"]
        if location not in all_locations:
            raise ValueError(f"Job location '{location}' not found in travel_matrix")

        _validate_time_value(j_data["time"])

        job = Job(
            id=job_id,
            location=location,
            time=j_data["time"],
            required_skills=j_data.get("required_skills", []),
            length=j_data.get("length", 1.0),
        )
        jobs.append(job)

    return engineers, jobs, travel_matrix
