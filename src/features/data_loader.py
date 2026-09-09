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

_TIME_RE = re.compile(r"^(\d{2}):(\d{2})$")


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

    # --- Top-level structure ---
    if not isinstance(data, dict):
        raise ValueError("JSON file must contain a single object")
    for key in ("engineers", "jobs", "travel_matrix"):
        if key not in data:
            raise ValueError(f"Missing '{key}' key in JSON file")

    if not isinstance(data["engineers"], list):
        raise ValueError("'engineers' must be a list")
    if not isinstance(data["jobs"], list):
        raise ValueError("'jobs' must be a list")

    # --- Travel matrix ---
    travel_matrix = data["travel_matrix"]
    if not isinstance(travel_matrix, dict):
        raise ValueError("travel_matrix must be a dictionary")

    all_locations: set = set()
    for source, destinations in travel_matrix.items():
        if not isinstance(destinations, dict):
            raise ValueError(f"travel_matrix['{source}'] must be a dictionary")
        all_locations.add(source)
        all_locations.update(destinations.keys())
        for dest, time in destinations.items():
            if not isinstance(time, (int, float)) or time < 0:
                raise ValueError(
                    f"travel_matrix['{source}']['{dest}'] must be a non-negative number"
                )
            if source == dest and time != 0.0:
                raise ValueError(
                    f"travel_matrix diagonal entry ['{source}']['{dest}'] must be 0.0, got {time}"
                )

    # Symmetry check: travel_matrix[A][B] must equal travel_matrix[B][A]
    for source in travel_matrix:
        for dest, time in travel_matrix[source].items():
            if dest in travel_matrix:
                reverse = travel_matrix[dest].get(source)
                if reverse is not None and round(reverse, 10) != round(time, 10):
                    raise ValueError(
                        f"travel_matrix is not symmetric: "
                        f"['{source}']['{dest}'] = {time} but "
                        f"['{dest}']['{source}'] = {reverse}"
                    )

    # --- Engineers ---
    engineers: List[Engineer] = []
    engineer_ids: set = set()
    for i, e_data in enumerate(data["engineers"]):
        ctx = f"engineers[{i}]"
        if not isinstance(e_data, dict):
            raise ValueError(f"{ctx} must be a dictionary")

        for field in ("id", "name", "location"):
            if field not in e_data:
                raise ValueError(f"{ctx} missing required field '{field}'")

        eng_id = e_data["id"]
        if not isinstance(eng_id, int):
            raise ValueError(f"{ctx} 'id' must be an integer, got {type(eng_id).__name__}")
        if eng_id in engineer_ids:
            raise ValueError(f"Duplicate engineer ID: {eng_id}")
        engineer_ids.add(eng_id)

        name = e_data["name"]
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"{ctx} 'name' must be a non-empty string")

        location = e_data["location"]
        if not isinstance(location, str):
            raise ValueError(f"{ctx} 'location' must be a string")
        if location not in all_locations:
            raise ValueError(
                f"{ctx} location '{location}' not found in travel_matrix"
            )

        working_hours = e_data.get("working_hours", 8.0)
        if not isinstance(working_hours, (int, float)) or working_hours <= 0 or working_hours > 24:
            raise ValueError(
                f"{ctx} 'working_hours' must be a positive number no greater than 24, got {working_hours!r}"
            )

        skills = e_data.get("skills", [])
        if not isinstance(skills, list) or not all(isinstance(s, str) for s in skills):
            raise ValueError(f"{ctx} 'skills' must be a list of strings")

        engineers.append(
            Engineer(
                id=eng_id,
                name=name,
                location=location,
                skills=skills,
                working_hours=float(working_hours),
            )
        )

    # --- Jobs ---
    jobs: List[Job] = []
    job_ids: set = set()
    for i, j_data in enumerate(data["jobs"]):
        ctx = f"jobs[{i}]"
        if not isinstance(j_data, dict):
            raise ValueError(f"{ctx} must be a dictionary")

        for field in ("id", "location", "time"):
            if field not in j_data:
                raise ValueError(f"{ctx} missing required field '{field}'")

        job_id = j_data["id"]
        if not isinstance(job_id, int):
            raise ValueError(f"{ctx} 'id' must be an integer, got {type(job_id).__name__}")
        if job_id in job_ids:
            raise ValueError(f"Duplicate job ID: {job_id}")
        job_ids.add(job_id)

        location = j_data["location"]
        if not isinstance(location, str):
            raise ValueError(f"{ctx} 'location' must be a string")
        if location not in all_locations:
            raise ValueError(
                f"{ctx} location '{location}' not found in travel_matrix"
            )

        time_val = j_data["time"]
        _time_match = _TIME_RE.match(time_val) if isinstance(time_val, str) else None
        if not _time_match or int(_time_match.group(1)) > 23 or int(_time_match.group(2)) > 59:
            raise ValueError(
                f"{ctx} 'time' must be in HH:MM format with valid hours (0-23) and minutes (0-59), got {time_val!r}"
            )

        length = j_data.get("length", 1.0)
        if not isinstance(length, (int, float)) or length <= 0:
            raise ValueError(
                f"{ctx} 'length' must be a positive number, got {length!r}"
            )

        required_skills = j_data.get("required_skills", [])
        if not isinstance(required_skills, list) or not all(
            isinstance(s, str) for s in required_skills
        ):
            raise ValueError(f"{ctx} 'required_skills' must be a list of strings")

        jobs.append(
            Job(
                id=job_id,
                location=location,
                time=time_val,
                required_skills=required_skills,
                length=float(length),
            )
        )

    return engineers, jobs, travel_matrix
