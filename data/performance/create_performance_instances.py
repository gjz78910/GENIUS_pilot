"""Script to generate large performance test instances.

Creates standardized large datasets for performance testing.
"""

from __future__ import annotations

import json
import random
from typing import Dict, List

random.seed(42)

# Available skills
all_skills = ["repair", "install", "maintain", "upgrade", "inspect", "configure", "troubleshoot", "replace"]


def create_travel_matrix(num_locations: int) -> Dict[str, Dict[str, float]]:
    """Create a travel matrix for given number of locations."""
    locations = [f"LOC{i:05d}" for i in range(num_locations)]
    matrix: Dict[str, Dict[str, float]] = {}
    
    for loc1 in locations:
        matrix[loc1] = {}
        for loc2 in locations:
            if loc1 == loc2:
                matrix[loc1][loc2] = 0.0
            else:
                # Generate symmetric travel times (0.1 to 2.0 hours)
                if loc2 not in matrix or loc1 not in matrix.get(loc2, {}):
                    travel_time = round(random.uniform(0.1, 2.0), 2)
                    matrix[loc1][loc2] = travel_time
                else:
                    matrix[loc1][loc2] = matrix[loc2][loc1]
    
    return matrix


def create_performance_instance(
    num_engineers: int, num_jobs: int, num_locations: int, filename: str
) -> None:
    """Create a performance test instance and save to JSON."""
    locations = [f"LOC{i:05d}" for i in range(num_locations)]
    travel_matrix = create_travel_matrix(num_locations)
    
    # Create engineers distributed across locations
    engineers = []
    for i in range(1, num_engineers + 1):
        location = locations[(i * num_locations // num_engineers) % num_locations]
        num_skills = random.randint(3, 6)
        skills = random.sample(all_skills, num_skills)
        working_hours = random.choice([8.0, 10.0, 12.0])
        engineers.append({
            "id": i,
            "name": f"Engineer{i:04d}",
            "location": location,
            "skills": skills,
            "working_hours": working_hours,
        })
    
    # Create jobs
    jobs = []
    for i in range(1, num_jobs + 1):
        location = random.choice(locations)
        hour = 8 + (i % 12)
        time = f"{hour:02d}:00"
        num_skills = random.randint(1, 3)
        required_skills = random.sample(all_skills, num_skills)
        length = random.choice([0.5, 1.0, 1.5, 2.0, 2.5, 3.0])
        jobs.append({
            "id": i,
            "location": location,
            "time": time,
            "required_skills": required_skills,
            "length": length,
        })
    
    # Create JSON structure
    instance = {
        "description": f"Performance test instance: {num_engineers} engineers, {num_jobs} jobs, {num_locations} locations",
        "engineers": engineers,
        "jobs": jobs,
        "travel_matrix": travel_matrix,
    }
    
    # Save to file
    filepath = f"data/performance/{filename}"
    with open(filepath, "w") as f:
        json.dump(instance, f, indent=2)
    
    print(f"Created {filename}: {num_engineers} engineers, {num_jobs} jobs, {num_locations} locations")


if __name__ == "__main__":
    # Create performance instances of varying sizes
    create_performance_instance(50, 1000, 200, "performance_1000_jobs.json")
    create_performance_instance(100, 5000, 500, "performance_5000_jobs.json")
    create_performance_instance(200, 10000, 1000, "performance_10000_jobs.json")
