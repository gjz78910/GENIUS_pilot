# GENIUS Pilot — Requirements Specification

## Purpose

A field-engineer scheduling system. Given a set of engineers and jobs, the system assigns each job to an engineer and calculates a travel route for each engineer's working day.

---

## Domain Concepts

### Engineer

| Field | Type | Default | Constraints |
|---|---|---|---|
| `id` | int | — | unique |
| `name` | str | — | — |
| `location` | str | — | must exist in the travel matrix |
| `skills` | list[str] | `[]` | normalised to lowercase |
| `working_hours` | float | `8.0` | must be > 0 |

### Job

| Field | Type | Default | Constraints |
|---|---|---|---|
| `id` | int | — | unique |
| `location` | str | — | must exist in the travel matrix |
| `time` | str | — | format `"HH:MM"` |
| `required_skills` | list[str] | `[]` | normalised to lowercase |
| `length` | float | `1.0` | duration in hours |

### Travel Matrix

A symmetric dict-of-dicts `matrix[loc_a][loc_b] -> float` giving travel time in hours. Same-location travel must be `0.0`.

---

## Functional Requirements

### FR-1 Skill matching

A job may only be assigned to an engineer who possesses **all** of the job's `required_skills`. Jobs for which no engineer has the required skills are left **unassigned** — they must not cause an error.

### FR-2 Capacity constraint

The total of `job.length` values plus estimated travel time for all jobs assigned to an engineer must not exceed that engineer's `working_hours`.

### FR-3 Balanced assignment

When multiple engineers are qualified and have remaining capacity, assignment must avoid overloading a single engineer. Engineers with more remaining capacity should be preferred (distance is the primary tiebreaker when capacities differ).

### FR-4 Most-constrained-first ordering

Jobs that fewer engineers can perform must be processed before jobs that many engineers can perform. This reserves exclusive-skill engineers for jobs only they can do.

### FR-5 Route calculation

Each engineer's assigned jobs must be arranged into a tour that starts and ends at the engineer's home location and visits every job location exactly once. The route must complete in acceptable time for practical job counts (≤ 10 jobs per engineer must complete in < 0.25 s).

### FR-6 Data loading

The system must load engineers, jobs, and a travel matrix from a JSON file. The loader must:

- Raise `ValueError` for missing required fields, duplicate IDs, engineer locations not in the matrix, invalid job locations, invalid time formats, asymmetric travel matrix, non-zero diagonal, and non-positive working hours.
- Apply default values: `working_hours=8.0`, `skills=[]`, `length=1.0`, `required_skills=[]`.

### FR-7 CSV report generation

For each engineer with at least one assigned job, produce a CSV file `engineer_{id}_schedule.csv` containing:

| Column | Description |
|---|---|
| `engineer_id` | Engineer identifier |
| `engineer_name` | Engineer name |
| `job_id` | Job identifier (or `"TOTAL"` for summary row) |
| `job_location` | Location string |
| `job_time` | Scheduled time string (`"HH:MM"`) |
| `required_skills` | Comma-separated skill list |
| `job_start_time_minutes` | Start time offset from day start (minutes) |
| `job_end_time_minutes` | End time offset from day start (minutes) |
| `job_duration_minutes` | `job.length × 60` |
| `travel_time_minutes` | Travel time to reach this job (minutes) |
| `total_time_minutes` | `job_duration_minutes + travel_time_minutes` |

Additional report constraints:

- **FR-7a** Rows are ordered by `job_time` (chronological).
- **FR-7b** The final row has `job_id = "TOTAL"` and aggregates `job_duration_minutes`, `travel_time_minutes`, and `total_time_minutes` across all job rows.
- **FR-7c** `job_end_time_minutes = job_start_time_minutes + job_duration_minutes`.
- **FR-7d** `travel_time_minutes > 0` for any job reached from a different location.
- **FR-7e** All jobs fit within the engineer's `working_hours` window (last `job_end_time_minutes ≤ working_hours × 60`).
- **FR-7f** No job appears more than once per report.

---

## Non-Functional Requirements

### NFR-1 Performance

| Input size | Time limit |
|---|---|
| 25 engineers, 250 jobs | 3 s |
| 80 engineers, 1 000 jobs | 5 s |
| 250 engineers, 3 000 jobs | 10 s |
| 350 engineers, 3 800 jobs | 15 s |
| 350 engineers, 4 000 jobs | 30 s |

Route calculation for 10 destinations must complete in < 0.25 s (rules out O(n!) brute force).

### NFR-2 Solution quality

For the five benchmark instances, the system must:

- Achieve `assignment_accuracy = 1.0` (every job assigned to the correct engineer).
- Keep `travel_time_ratio ≤ 1.5` (actual total travel ÷ optimal total travel).
- Produce zero `unassigned_penalty` (no extra or missing unassigned jobs).

### NFR-3 No external runtime dependencies

All routing and scheduling logic uses only the Python standard library.

### NFR-4 Skill normalisation

Skill comparison is case-insensitive. `Engineer.skills` and `Job.required_skills` are normalised to lowercase on construction.

---

## Input / Output

### Input (JSON)

```json
{
  "engineers": [ { "id": 1, "name": "...", "location": "A", "skills": ["repair"], "working_hours": 8.0 } ],
  "jobs":      [ { "id": 1, "location": "A", "time": "09:00", "required_skills": ["repair"], "length": 2.0 } ],
  "travel_matrix": { "A": { "A": 0.0, "B": 1.0 }, "B": { "A": 1.0, "B": 0.0 } }
}
```

### Output

- A dict mapping `engineer_id -> List[Job]` (assignments)
- A dict mapping `engineer_id -> (route_tuple, total_distance)` (routes)
- A list of unassigned `Job` objects
- Per-engineer CSV files (when `generate_report` is called)
