# GENIUS Pilot Experiment - Catchup Meeting Agenda

## 1. Codebase Progress Update

### Task 1 - Optimization (COMPLETE)

- Created 3 small benchmark instances with known optimal solutions (`data/benchmarks/benchmark_small_*.json`)
- Implemented "distance to optimal" metric to measure solution quality (`tests/test_benchmarks.py`)
- Created 3 larger performance test instances (1000, 5000, 10000 jobs) (`data/performance/performance_*.json`)
- Performance tests separated from correctness tests (`tests/performance/test_performance.py`)
- All benchmark validation tests passing (`tests/test_benchmarks.py`)
- Core optimization code: `src/optimization/routing.py`, `src/optimization/matching.py`

### Task 2 - CSV Reporting (COMPLETE)

- CSV report generation implemented (`src/features/report.py`)
- Reports include all required fields: job ID, location, time, required skills, travel time
- Time representation in minutes (as specified)
- Correctness tests validate: sequential timing, working-hours constraints, no duplicates (`tests/test_report_correctness.py`)
- All report tests passing (`tests/test_report_correctness.py`)
- Example reports generated in `reports/` directory

### Task 3 - External Data Loading (COMPLETE)

- JSON data loader implemented with full validation (`src/features/data_loader.py`)
- Example data files provided (`data/benchmarks/`, `data/performance/`)
- Performance instances can be loaded via data loader
- All data loader tests passing (`tests/test_data_loader.py`)

### Participant Materials - Updated (NEW)

- Created separate instruction files for different participant groups:
  - `PARTICIPANT_INSTRUCTIONS_MANUAL.md` - For participants coding without AI tools
    - Clearly specifies: NO AI chatbots, NO AI assistants, NO AI tools
    - Allows: Google, Stack Overflow, documentation, traditional resources
  - `PARTICIPANT_INSTRUCTIONS_AI.md` - For participants using AI assistance
    - Clarifies: Can use Amazon Q Developer in VS Code
    - Also allows other AI tools outside IDE (per experiment design line 95)
    - Emphasizes Q Developer as primary tool
- Improved simple example in instructions to be more understandable for complete outsiders
- Instructions now use clearer, more relatable language (e.g., "internet router repair" instead of abstract examples)

### Waiting On

- Amazon Q Developer license: Requested from King's IT team, should arrive in a few days

### Still To Do

- Test experiments: Run once license is available, verify screen recording
- Participant materials: Surveys and interview guide still to be drafted
- Dry run preparation: Checklist created (can be recreated if needed for actual dry run)

## 2. Next Steps

- **Jingzhi:** Wait for license, then start test experiments and draft participant materials
- **Adam:** Set up GitLab repo automation and coordinate pilot logistics
- **All:** Review codebase and provide feedback if needed

## 3. Recent Updates (Since Last Meeting)

- **Participant Instructions Refinement:**
  - Separated instructions into manual vs AI-assisted versions for clarity
  - Verified alignment with experiment design regarding AI tool usage (line 95 allows AI tools outside IDE)
  - Improved examples to be more accessible to non-technical readers
  - Both instruction files ready for dry run testing

- **Experiment Design Clarification:**
  - Confirmed that AI participants can use AI tools outside IDE (per Experiment_design.md line 95)
  - Primary focus remains on Q Developer plugin usage within IDE
  - Instructions updated to reflect this flexibility while emphasizing Q Developer