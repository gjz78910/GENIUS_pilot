"""Definition of the Job class used in the scheduling tool.

A `Job` represents a work assignment that needs to be carried out by an
engineer.  It includes an identifier, the location where the work will
take place, an optional scheduled time and a list of required skills.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class Job:
    """Represents a job that must be assigned to an engineer.

    Attributes
    ----------
    id: int
        Unique identifier for the job.
    location: str
        Location of the job.  For the purposes of this MVP the location
        is typically a simple string (e.g. "A", "B", ...).
    time: str
        Scheduled time for the job represented as a human‑readable string.
        The scheduling algorithms in this MVP do not yet make use of this
        field but it is included for completeness.
    required_skills: List[str]
        A list of skills (strings) required to perform the job.
    """

    id: int
    location: str
    time: str
    required_skills: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        # normalise required skills to lower case for consistency
        self.required_skills = [skill.lower() for skill in self.required_skills]

    def __repr__(self) -> str:
        return (
            f"Job(id={self.id!r}, location={self.location!r}, time={self.time!r}, "
            f"required_skills={self.required_skills!r})"
        )