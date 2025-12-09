"""Definition of the Engineer class used in the scheduling tool.

An `Engineer` represents a field engineer with a unique identifier,
a name, a home location and a list of skills.  Skills are expressed as
strings and used to match engineers to jobs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Union, Tuple


Location = Union[str, Tuple[float, float]]


@dataclass
class Engineer:
    """Represents a field engineer that can be assigned to jobs.

    Attributes
    ----------
    id: int
        Unique identifier for the engineer.
    name: str
        Human‑friendly name.
    location: Location
        Home base of the engineer.  For the purposes of this MVP the
        location is typically a simple string (e.g. "A", "B", ...).
    skills: List[str]
        A list of skills (strings) that this engineer possesses.
    """

    id: int
    name: str
    location: Location
    skills: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        # normalise skills to lower case for consistency
        self.skills = [skill.lower() for skill in self.skills]

    def __repr__(self) -> str:
        return (
            f"Engineer(id={self.id!r}, name={self.name!r}, "
            f"location={self.location!r}, skills={self.skills!r})"
        )