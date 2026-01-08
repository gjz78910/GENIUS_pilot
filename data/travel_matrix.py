"""Hardcoded travel matrix for job locations.

The travel matrix represents the travel time (in hours) between pairs of
locations. The outer keys are starting locations and the inner keys are
destination locations. Travel times are symmetric.
"""

from __future__ import annotations

import random
from typing import Dict

__all__ = ["travel_matrix"]

random.seed(42)

# Generate 100 locations
locations = [f"LOC{i:03d}" for i in range(100)]

# Generate travel matrix with normal distribution (mean=0.5h, std=1.0h, max=5h)
travel_matrix: Dict[str, Dict[str, float]] = {}
for loc1 in locations:
    travel_matrix[loc1] = {}
    for loc2 in locations:
        if loc1 == loc2:
            travel_matrix[loc1][loc2] = 0.0
        else:
            # Generate symmetric travel times with normal distribution
            if loc2 not in travel_matrix or loc1 not in travel_matrix[loc2]:
                travel_time = min(max(random.gauss(0.5, 1.0), 0.05), 5.0)
                travel_matrix[loc1][loc2] = travel_time
            else:
                travel_matrix[loc1][loc2] = travel_matrix[loc2][loc1]