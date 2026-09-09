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

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


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
            if source == dest and time != 0:
                raise ValueError(
                    f"travel_matrix diagonal must be 0: travel_matrix[{source}][{dest}] = {time}"
                )

    for source, destinations in travel_matrix.items():
        for dest, time in destinations.items():
            reverse = travel_matrix.get(dest, {}).get(source)
            if reverse is not None and reverse != time:
                raise ValueError(
                    f"travel_matrix is not symmetric: [{source}][{dest}]={time} but [{dest}][{source}]={reverse}"
                )

    # Validate top-level list types
    if not isinstance(data["engineers"], list):
        raise ValueError("'engineers' must be a list")
    if not isinstance(data["jobs"], list):
        raise ValueError("'jobs' must be a list")

    # Load engineers
    engineers = []
    engineer_ids = set()
    for e_data in data["engineers"]:
        if not isinstance(e_data, dict):
            raise ValueError("Each engineer must be a dictionary")

        for field in ("id", "name", "location"):
            if field not in e_data:
                raise ValueError(f"Engineer missing '{field}' field")

        eng_id = e_data["id"]
        if not isinstance(eng_id, int):
            raise ValueError(f"Engineer 'id' must be an integer, got {eng_id!r}")
        if eng_id in engineer_ids:
            raise ValueError(f"Duplicate engineer ID: {eng_id}")
        engineer_ids.add(eng_id)

        if not isinstance(e_data["name"], str):
            raise ValueError(f"Engineer {eng_id} 'name' must be a string")

        location = e_data["location"]
        if location not in all_locations:
            raise ValueError(f"Engineer location '{location}' not found in travel_matrix")

        skills = e_data.get("skills", [])
        if not isinstance(skills, list) or not all(isinstance(s, str) for s in skills):
            raise ValueError(f"Engineer {eng_id} 'skills' must be a list of strings")

        working_hours = e_data.get("working_hours", 8.0)
        if not isinstance(working_hours, (int, float)) or working_hours <= 0 or working_hours > 24:
            raise ValueError(f"Engineer {eng_id} 'working_hours' must be between 0 and 24")

        engineer = Engineer(
            id=eng_id,
            name=e_data["name"],
            location=location,
            skills=skills,
            working_hours=working_hours,
        )
        engineers.append(engineer)

    # Load jobs
    jobs = []
    job_ids = set()
    for j_data in data["jobs"]:
        if not isinstance(j_data, dict):
            raise ValueError("Each job must be a dictionary")

        for field in ("id", "location", "time"):
            if field not in j_data:
                raise ValueError(f"Job missing '{field}' field")

        job_id = j_data["id"]
        if not isinstance(job_id, int):
            raise ValueError(f"Job 'id' must be an integer, got {job_id!r}")
        if job_id in job_ids:
            raise ValueError(f"Duplicate job ID: {job_id}")
        job_ids.add(job_id)

        location = j_data["location"]
        if location not in all_locations:
            raise ValueError(f"Job {job_id} location '{location}' not found in travel_matrix")

        time_val = j_data["time"]
        if not isinstance(time_val, str) or not _TIME_RE.match(time_val):
            raise ValueError(f"Job {job_id} 'time' must be in HH:MM format, got {time_val!r}")

        required_skills = j_data.get("required_skills", [])
        if not isinstance(required_skills, list) or not all(isinstance(s, str) for s in required_skills):
            raise ValueError(f"Job {job_id} 'required_skills' must be a list of strings")

        length = j_data.get("length", 1.0)
        if not isinstance(length, (int, float)) or length <= 0:
            raise ValueError(f"Job {job_id} 'length' must be a positive number")

        job = Job(
            id=job_id,
            location=location,
            time=time_val,
            required_skills=required_skills,
            length=length,
        )
        jobs.append(job)

    return engineers, jobs, travel_matrix
