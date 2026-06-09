# Report Generation Bugfix Design

## Overview

The CSV report generation module (`src/features/report.py`) has four defects that cause incorrect output in per-engineer schedule CSVs. The `_calculate_job_timings` function hardcodes `travel_time_minutes` to 0.0 instead of using the computed travel value, and returns jobs in TSP route order rather than chronological `job_time` order. The `generate_report` function hardcodes `total_time_minutes` to 0.0 instead of computing `duration + travel`, and does not append a TOTAL summary row after all job detail rows.

The fix is minimal and localized to `src/features/report.py`: correct the two hardcoded values, add a sort before returning job records, and append a summary row after writing detail rows.

## Glossary

- **Bug_Condition (C)**: The set of inputs where the current code produces incorrect output — any engineer with at least one assigned job triggers all four defects simultaneously
- **Property (P)**: The desired correct behavior — travel time reflects actual distances, total time sums duration and travel, jobs appear chronologically, and a TOTAL row aggregates metrics
- **Preservation**: Existing correct behavior that must remain unchanged — CSV file naming, column structure, no-overlap timing, working-hours bounds, no missing/duplicate jobs, and `end = start + duration`
- **`_calculate_job_timings`**: Function in `src/features/report.py` that builds job records with timing data by traversing the TSP route
- **`generate_report`**: Function in `src/features/report.py` that writes per-engineer CSV files from job records
- **TSP route order**: The order locations are visited to minimize travel distance (not necessarily chronological)
- **Chronological order**: Jobs sorted by their `job_time` field (e.g., "09:00" < "10:00" < "11:00")

## Bug Details

### Bug Condition

The bug manifests whenever `generate_report` is called with valid assignments, routes, and a travel matrix. Every engineer with at least one job will have incorrect travel time (0.0), incorrect total time (0.0), no summary row, and route-order output. The four defects are independent but share the same trigger condition: the presence of assigned jobs.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type ReportGenerationCall (engineers, assignments, routes, travel_matrix)
  OUTPUT: boolean

  RETURN EXISTS engineer_id IN assignments.keys()
         WHERE len(assignments[engineer_id]) > 0
         AND routes IS NOT None
         AND travel_matrix IS NOT None
END FUNCTION
```

### Examples

- **Travel time bug**: Engineer at location A has a job at location B (0.5 hours apart). Report shows `travel_time_minutes = 0.0` instead of `30.0`.
- **Total time bug**: A job has `job_duration_minutes = 120.0` and `travel_time_minutes = 30.0`. Report shows `total_time_minutes = 0.0` instead of `150.0`.
- **Missing TOTAL row**: After 3 job detail rows, the CSV ends without a summary row. Expected: a final row with `job_id='TOTAL'` and summed metrics.
- **Ordering bug**: Engineer at location D has jobs at A (09:00), B (10:00), C (11:00). TSP route visits B first, so CSV lists B before A. Expected: A, B, C (chronological).

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- One CSV file per engineer named `engineer_{id}_schedule.csv`
- CSV columns remain: engineer_id, engineer_name, job_id, job_location, job_time, required_skills, job_start_time_minutes, job_end_time_minutes, job_duration_minutes, travel_time_minutes, total_time_minutes
- All assigned jobs appear in the report with no duplicates or missing entries
- `job_end_time_minutes = job_start_time_minutes + job_duration_minutes` for each job
- Jobs do not overlap in time (each starts at or after previous end plus travel)
- All jobs fit within the engineer's working hours window
- When no routes/travel_matrix are provided, basic records are created with zeroed timing

**Scope:**
All inputs that do NOT involve the specific defective code paths should be unaffected. This includes:
- CSV file creation and directory handling
- Engineer lookup and filtering of empty assignments
- The overall structure of the DictWriter output
- Handling of engineers with no assigned jobs (skipped)

## Hypothesized Root Cause

Based on code analysis, the root causes are confirmed (not hypothesized):

1. **Hardcoded travel_time_minutes**: In `_calculate_job_timings` (line ~56), the dict literal sets `"travel_time_minutes": 0.0` instead of using the already-computed `travel_minutes` variable from line ~42.

2. **Hardcoded total_time_minutes**: In `generate_report` (line ~120), the variable `total_time = 0.0` is never updated. It should be computed as `record["job_duration_minutes"] + record["travel_time_minutes"]`.

3. **Missing TOTAL summary row**: In `generate_report`, after the `for record in job_records` loop, there is no code to aggregate metrics and write a final summary row.

4. **Route-order output instead of chronological**: In `_calculate_job_timings`, job records are built in route traversal order and returned directly. There is no sort by `job_time` before returning.

## Correctness Properties

Property 1: Bug Condition - Travel Time Correctness

_For any_ report generation call where an engineer has jobs at multiple locations with known travel times, the fixed `_calculate_job_timings` function SHALL populate `travel_time_minutes` with the actual travel time (in minutes) from the previous location to the job's location, matching the travel matrix value × 60.

**Validates: Requirements 2.1**

Property 2: Bug Condition - Total Time Correctness

_For any_ job record written to the CSV, the fixed `generate_report` function SHALL compute `total_time_minutes` as the sum of `job_duration_minutes` and `travel_time_minutes` for that row.

**Validates: Requirements 2.2**

Property 3: Bug Condition - TOTAL Summary Row

_For any_ engineer with at least one assigned job, the fixed `generate_report` function SHALL append a final row with `job_id='TOTAL'` containing the sum of `job_duration_minutes`, `travel_time_minutes`, and `total_time_minutes` across all detail rows.

**Validates: Requirements 2.3**

Property 4: Bug Condition - Chronological Ordering

_For any_ engineer with multiple assigned jobs, the fixed `_calculate_job_timings` function SHALL return job records sorted in ascending order by their `job_time` field.

**Validates: Requirements 2.4**

Property 5: Preservation - CSV Structure and Timing Integrity

_For any_ report generation call, the fixed code SHALL produce the same CSV file naming, column structure, no-overlap timing guarantees, working-hours bounds, and `end = start + duration` calculations as the original code (except for the corrected fields).

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

## Fix Implementation

### Changes Required

**File**: `src/features/report.py`

**Function**: `_calculate_job_timings`

**Specific Changes**:
1. **Fix travel_time_minutes**: Change `"travel_time_minutes": 0.0` to `"travel_time_minutes": travel_minutes` in the job_records.append() dict literal (~line 56).

2. **Sort by job_time before returning**: Before the `return job_records` statement, add `job_records.sort(key=lambda r: r["job_time"])` to ensure chronological output regardless of TSP route order.

**Function**: `generate_report`

**Specific Changes**:
3. **Fix total_time_minutes**: Replace `total_time = 0.0` with `total_time = record["job_duration_minutes"] + record["travel_time_minutes"]` (or compute inline) so the written value reflects actual duration + travel.

4. **Append TOTAL summary row**: After the `for record in job_records` loop, compute aggregate sums of `job_duration_minutes`, `travel_time_minutes`, and `total_time_minutes` across all records, then call `writer.writerow(...)` with `job_id='TOTAL'` and the aggregated values.

5. **Summary row field values**: The TOTAL row should have `engineer_id` and `engineer_name` set normally, `job_location`, `job_time`, and `required_skills` left empty (or blank strings), and numeric aggregates rounded to 2 decimal places.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm the root cause analysis by running existing tests against unfixed code.

**Test Plan**: Run the four failing tests in `tests/test_report_correctness.py` on the unfixed code to confirm they fail for the expected reasons.

**Test Cases**:
1. **Travel Time Test** (`test_travel_time_between_jobs`): Engineer with jobs at locations A and B — asserts at least one `travel_time_minutes > 0` (will fail on unfixed code)
2. **Total Time Test** (`test_total_time_is_duration_plus_travel`): Asserts `total_time = duration + travel` for each row (will fail on unfixed code)
3. **Summary Row Test** (`test_summary_row`): Asserts last row has `job_id='TOTAL'` with correct aggregates (will fail on unfixed code)
4. **Ordering Test** (`test_jobs_ordered_by_time`): Asserts jobs appear in chronological `job_time` order (will fail on unfixed code)

**Expected Counterexamples**:
- `travel_time_minutes` is always 0.0 even when jobs are at different locations
- `total_time_minutes` is always 0.0 regardless of duration and travel values
- No TOTAL row exists in any CSV output
- Jobs appear in route order (B, A, C) instead of time order (A, B, C)

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  csv_output := generate_report_fixed(input)
  FOR EACH row IN csv_output (excluding TOTAL):
    ASSERT row.travel_time_minutes == travel_matrix[prev_loc][row.location] * 60
    ASSERT row.total_time_minutes == row.job_duration_minutes + row.travel_time_minutes
  END FOR
  ASSERT last_row.job_id == "TOTAL"
  ASSERT last_row.job_duration_minutes == SUM(detail_rows.job_duration_minutes)
  ASSERT last_row.travel_time_minutes == SUM(detail_rows.travel_time_minutes)
  ASSERT last_row.total_time_minutes == SUM(detail_rows.total_time_minutes)
  ASSERT job_times ARE sorted ascending
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function. Also verify that unchanged behaviors remain intact for all inputs.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  csv_output := generate_report_fixed(input)
  FOR EACH row IN csv_output (excluding TOTAL):
    ASSERT row.job_end_time_minutes == row.job_start_time_minutes + row.job_duration_minutes
    ASSERT row[i].job_start_time_minutes >= row[i-1].job_end_time_minutes (no overlap)
  END FOR
  ASSERT max(job_end_time_minutes) <= engineer.working_hours * 60
  ASSERT set(reported_job_ids) == set(assigned_job_ids)
  ASSERT len(reported_job_ids) == len(set(reported_job_ids)) (no duplicates)
  ASSERT csv columns == expected_columns
  ASSERT file_name == f"engineer_{id}_schedule.csv"
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many random engineer/job/route configurations automatically
- It catches edge cases that manual unit tests might miss (e.g., single job, jobs at same location, zero travel time)
- It provides strong guarantees that structural invariants hold across all inputs

**Test Plan**: Run the existing passing tests on unfixed code to capture correct baseline behavior, then verify these continue to pass after fix.

**Test Cases**:
1. **Sequential Timing Preservation** (`test_sequential_timing_no_overlap`): Verify jobs don't overlap after fix
2. **Working Hours Preservation** (`test_working_hours_window`): Verify all jobs still fit within working hours
3. **No Missing Jobs Preservation** (`test_no_missing_jobs`): Verify all assigned jobs still appear
4. **No Duplicates Preservation** (`test_no_duplicate_jobs`): Verify no duplicate jobs after fix
5. **Time Calculation Preservation** (`test_time_calculations`): Verify `end = start + duration` still holds
6. **CSV Format Preservation** (`test_csv_format`): Verify column structure unchanged

### Unit Tests

- Test `_calculate_job_timings` returns correct `travel_time_minutes` for known travel matrix values
- Test `_calculate_job_timings` returns records sorted by `job_time`
- Test `generate_report` writes `total_time_minutes = duration + travel` for each row
- Test `generate_report` appends TOTAL row with correct aggregates
- Test edge cases: single job (travel from home only), all jobs at same location (zero inter-job travel), engineer with no jobs (skipped)

### Property-Based Tests

- Generate random engineer locations, job locations, and travel matrices; verify `travel_time_minutes` matches matrix lookup × 60
- Generate random job durations and travel times; verify `total_time_minutes == duration + travel` for all rows
- Generate random multi-job assignments; verify TOTAL row sums match detail row sums exactly
- Generate random job time strings; verify output order matches sorted job times
- Generate random valid inputs; verify all preservation properties (no overlap, within hours, no duplicates, end = start + duration)

### Integration Tests

- Test full scheduling pipeline → report generation with realistic multi-engineer, multi-job scenarios
- Test that `tests/test_report_correctness.py` all pass after fix (10 tests)
- Test report generation with edge cases from the scheduler (unassigned jobs, single-job engineers)
