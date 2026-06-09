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
            # Diagonal entries (distance from a location to itself) must be zero.
            # A non-zero self-distance is physically meaningless and indicates
            # a data error in the input file.
            if source == dest and time != 0.0:
                raise ValueError(
                    f"travel_matrix diagonal entry [{source}][{dest}] must be 0.0, got {time}"
                )

    # Validate travel matrix symmetry: distance A->B must equal B->A.
    # An asymmetric matrix would produce inconsistent route calculations
    # depending on travel direction, which this system does not support.
    for source in travel_matrix:
        for dest in travel_matrix.get(source, {}):
            if dest in travel_matrix and source in travel_matrix.get(dest, {}):
                forward = travel_matrix[source][dest]
                reverse = travel_matrix[dest][source]
                if forward != reverse:
                    raise ValueError(
                        f"travel_matrix is not symmetric: [{source}][{dest}]={forward} "
                        f"but [{dest}][{source}]={reverse}"
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

        # Validate working_hours is within a reasonable range (0 to 24).
        # Negative hours are nonsensical, and no engineer can work more than
        # 24 hours in a single day.
        working_hours = e_data.get("working_hours", 8.0)
        if not isinstance(working_hours, (int, float)) or working_hours < 0 or working_hours > 24:
            raise ValueError(
                f"Engineer '{e_data['name']}' has invalid working_hours: {working_hours}. "
                "Must be between 0 and 24."
            )

        engineer = Engineer(
            id=eng_id,
            name=e_data["name"],
            location=location,
            skills=e_data.get("skills", []),
            working_hours=working_hours,
            max_jobs=e_data.get("max_jobs", 10),
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
        # Validate that the job's location exists in the travel matrix.
        # Without this, routing calculations would fail with a KeyError
        # when trying to look up travel distances for this job.
        if location not in all_locations:
            raise ValueError(f"Job location '{location}' not found in travel_matrix")

        # Validate time format is HH:MM with valid hour (00-23) and minute (00-59).
        # This ensures scheduling logic can reliably parse and compare job times.
        # Reject strings that don't match the two-digit colon two-digit pattern,
        # as well as values outside the valid clock range (e.g. "25:00").
        time_str = j_data["time"]
        time_match = re.match(r"^(\d{2}):(\d{2})$", str(time_str))
        if not time_match:
            raise ValueError(
                f"Job {job_id} has invalid time format: '{time_str}'. Expected HH:MM."
            )
        hour, minute = int(time_match.group(1)), int(time_match.group(2))
        if hour > 23 or minute > 59:
            raise ValueError(
                f"Job {job_id} has invalid time value: '{time_str}'. "
                "Hour must be 00-23, minute must be 00-59."
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
