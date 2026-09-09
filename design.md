# GENIUS Pilot — Design Document

## Architecture Overview

The system is split into four layers. Each layer has a single responsibility and depends only on layers below it.

```
┌─────────────────────────────────────────┐
│  Entry points                           │
│  src/demo.py · src/features/data_loader │
├─────────────────────────────────────────┤
│  Orchestration                          │
│  src/scheduling/scheduler.py            │
├─────────────────────────────────────────┤
│  Algorithms                             │
│  src/optimization/matching.py           │
│  src/optimization/routing.py            │
├─────────────────────────────────────────┤
│  Domain models                          │
│  src/models/engineer.py                 │
│  src/models/job.py                      │
└─────────────────────────────────────────┘
```

The reporting feature (`src/features/report.py`) sits beside the orchestration layer — it consumes the output of `Scheduler.create_schedule` but does not participate in the scheduling logic.

---

## Module Responsibilities

### `src/models/`

Pure data containers. No logic except `__post_init__` skill normalisation (lowercase). Both `Engineer` and `Job` are `@dataclass`es.

### `src/optimization/routing.py`

Solves the Travelling Salesperson Problem for a single engineer's job list.

**Public surface:** `find_optimal_route(start, destinations, travel_matrix)` — the only function the rest of the system calls. Returns `(route_tuple, total_distance)`.

**Implementations available:**
- `brute_force_tsp` — O(n!), exact. Kept for reference and small-instance correctness tests.
- `nearest_neighbor_tsp` — O(n²), heuristic. Greedy: always move to the closest unvisited destination. `find_optimal_route` delegates here.

`find_optimal_route` is an intentional seam: swapping the underlying algorithm requires changing one line.

### `src/optimization/matching.py`

Assigns jobs to engineers. Single public function: `assign_jobs(engineers, jobs, travel_matrix)`.

**Algorithm (three-phase greedy):**

1. **Sort jobs by constraint level.** Count how many engineers possess all skills for each job. Sort ascending — jobs only one engineer can do go first (most-constrained-first heuristic).

2. **For each job, filter and sort candidates.**
   - Keep only engineers who have all required skills.
   - Sort by `(travel_distance, -remaining_capacity)`: nearest engineer first; tie-break on who has more headroom.

3. **Capacity-check and assign.** Iterate candidates in order. For each, estimate total travel time by calling `find_optimal_route` on the engineer's current jobs plus this new job. Accept the first candidate where `total_job_time + new_job.length + estimated_travel ≤ working_hours`. If no candidate fits, the job is unassigned.

**Why most-constrained-first?** Without it, shared-skill jobs can fill the only engineer who can do an exclusive-skill job. Processing exclusive jobs first reserves capacity where it is needed.

**Why distance-first sort with capacity tiebreaker?** Distance-first minimises total travel (matching the benchmark optimal solutions). The capacity tiebreaker means equidistant engineers with less load are preferred, spreading work when distances are equal.

### `src/scheduling/scheduler.py`

Thin orchestrator. `Scheduler.create_schedule()`:

1. Calls `assign_jobs` → gets assignments and unassigned list.
2. For each engineer with ≥ 1 job, calls `find_optimal_route` on their job locations.
3. Returns `(assignments, routes, unassigned)`.

### `src/features/data_loader.py`

Reads a JSON file, validates it against the domain rules (see spec FR-6), applies defaults, and constructs `Engineer` and `Job` objects. Raises typed exceptions so callers can give user-friendly error messages.

### `src/features/report.py`

Converts scheduling output to per-engineer CSV files.

**`_calculate_job_timings`** walks the route tuple in order, accumulating time in minutes. For each route stop it computes the travel cost from the previous stop. The first job at each stop receives that travel cost; subsequent jobs at the same stop get `0`. Returns a list of per-job timing dicts.

**`generate_report`** sorts the timing records by `job_time` (chronological presentation), writes job rows, then appends a `TOTAL` summary row that sums `job_duration_minutes`, `travel_time_minutes`, and `total_time_minutes`.

---

## Data Flow

```
JSON file
   │
   ▼ load_data()
(engineers, jobs, travel_matrix)
   │
   ▼ Scheduler.create_schedule()
   │   ├─ assign_jobs()          → assignments, unassigned
   │   └─ find_optimal_route()   → routes
   │
   ▼
(assignments, routes, unassigned)
   │
   ▼ generate_report()
per-engineer CSV files
```

---

## Key Design Decisions

### `find_optimal_route` as a seam

All callers (matching and scheduler) go through `find_optimal_route`. The brute-force and nearest-neighbor implementations are separate named functions. Replacing the algorithm is a one-line change in `find_optimal_route`.

### O(n²) routing in the matching loop

`assign_jobs` calls `find_optimal_route` for each (job, candidate engineer) pair to estimate whether the job fits. With nearest-neighbor TSP this is O(k²) per call (k = current jobs for that engineer). The total cost is bounded in practice because each engineer carries at most `working_hours / min_job_length` jobs.

### Constraint-level job ordering

Sorting jobs by number of qualified engineers before the assignment loop is a standard CSP heuristic (Minimum Remaining Values). It does not change asymptotic complexity but eliminates the class of greedy failures where a shared-skill job blocks an exclusive-skill engineer.

### Route order vs. report order

Routes are computed for travel efficiency (TSP order). The CSV report presents jobs in `job_time` order for readability. These two orderings can differ. Travel times in the report are computed from the TSP route; the `job_time` sort is applied only to the output rows.

### No external dependencies

The standard library (`itertools`, `csv`, `json`, `os`) covers all needs. This keeps the environment simple for a participant study.

---

## File Layout

```
GENIUS_pilot/
├── src/
│   ├── models/
│   │   ├── engineer.py          # Engineer dataclass
│   │   └── job.py               # Job dataclass
│   ├── optimization/
│   │   ├── routing.py           # TSP algorithms
│   │   └── matching.py          # Job assignment
│   ├── scheduling/
│   │   └── scheduler.py         # Orchestrator
│   ├── features/
│   │   ├── data_loader.py       # JSON input
│   │   └── report.py            # CSV output
│   └── demo.py                  # Runnable entry point
├── data/
│   ├── sample_data.py           # 10 engineers, 100 jobs (seeded)
│   ├── travel_matrix.py         # 100×100 matrix (seeded)
│   ├── benchmarks/              # 5 small instances with known optimal solutions
│   ├── external/                # Example external input
│   └── performance/             # Large instances (1k–10k jobs)
├── tests/
│   ├── test_models.py
│   ├── test_engineer.py
│   ├── test_job.py
│   ├── test_routing.py
│   ├── test_routing_checkpoint_a.py   # Performance gate: 10 destinations < 0.25 s
│   ├── test_matching.py
│   ├── test_scheduler.py
│   ├── test_scheduler_integration.py
│   ├── test_benchmarks.py             # Quality gate: accuracy = 1.0, ratio ≤ 1.5
│   ├── test_report_correctness.py
│   ├── test_data_loader.py
│   └── performance/
│       └── test_scalability.py        # 5-level throughput gates
├── spec.md                      # Requirements
└── design.md                    # This file
```

---

## Test Strategy

| Layer | Test file | What it checks |
|---|---|---|
| Models | `test_models.py`, `test_engineer.py`, `test_job.py` | Construction, defaults, skill normalisation |
| Routing | `test_routing.py` | Correctness invariants (all locations visited, route starts/ends at home) |
| Routing perf | `test_routing_checkpoint_a.py` | 10 destinations in < 0.25 s |
| Matching | `test_matching.py` | Skill filter, capacity, proximity, overflow |
| Scheduler (integration) | `test_scheduler.py`, `test_scheduler_integration.py` | End-to-end correctness on sample and custom data |
| Quality | `test_benchmarks.py` | Assignment accuracy and travel efficiency vs. known-optimal solutions |
| Report | `test_report_correctness.py` | CSV structure, time arithmetic, ordering, TOTAL row |
| Data loader | `test_data_loader.py` | All validation error paths and default-value application |
| Scalability | `tests/performance/test_scalability.py` | Throughput at five input sizes |
