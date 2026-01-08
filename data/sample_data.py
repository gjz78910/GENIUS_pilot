"""Hardcoded sample engineers and jobs for the scheduling tool.

This module defines a large set of engineers and jobs that can be used
for demonstration and testing purposes.  Participants in the experiment
can modify or extend this data set as needed.
"""

from __future__ import annotations

import random

from src.models.engineer import Engineer
from src.models.job import Job

__all__ = ["engineers", "jobs"]

random.seed(42)

# Generate 100 locations
locations = [f"LOC{i:03d}" for i in range(100)]

# Available skills
all_skills = ["repair", "install", "maintain", "upgrade", "inspect", "configure", "troubleshoot", "replace"]

# Generate 10 engineers distributed evenly across locations
engineers = []
for i in range(1, 11):
    location = locations[i * 10 - 10]  # Distribute evenly: LOC000, LOC010, LOC020, ..., LOC090
    num_skills = random.randint(3, 6)
    skills = random.sample(all_skills, num_skills)
    working_hours = random.choice([8.0, 10.0, 12.0])
    engineers.append(Engineer(id=i, name=f"Engineer{i:02d}", location=location, skills=skills, working_hours=working_hours))

# Generate 100 jobs
jobs = []
for i in range(1, 101):
    location = random.choice(locations)
    hour = 8 + (i % 12)
    time = f"{hour:02d}:00"
    num_skills = random.randint(1, 3)
    required_skills = random.sample(all_skills, num_skills)
    length = random.choice([0.5, 1.0, 1.5, 2.0, 2.5, 3.0])
    jobs.append(Job(id=i, location=location, time=time, required_skills=required_skills, length=length))