# Requirements Document

## Introduction

This document specifies the requirements for the two-pass matching feature in the job-to-engineer assignment system. The feature replaces the existing single-pass greedy matching algorithm with a two-pass approach that prioritizes exclusive job assignments before applying greedy closest-engineer logic to remaining jobs. This prevents scenarios where multi-skilled engineers are consumed by shared-skill jobs, leaving exclusive-skill jobs unassignable.

## Glossary

- **Matching_Engine**: The `assign_jobs` function and its internal components responsible for assigning jobs to engineers
- **Eligibility_Map**: A mapping from each job to the list of engineers qualified to perform it based on skill requirements
- **Exclusive_Job**: A job for which only one engineer (or very few engineers, up to the exclusivity threshold) possesses the required skills
- **Exclusivity_Threshold**: The maximum number of eligible engineers for a job to be classified as exclusive (default: 1)
- **Capacity**: The remaining working hours available for an engineer after accounting for assigned job durations and estimated travel time
- **Travel_Matrix**: A dictionary representing travel time in hours between all pairs of locations
- **Pass_1**: The first assignment phase that handles exclusive jobs sorted by exclusivity score (fewest eligible engineers first)
- **Pass_2**: The second assignment phase that assigns remaining jobs using greedy closest-engineer logic

## Requirements

### Requirement 1: Build Eligibility Map

**User Story:** As a scheduling system, I want to pre-compute which engineers qualify for each job, so that both assignment passes can efficiently determine candidate engineers.

#### Acceptance Criteria

1. WHEN the Matching_Engine receives a list of engineers and jobs, THE Matching_Engine SHALL compute an Eligibility_Map that maps each job to all engineers possessing every required skill for that job
2. WHEN a job requires no skills, THE Matching_Engine SHALL include all engineers as eligible for that job
3. WHEN no engineer possesses all required skills for a job, THE Matching_Engine SHALL map that job to an empty list of eligible engineers
4. WHEN a job maps to an empty eligibility list, THE Matching_Engine SHALL immediately classify that job as unassigned without attempting assignment

### Requirement 2: Exclusive Job Identification and Priority Assignment

**User Story:** As a scheduler operator, I want jobs with limited engineer options assigned first, so that rare-skill engineers are reserved for jobs only they can handle.

#### Acceptance Criteria

1. WHEN the Eligibility_Map is built, THE Matching_Engine SHALL identify exclusive jobs as those with a number of eligible engineers less than or equal to the Exclusivity_Threshold
2. WHEN processing exclusive jobs in Pass_1, THE Matching_Engine SHALL sort them in ascending order by number of eligible engineers (most constrained first)
3. WHEN assigning an exclusive job, THE Matching_Engine SHALL select the closest eligible engineer with sufficient capacity
4. WHEN an exclusive job cannot be assigned in Pass_1 due to insufficient capacity, THE Matching_Engine SHALL defer that job to Pass_2 for a second assignment attempt
5. WHEN all exclusive jobs have been processed, THE Matching_Engine SHALL pass remaining jobs (non-exclusive jobs plus deferred exclusive jobs) to Pass_2

### Requirement 3: Greedy Assignment of Remaining Jobs

**User Story:** As a scheduler operator, I want remaining jobs assigned to the closest available engineer, so that travel time is minimized for non-exclusive work.

#### Acceptance Criteria

1. WHEN Pass_2 processes remaining jobs, THE Matching_Engine SHALL sort eligible engineers for each job by travel distance from the engineer's location to the job's location in ascending order
2. WHEN assigning a remaining job, THE Matching_Engine SHALL attempt assignment to the closest eligible engineer first, falling back to the next closest if capacity is exceeded
3. IF no eligible engineer has sufficient capacity for a remaining job, THEN THE Matching_Engine SHALL add that job to the unassigned list

### Requirement 4: Capacity Validation

**User Story:** As a scheduler operator, I want accurate capacity checks that include travel time, so that no engineer is overloaded beyond their working hours.

#### Acceptance Criteria

1. WHEN evaluating whether a new job fits an engineer's capacity, THE Matching_Engine SHALL compute total load as the sum of all assigned job durations plus estimated travel time for the complete route including the new job
2. WHEN total load exceeds the engineer's working hours, THE Matching_Engine SHALL reject the assignment and try the next candidate
3. THE Matching_Engine SHALL use the `find_optimal_route` function to estimate travel time for the full set of assigned job locations

### Requirement 5: Assignment Completeness and Correctness

**User Story:** As a scheduler operator, I want every job accounted for with valid assignments, so that no jobs are lost and all constraints are respected.

#### Acceptance Criteria

1. THE Matching_Engine SHALL place every input job in exactly one of: an engineer's assignment list or the unassigned list
2. THE Matching_Engine SHALL never assign a job to more than one engineer
3. THE Matching_Engine SHALL never assign a job to an engineer who lacks any of the job's required skills
4. THE Matching_Engine SHALL maintain an assignments dictionary with an entry for every engineer, including those with no assigned jobs (empty list)

### Requirement 6: Backward Compatibility

**User Story:** As a developer, I want the updated matching to maintain the same function signature and behavior for existing scenarios, so that no existing tests or integrations break.

#### Acceptance Criteria

1. THE Matching_Engine SHALL maintain the existing `assign_jobs` function signature: `(engineers, jobs, travel_matrix) -> tuple[Dict[int, List[Job]], List[Job]]`
2. WHEN no exclusive jobs exist in the input, THE Matching_Engine SHALL produce results equivalent to the previous greedy closest-engineer algorithm
3. THE Matching_Engine SHALL pass all existing tests in `test_matching.py` without modification

### Requirement 7: Benchmark Quality

**User Story:** As a scheduler operator, I want the two-pass matching to solve capacity-skill trade-off and exclusive-skill-trap scenarios, so that benchmarks 4 and 5 pass with optimal solutions.

#### Acceptance Criteria

1. WHEN processing benchmark 4 (capacity-skill trade-off), THE Matching_Engine SHALL assign all jobs with zero unassigned jobs
2. WHEN processing benchmark 5 (exclusive skill trap), THE Matching_Engine SHALL assign all jobs with zero unassigned jobs
3. WHEN processing benchmarks 1, 2, and 3, THE Matching_Engine SHALL continue to produce correct results with no regressions

### Requirement 8: Graceful Handling of Edge Cases

**User Story:** As a developer, I want the matching engine to handle degenerate inputs gracefully, so that the system remains robust.

#### Acceptance Criteria

1. WHEN the engineers list is empty, THE Matching_Engine SHALL return an empty assignments dictionary and all jobs as unassigned
2. WHEN the jobs list is empty, THE Matching_Engine SHALL return an assignments dictionary with empty lists for each engineer and an empty unassigned list
3. IF a location referenced by a job or engineer is not present in the Travel_Matrix, THEN THE Matching_Engine SHALL treat the travel distance as infinite, preventing assignment to unreachable engineers
