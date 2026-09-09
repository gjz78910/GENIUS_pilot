# Requirement Fulfilment Check

Verifying the four core requirements described in the project brief against the actual source code.

---

## 1. Assigns jobs to engineers based on skills and location

**File:** `src/optimization/matching.py`

| Check | Where | Status |
|---|---|---|
| Only engineers with all required skills are considered | Lines 56–59 — `all(req_skill in engineer.skills ...)` | ✅ Fulfilled |
| Closest engineer (by travel distance) is preferred | Line 70 — `travel_matrix[engineer.location][job.location]` as primary sort key | ✅ Fulfilled |
| Engineer capacity (working hours) is respected | Line 89 — `total_job_time + job.length + travel ≤ working_hours` | ✅ Fulfilled |
| Jobs no engineer can do are left unassigned (no crash) | Lines 61–64 — silent `continue` to `unassigned` | ✅ Fulfilled |
| Exclusive-skill jobs are reserved before shared ones fill capacity | Lines 44–52 — `sorted(jobs, key=_skilled_count)` | ✅ Fulfilled |

**Example from brief:** Alice at A with `repair` skill. A repair job at A.
- Skill filter: Alice has `repair` → passes.
- Distance: `travel_matrix["A"]["A"] = 0.0` → Alice is the closest candidate.
- Result: job assigned to Alice. ✅

---

## 2. Finds a good travel route for each engineer

**File:** `src/optimization/routing.py`

| Check | Where | Status |
|---|---|---|
| Route starts and ends at engineer's home location | `nearest_neighbor_tsp` — `route = [start]`, appends `start` at end | ✅ Fulfilled |
| Every job location is visited exactly once | Greedy loop removes each destination from `unvisited` | ✅ Fulfilled |
| Route is efficient (not brute-force) | `nearest_neighbor_tsp` — O(n²) greedy, not O(n!) | ✅ Fulfilled |
| `find_optimal_route` is the single entry point used by all callers | Line 125 — delegates to `nearest_neighbor_tsp` | ✅ Fulfilled |

**Example from brief:** Alice has jobs at A, B, C. Starting at A.
- Nearest-neighbor builds the route greedily: A → closest unvisited → … → A.
- Returns e.g. `("A", "B", "C", "A")` with total distance. ✅

---

## 3. Creates reports showing each engineer's schedule

**File:** `src/features/report.py`

| Check | Where | Status |
|---|---|---|
| One CSV file per engineer (skips engineers with no jobs) | Lines 118–120 — `if not jobs: continue` | ✅ Fulfilled |
| Shows job location, time, required skills | Lines 65–74 — all three stored in each record | ✅ Fulfilled |
| Shows start/end time and duration in minutes | Lines 61–63 — computed from route walk | ✅ Fulfilled |
| Shows travel time to each job | Lines 55–76 — `pending_travel` given to first job at each stop | ✅ Fulfilled |
| `total_time_minutes = duration + travel` | Line 173 | ✅ Fulfilled |
| Jobs ordered chronologically by `job_time` | Line 149 — `job_records.sort(key=lambda r: r["job_time"])` | ✅ Fulfilled |
| TOTAL summary row at end of each CSV | Lines 188–203 | ✅ Fulfilled |

**Minor gap — fallback path (no route provided):**
Lines 133–146: when `generate_report` is called without `routes` or `travel_matrix`, all `travel_time_minutes` are written as `0.0`. This is a valid fallback but means travel is invisible if the caller omits those arguments. The `Scheduler` always passes them, so normal usage is unaffected.

---

## 4. Can load job data from files

**File:** `src/features/data_loader.py`

| Check | Where | Status |
|---|---|---|
| Reads engineers, jobs, travel matrix from JSON | Lines 43–44, 88–123, 125–167 | ✅ Fulfilled |
| Raises `FileNotFoundError` if file absent | Built-in `open()` behaviour | ✅ Fulfilled |
| Raises `ValueError` for missing top-level keys | Lines 49–54 | ✅ Fulfilled |
| Raises `ValueError` for duplicate engineer/job IDs | Lines 103–106, 140–143 | ✅ Fulfilled |
| Raises `ValueError` for engineer location not in matrix | Lines 108–110 | ✅ Fulfilled |
| Raises `ValueError` for job location not in matrix | Lines 145–147 | ✅ Fulfilled |
| Raises `ValueError` for invalid `HH:MM` time format | Lines 150–158 | ✅ Fulfilled |
| Raises `ValueError` for asymmetric travel matrix | Lines 79–86 | ✅ Fulfilled |
| Raises `ValueError` for non-zero diagonal | Lines 73–76 | ✅ Fulfilled |
| Applies defaults (`working_hours=8.0`, `skills=[]`, `length=1.0`, `required_skills=[]`) | Lines 112, 120–121, 164–165 | ✅ Fulfilled |

**One discrepancy found — undocumented upper bound on `working_hours`:**
```python
# data_loader.py line 113
if not isinstance(working_hours, (int, float)) or working_hours < 0 or working_hours > 24:
    raise ValueError(...)
```
The spec (FR-6) only requires `working_hours > 0`. The code additionally rejects values above 24.
This is not documented in the spec and causes the test `test_load_invalid_working_hours` to assert that `25.0` is invalid — a constraint that does not exist in the spec.

**Minor gap — symmetry check is one-directional:**
Lines 79–86 only check that `matrix[A][B] == matrix[B][A]` when **both entries exist**. If `matrix[A][B]` is present but `matrix[B][A]` is absent entirely, no error is raised. A fully asymmetric file with missing reverse entries passes validation.

---

## Summary

| Requirement | Fulfilled? | Notes |
|---|---|---|
| Assign jobs by skills and location | ✅ Yes | Fully implemented |
| Find a good travel route | ✅ Yes | Nearest-neighbor O(n²) heuristic |
| Create per-engineer schedule reports | ✅ Yes | One minor fallback caveat |
| Load job data from files | ✅ Yes | Two small edge-case gaps |

All four requirements are fulfilled. The two items worth addressing:

1. **`data_loader.py:113`** — the `working_hours > 24` check should either be added to the spec or removed from the code.
2. **`data_loader.py:79–86`** — symmetry check should also verify that a reverse entry exists, not just that it matches when present.
