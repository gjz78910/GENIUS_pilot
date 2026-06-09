# Implementation Plan: Two-Pass Matching

## Overview

Refactor `assign_jobs` in `src/optimization/matching.py` to use a two-pass strategy: first assign exclusive jobs (those with very few qualified engineers), then assign remaining jobs greedily by proximity. This ensures rare-skill engineers are reserved for jobs only they can handle, fixing benchmarks 4 and 5.

## Tasks

- [x] 1. Add helper functions for eligibility and capacity checking
  - [x] 1.1 Implement `_build_eligibility_map` helper function
    - Add function to `src/optimization/matching.py` that maps each job ID to the list of engineers possessing all required skills
    - Return an empty list for jobs no engineer can handle
    - If a job requires no skills, include all engineers as eligible
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 1.2 Implement `_has_capacity` helper function
    - Add function to `src/optimization/matching.py` that checks whether adding a new job to an engineer's current jobs fits within working hours
    - Compute total load as sum of all job durations plus estimated travel time using `find_optimal_route` for the full route including the new job
    - Return `True` only if total load ≤ engineer's working hours
    - _Requirements: 4.1, 4.2, 4.3_

  - [x]* 1.3 Write unit tests for `_build_eligibility_map` and `_has_capacity`
    - Test eligibility map with various skill combinations (all match, partial match, no match, no required skills)
    - Test capacity check with edge cases (exact capacity, over capacity, zero travel)
    - _Requirements: 1.1, 1.2, 1.3, 4.1, 4.2, 4.3_

- [x] 2. Refactor `assign_jobs` to use two-pass logic
  - [x] 2.1 Implement Pass 1 — exclusive job assignment
    - Identify exclusive jobs (eligibility count ≤ exclusivity threshold, default 1)
    - Sort exclusive jobs by number of eligible engineers ascending (most constrained first)
    - Assign each exclusive job to the closest eligible engineer with capacity
    - Defer unassignable exclusive jobs to Pass 2
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 2.2 Implement Pass 2 — greedy closest-first assignment
    - Process remaining jobs (non-exclusive + deferred exclusive jobs)
    - Sort eligible engineers by travel distance ascending for each job
    - Assign to closest engineer with capacity, fall back to next closest
    - Add to unassigned list if no engineer has capacity
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 2.3 Wire the two passes together in `assign_jobs`
    - Replace the existing single-pass loop with the two-pass structure
    - Use `_build_eligibility_map` to compute eligibility upfront
    - Immediately classify jobs with empty eligibility as unassigned
    - Maintain the existing function signature: `(engineers, jobs, travel_matrix) -> tuple[Dict[int, List[Job]], List[Job]]`
    - Ensure assignments dict has an entry for every engineer (including empty lists)
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 6.1, 8.1, 8.2_

- [x] 3. Checkpoint — Verify existing tests pass
  - Ensure all tests pass (`python -m pytest tests/test_matching.py tests/test_benchmarks.py`), ask the user if questions arise.

- [ ] 4. Add property-based tests for correctness properties
  - [ ]* 4.1 Write property test for assignment completeness
    - **Property 1: Assignment Completeness**
    - Generate random engineers, jobs, and travel matrices using Hypothesis
    - Assert that every input job appears exactly once in either an assignment list or the unassigned list
    - Assert that assignments dict contains an entry for every engineer
    - **Validates: Requirements 5.1, 5.4, 1.4**

  - [ ]* 4.2 Write property test for no duplicate assignments
    - **Property 2: No Duplicate Assignments**
    - Assert that no job ID appears in more than one engineer's assignment list
    - **Validates: Requirement 5.2**

  - [ ]* 4.3 Write property test for skill validity
    - **Property 3: Skill Validity**
    - Assert that every assigned job's required skills are a subset of the assigned engineer's skills
    - **Validates: Requirements 5.3, 1.1**

  - [ ]* 4.4 Write property test for capacity validity
    - **Property 4: Capacity Validity**
    - Assert that each engineer's total load (job durations + optimal route travel time) does not exceed working hours
    - **Validates: Requirements 4.1, 4.2, 4.3**

  - [ ]* 4.5 Write property test for exclusive job assignment
    - **Property 5: Exclusive Job Assignment**
    - For any job where exactly one engineer has the required skills and that engineer has sufficient capacity for the job alone, assert the job is not in the unassigned list
    - **Validates: Requirements 2.1, 2.2, 2.3**

- [x] 5. Verify benchmarks and backward compatibility
  - [x] 5.1 Run benchmarks 4 and 5 and confirm they pass with all jobs assigned
    - Execute `python -m pytest tests/test_benchmarks.py::TestBenchmarksWithOptimal::test_benchmark_small_04 tests/test_benchmarks.py::TestBenchmarksWithOptimal::test_benchmark_small_05 -v`
    - Confirm zero unassigned jobs and assignment accuracy of 1.0
    - _Requirements: 7.1, 7.2_

  - [x] 5.2 Run all existing tests and confirm no regressions
    - Execute `python -m pytest tests/test_matching.py tests/test_benchmarks.py -v`
    - Confirm benchmarks 1, 2, 3 still pass
    - Confirm all unit tests in test_matching.py pass without modification
    - _Requirements: 6.2, 6.3, 7.3_

- [x] 6. Final checkpoint — Ensure all tests pass
  - Run full test suite (`python -m pytest tests/ -v`), ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- The design uses Python, so all implementations target `src/optimization/matching.py`
- Property tests use the `hypothesis` library — add to `requirements.txt` if not present
- The exclusivity threshold defaults to 1 (only jobs with exactly one eligible engineer are exclusive in Pass 1)
- Checkpoints ensure incremental validation before moving forward
