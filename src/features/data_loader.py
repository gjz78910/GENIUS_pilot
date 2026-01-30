"""External data loader for scheduling tool.

Loads engineers, jobs and travel matrices from JSON files.

Data Format Specification:
--------------------------

The JSON file should contain a single object with three keys: "engineers", "jobs", and "travel_matrix".

Example JSON structure:
{
  "engineers": [
    {
      "id": 1,
      "name": "Alice",
      "location": "A",
      "skills": ["repair", "install"],
      "working_hours": 8.0
    }
  ],
  "jobs": [
    {
      "id": 1,
      "location": "B",
      "time": "09:00",
      "required_skills": ["repair"],
      "length": 2.0
    }
  ],
  "travel_matrix": {
    "A": {"A": 0.0, "B": 0.5},
    "B": {"A": 0.5, "B": 0.0}
  }
}

Field Requirements:
- engineers: List of engineer objects
  - id: int (required, unique)
  - name: str (required)
  - location: str (required, must exist in travel_matrix)
  - skills: List[str] (optional, default: [])
  - working_hours: float (optional, default: 8.0)

- jobs: List of job objects
  - id: int (required, unique)
  - location: str (required, must exist in travel_matrix)
  - time: str (required, format: "HH:MM")
  - required_skills: List[str] (optional, default: [])
  - length: float (optional, default: 1.0, in hours)

- travel_matrix: Dict[str, Dict[str, float]]
  - Outer keys: source locations
  - Inner keys: destination locations
  - Values: travel time in hours (must be >= 0.0)
  - Must be symmetric: travel_matrix[A][B] == travel_matrix[B][A]
  - Must include all locations referenced in engineers and jobs
  - Diagonal values (same location) must be 0.0
"""

from __future__ import annotations

import json
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

        engineer = Engineer(
            id=eng_id,
            name=e_data["name"],
            location=location,
            skills=e_data.get("skills", []),
            working_hours=e_data.get("working_hours", 8.0),
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

        job = Job(
            id=job_id,
            location=location,
            time=j_data["time"],
            required_skills=j_data.get("required_skills", []),
            length=j_data.get("length", 1.0),
        )
        jobs.append(job)

    return engineers, jobs, travel_matrix
