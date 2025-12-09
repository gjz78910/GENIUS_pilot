"""Hardcoded travel matrix for job locations.

The travel matrix represents the distance between pairs of locations.  The
outer keys are starting locations and the inner keys are destination
locations.  Distances are symmetric and measured in arbitrary units.
"""

from __future__ import annotations

from typing import Dict


__all__ = ["travel_matrix"]

travel_matrix: Dict[str, Dict[str, float]] = {
    "A": {"A": 0, "B": 10, "C": 15, "D": 20},
    "B": {"A": 10, "B": 0, "C": 35, "D": 25},
    "C": {"A": 15, "B": 35, "C": 0, "D": 30},
    "D": {"A": 20, "B": 25, "C": 30, "D": 0},
}