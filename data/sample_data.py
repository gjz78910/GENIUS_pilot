"""Hardcoded sample engineers and jobs for the scheduling tool.

This module defines a small set of engineers and jobs that can be used
for demonstration and testing purposes.  Participants in the experiment
can modify or extend this data set as needed.
"""

from __future__ import annotations

from src.models.engineer import Engineer
from src.models.job import Job

__all__ = ["engineers", "jobs"]


# Define a few engineers with distinct locations and skill sets
engineers = [
    Engineer(id=1, name="Alice", location="A", skills=["repair", "install", "upgrade"]),
    Engineer(id=2, name="Bob", location="B", skills=["install"]),
    Engineer(id=3, name="Charlie", location="C", skills=["repair", "maintain"]),
    Engineer(id=4, name="Daisy", location="D", skills=["maintain", "repair", "install"]),
]


# Define a set of jobs with locations, times and required skills
jobs = [
    Job(id=1, location="D", time="09:00", required_skills=["repair"]),
    Job(id=2, location="B", time="10:00", required_skills=["install"]),
    Job(id=3, location="C", time="11:00", required_skills=["maintain"]),
    # Alice gets jobs needing "upgrade" skill (only she has it) at various locations
    Job(id=4, location="A", time="12:00", required_skills=["upgrade"]),
    Job(id=5, location="B", time="13:00", required_skills=["upgrade"]),
    Job(id=6, location="C", time="14:00", required_skills=["upgrade"]),
    Job(id=7, location="D", time="15:00", required_skills=["upgrade"]),
    Job(id=8, location="A", time="16:00", required_skills=["upgrade"]),
    Job(id=9, location="B", time="17:00", required_skills=["upgrade"]),
    Job(id=10, location="C", time="18:00", required_skills=["upgrade"]),
    Job(id=11, location="D", time="19:00", required_skills=["upgrade"]),
    Job(id=12, location="A", time="20:00", required_skills=["upgrade"]),
    Job(id=13, location="B", time="21:00", required_skills=["upgrade"]),
    # Alice (at A) gets 10 jobs across locations A,B,C,D → TSP finds best route order
]