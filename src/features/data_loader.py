"""Load engineers, jobs, and travel matrix from a JSON file.

Expected top-level keys:
- `engineers`
- `jobs`
- `travel_matrix`
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Tuple

from src.models.engineer import Engineer
from src.models.job import Job


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

    # Diagonal must be zero (travel from a location to itself)
    for loc in travel_matrix:
        if loc in travel_matrix[loc] and travel_matrix[loc][loc] != 0.0:
            raise ValueError(f"travel_matrix[{loc}][{loc}] must be 0 (diagonal must be zero)")

    # Matrix must be symmetric
    for loc_a, destinations in travel_matrix.items():
        for loc_b, time_ab in destinations.items():
            time_ba = travel_matrix.get(loc_b, {}).get(loc_a)
            if time_ba is None:
                raise ValueError(
                    f"travel_matrix is not symmetric: [{loc_a}][{loc_b}] exists but [{loc_b}][{loc_a}] is missing"
                )
            if abs(time_ab - time_ba) > 1e-9:
                raise ValueError(
                    f"travel_matrix is not symmetric: [{loc_a}][{loc_b}]={time_ab} != [{loc_b}][{loc_a}]={time_ba}"
                )

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
            raise ValueError(f"Engineer {eng_id}: working_hours must be between 0 and 24, got {working_hours!r}")

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

        location = j_data["location"]
        if location not in all_locations:
            raise ValueError(f"Job {job_id}: location '{location}' not found in travel_matrix")

        job_time = j_data["time"]
        try:
            datetime.strptime(job_time, "%H:%M")
        except (ValueError, TypeError):
            raise ValueError(f"Job {job_id}: time '{job_time}' is not a valid HH:MM time")

        job = Job(
            id=job_id,
            location=location,
            time=j_data["time"],
            required_skills=j_data.get("required_skills", []),
            length=j_data.get("length", 1.0),
        )
        jobs.append(job)

    return engineers, jobs, travel_matrix
