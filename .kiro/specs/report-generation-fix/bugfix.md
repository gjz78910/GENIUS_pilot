# Bugfix Requirements Document

## Introduction

The CSV report generation module (`src/features/report.py`) contains four defects that produce incorrect output in per-engineer schedule CSVs. Travel time between jobs is always reported as 0.0, total time per job is always 0.0, there is no summary (TOTAL) row aggregating metrics, and jobs are listed in TSP route order rather than chronological order by `job_time`. These defects cause 4 failing tests in `tests/test_report_correctness.py`.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN an engineer has jobs at different locations THEN the system writes `travel_time_minutes = 0.0` for every job record instead of the actual computed travel time to reach that job

1.2 WHEN a job record is written to the CSV THEN the system writes `total_time_minutes = 0.0` instead of computing the sum of duration and travel time

1.3 WHEN all job detail rows have been written for an engineer THEN the system does not append a TOTAL summary row with aggregated duration, travel, and total columns

1.4 WHEN an engineer has multiple jobs with different `job_time` values THEN the system outputs jobs in TSP route order rather than sorted chronologically by `job_time`

### Expected Behavior (Correct)

2.1 WHEN an engineer has jobs at different locations THEN the system SHALL write the actual travel time (in minutes) from the previous location to each job's location in the `travel_time_minutes` column

2.2 WHEN a job record is written to the CSV THEN the system SHALL compute `total_time_minutes` as `job_duration_minutes + travel_time_minutes`

2.3 WHEN all job detail rows have been written for an engineer THEN the system SHALL append a final row with `job_id='TOTAL'` containing the sum of `job_duration_minutes`, `travel_time_minutes`, and `total_time_minutes` across all detail rows

2.4 WHEN an engineer has multiple jobs THEN the system SHALL output jobs sorted in ascending chronological order by their `job_time` field (e.g., 09:00 before 10:00 before 11:00)

### Unchanged Behavior (Regression Prevention)

3.1 WHEN a report is generated THEN the system SHALL CONTINUE TO produce one CSV file per engineer named `engineer_{id}_schedule.csv`

3.2 WHEN a report is generated THEN the system SHALL CONTINUE TO include the correct CSV columns: engineer_id, engineer_name, job_id, job_location, job_time, required_skills, job_start_time_minutes, job_end_time_minutes, job_duration_minutes, travel_time_minutes, total_time_minutes

3.3 WHEN jobs are assigned to an engineer THEN the system SHALL CONTINUE TO include all assigned jobs in the report with no duplicates or missing entries

3.4 WHEN a report is generated THEN the system SHALL CONTINUE TO compute `job_end_time_minutes = job_start_time_minutes + job_duration_minutes` correctly for each job

3.5 WHEN a report is generated THEN the system SHALL CONTINUE TO ensure jobs do not overlap in time (each job starts at or after the previous job ends plus travel)

3.6 WHEN a report is generated THEN the system SHALL CONTINUE TO ensure all jobs fit within the engineer's working hours window
