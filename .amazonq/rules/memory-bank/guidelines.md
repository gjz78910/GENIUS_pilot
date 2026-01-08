# Development Guidelines

## Code Quality Standards

### Documentation Style

**Module-Level Docstrings** (5/5 files)
- Every module starts with a triple-quoted docstring
- Describes the module's purpose and key functionality
- Uses proper formatting with line breaks for readability
- Example:
```python
"""High‑level scheduler that orchestrates matching and routing.

This module defines a `Scheduler` class that takes a list of engineers,
a list of jobs and a travel matrix.  It coordinates assigning jobs to
engineers and computing an optimised travel route for each engineer.
"""
```

**Function/Method Docstrings** (5/5 files)
- All public functions have comprehensive docstrings
- Uses NumPy-style documentation format with sections:
  - Parameters section with type and description
  - Returns section with type and description
- Example:
```python
def assign_jobs(
    engineers: List[Engineer], jobs: List[Job], travel_matrix: Dict[str, Dict[str, float]]
) -> Dict[int, List[Job]]:
    """Assign jobs to engineers using a simple bucket/bin sort.

    Parameters
    ----------
    engineers : List[Engineer]
        The available field engineers.
    jobs : List[Job]
        The jobs that need to be assigned.
    travel_matrix : Dict[str, Dict[str, float]]
        A dictionary representing the travel distance between locations.

    Returns
    -------
    Dict[int, List[Job]]
        A mapping from engineer ID to the list of jobs assigned to that
        engineer.
    """
```

**Class Docstrings** (2/2 classes)
- Classes use docstrings with Attributes section for dataclasses
- Brief description followed by detailed attribute documentation
- Example:
```python
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
        Home base of the engineer.
    skills: List[str]
        A list of skills (strings) that this engineer possesses.
    """
```

### Code Formatting Patterns

**Import Organization** (5/5 files)
- Future imports first: `from __future__ import annotations`
- Standard library imports grouped together
- Third-party imports (none in this project)
- Local imports last, grouped by package
- Example:
```python
from __future__ import annotations

from itertools import permutations
from typing import Iterable, Sequence, Tuple, Dict

from src.models.engineer import Engineer
from src.models.job import Job
```

**Type Hints** (5/5 files)
- All function signatures include complete type hints
- Return types always specified
- Complex types use typing module: `List`, `Dict`, `Tuple`, `Optional`, `Union`
- Type aliases for clarity: `Location = Union[str, Tuple[float, float]]`
- Example:
```python
def brute_force_tsp(
    start: str, destinations: Sequence[str], travel_matrix: Dict[str, Dict[str, float]]
) -> Tuple[Tuple[str, ...], float]:
```

**Line Length and Formatting** (5/5 files)
- Function signatures split across multiple lines when long
- One parameter per line for readability
- Closing parenthesis on same line as last parameter
- Example:
```python
def __init__(
    self,
    engineers: List[Engineer],
    jobs: List[Job],
    travel_matrix: Dict[str, Dict[str, float]],
) -> None:
```

### Naming Conventions

**Variables** (5/5 files)
- Snake_case for all variables: `best_engineer`, `job_locations`, `assigned_jobs`
- Descriptive names that convey purpose
- Type suffixes when helpful: `distance_fn`, `route_str`

**Functions** (5/5 files)
- Snake_case for all functions: `assign_jobs`, `brute_force_tsp`, `create_schedule`
- Verb-based names indicating action: `assign`, `create`, `compute`

**Classes** (2/2 files)
- PascalCase: `Engineer`, `Scheduler`
- Noun-based names representing entities

**Constants** (3/5 files)
- Lowercase for local constants: `best_distance`, `best_route`
- Use `float("inf")` for infinity values

## Structural Conventions

### Dataclass Pattern (1/2 models)

**Using @dataclass Decorator**
```python
from dataclasses import dataclass, field

@dataclass
class Engineer:
    id: int
    name: str
    location: Location
    skills: List[str] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        # Data normalization logic
        self.skills = [skill.lower() for skill in self.skills]
```

**Benefits**:
- Automatic `__init__`, `__repr__`, `__eq__` generation
- Clean attribute declarations with type hints
- `__post_init__` for data validation/normalization
- `field(default_factory=list)` for mutable defaults

### Class-Based Organization (2/5 files)

**Scheduler Pattern**
```python
class Scheduler:
    """Coordinate job assignment and route optimisation for engineers."""
    
    def __init__(
        self,
        engineers: List[Engineer],
        jobs: List[Job],
        travel_matrix: Dict[str, Dict[str, float]],
    ) -> None:
        self.engineers = engineers
        self.jobs = jobs
        self.travel_matrix = travel_matrix
    
    def create_schedule(self) -> Tuple[...]:
        # Orchestration logic
```

**When to Use Classes**:
- Orchestration/coordination logic (Scheduler)
- Data models with behavior (Engineer, Job)
- Stateful operations

**When to Use Functions**:
- Pure algorithms (matching, routing)
- Stateless transformations
- Utility operations

## Semantic Patterns

### Algorithm Implementation Pattern (2/2 optimization files)

**Structure**:
1. Initialize result containers
2. Iterate over input data
3. Apply filtering/selection logic
4. Update results
5. Return final result

**Example - Matching Algorithm**:
```python
def assign_jobs(engineers, jobs, travel_matrix):
    # 1. Initialize
    assignments: Dict[int, List[Job]] = {e.id: [] for e in engineers}
    
    # 2. Iterate
    for job in jobs:
        # 3. Filter candidates
        candidates = [e for e in engineers if all(skill in e.skills for skill in job.required_skills)]
        if not candidates:
            continue
        
        # 4. Select best
        best_engineer = min(candidates, key=distance_fn)
        assignments[best_engineer.id].append(job)
    
    # 5. Return
    return assignments
```

### Inline Function Definition Pattern (2/5 files)

**Local Helper Functions**:
```python
def distance_fn(engineer: Engineer) -> float:
    return travel_matrix.get(engineer.location, {}).get(job.location, float("inf"))

best_engineer = min(candidates, key=distance_fn)
```

**When to Use**:
- Function only used once in local scope
- Captures local variables (closure)
- Improves readability with named logic

### Dictionary Initialization Pattern (3/5 files)

**Dictionary Comprehension for Initialization**:
```python
# Initialize with empty lists for all engineers
assignments: Dict[int, List[Job]] = {e.id: [] for e in engineers}

# Initialize with empty dict for all locations
routes: Dict[int, Tuple[Tuple[str, ...], float]] = {}
```

### Safe Dictionary Access Pattern (3/5 files)

**Using .get() with Defaults**:
```python
# Nested dictionary access with fallback
distance = travel_matrix.get(engineer.location, {}).get(job.location, float("inf"))

# Simple access with default
assigned_jobs = assignments.get(engineer.id, [])
route, distance = routes.get(engineer.id, ((), 0))
```

**Benefits**:
- Avoids KeyError exceptions
- Provides sensible defaults
- Cleaner than try/except blocks

### List Comprehension Pattern (4/5 files)

**Filtering with Comprehensions**:
```python
# Filter with condition
candidates = [engineer for engineer in engineers 
              if all(req_skill in engineer.skills for req_skill in job.required_skills)]

# Transform data
job_ids = [job.id for job in assigned_jobs]
job_locations = [job.location for job in assigned_jobs]
```

### Early Return Pattern (3/5 files)

**Guard Clauses**:
```python
if not candidates:
    continue

if not destinations:
    return (start, start), 0.0

if not assigned_jobs:
    continue
```

**Benefits**:
- Reduces nesting
- Handles edge cases early
- Improves readability

## Internal API Usage

### Model Instantiation

**Engineer Creation**:
```python
from src.models.engineer import Engineer

engineer = Engineer(
    id=1,
    name="Alice",
    location="A",
    skills=["repair", "install"]  # Auto-normalized to lowercase
)
```

**Job Creation**:
```python
from src.models.job import Job

job = Job(
    id=1,
    location="D",
    scheduled_time="09:00",
    required_skills={"repair"}  # Set of lowercase strings
)
```

### Scheduler Usage

**Complete Workflow**:
```python
from src.scheduling.scheduler import Scheduler
from data.sample_data import engineers, jobs
from data.travel_matrix import travel_matrix

# Initialize scheduler
scheduler = Scheduler(engineers, jobs, travel_matrix)

# Execute scheduling
assignments, routes = scheduler.create_schedule()

# Access results
for engineer in engineers:
    assigned_jobs = assignments.get(engineer.id, [])
    if assigned_jobs:
        route, distance = routes.get(engineer.id, ((), 0))
```

### Optimization Functions

**Direct Algorithm Usage**:
```python
from src.optimization.matching import assign_jobs
from src.optimization.routing import brute_force_tsp

# Job assignment
assignments = assign_jobs(engineers, jobs, travel_matrix)

# Route optimization
route, distance = brute_force_tsp(
    start="A",
    destinations=["B", "C", "D"],
    travel_matrix=travel_matrix
)
```

## Common Code Idioms

### Min/Max with Key Function (2/5 files)

```python
# Find minimum by custom criteria
best_engineer = min(candidates, key=distance_fn)

# Find minimum distance in TSP
if distance < best_distance:
    best_distance = distance
    best_route = (start,) + perm + (start,)
```

### Tuple Concatenation (1/5 files)

```python
# Build route tuple
best_route = (start,) + perm + (start,)
```

### Assertion for Type Checking (1/5 files)

```python
assert best_route is not None  # for type checker
return best_route, best_distance
```

**Purpose**: Satisfy static type checkers when logic guarantees non-None

### String Formatting (2/5 files)

**F-strings Preferred**:
```python
print(f"Engineer {engineer.id} ({engineer.name}) assigned jobs: {job_ids}")
print(f"  Optimal route: {route_str} (total distance {distance})")
```

**String Join for Sequences**:
```python
route_str = " -> ".join(route)
```

## Testing Patterns

### Test Organization
- Test files mirror source structure: `test_models.py`, `test_scheduler.py`
- Use unittest framework from standard library
- Test classes inherit from `unittest.TestCase`

### Module Execution Pattern (2/2 entry points)

**Main Guard**:
```python
def main() -> None:
    """Run the example scheduling workflow and print the results."""
    # Implementation

if __name__ == "__main__":
    main()
```

**Module Execution**:
```bash
python -m src.main
python -m unittest discover -s tests
```

## Data Normalization Pattern (2/2 models)

**Automatic Normalization in __post_init__**:
```python
def __post_init__(self) -> None:
    # Normalize skills to lowercase for consistency
    self.skills = [skill.lower() for skill in self.skills]
```

**Benefits**:
- Ensures data consistency
- Case-insensitive comparisons
- Single source of truth for normalization

## Error Handling Philosophy

### Graceful Degradation (2/5 files)
- Unassigned jobs silently skipped (no exception)
- Missing travel matrix entries default to infinity
- Empty job lists handled without errors

### Minimal Exception Handling
- No try/except blocks in current codebase
- Relies on defensive programming (guards, defaults)
- Assumes valid input data

## Performance Considerations

### Algorithm Complexity Awareness (1/5 files)
```python
# Brute-force TSP - O(n!) complexity
for perm in permutations(destinations):
    # Only suitable for small n (< 10)
```

**Documentation**: Explicitly state algorithm limitations in docstrings

### Efficient Data Structures (3/5 files)
- Use sets for skill matching: `skill in engineer.skills`
- Dictionary lookups for assignments: O(1) access
- List comprehensions over loops for filtering

## Extension Points

### Stub Implementation Pattern (2/2 feature files)

**report.py and data_loader.py**:
- Intentionally incomplete for experiment tasks
- Should follow same documentation and typing standards
- Expected to integrate with existing scheduler API

### Future Enhancement Areas
1. **Workload balancing** in matching.py
2. **Time constraints** in routing.py
3. **CSV/JSON I/O** in data_loader.py
4. **Report generation** in report.py
