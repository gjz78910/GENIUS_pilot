# Participant Instructions - Field Engineer Scheduling System

## What This System Does

This is a **field engineer scheduling system** that:
- Assigns jobs to engineers based on their skills and location
- Finds the best travel route for each engineer to visit their assigned jobs
- Generates reports showing each engineer's schedule
- Can load data from external files

**Simple Example:**
- Engineer Alice (at location "A", skills: repair, install) gets assigned Job 1 (at location "A", needs repair skill)
- The system finds the shortest route for Alice to visit all her jobs

---

## Setup Instructions

### Step 1: Activate the Conda Environment

The project uses a conda environment called `genius_pilot`. Activate it:

```bash
conda activate genius_pilot
```

If you see `(genius_pilot)` at the start of your terminal prompt, you're ready!

## Quick Start - Verify Setup and See the System Work

### 1. Verify Setup by Running the Demo

Run the demo to verify everything works:

```bash
python -m src.demo
```

**What you'll see:**
- A list of engineers and which jobs they're assigned
- The travel route for each engineer
- Any jobs that couldn't be assigned

**Example output:**
```
Engineer 1 (Alice) assigned jobs: [1, 3]
  Job time: 3.0h, Travel time: 0.0h
  Total: 3.0h / 8.0h working hours
  Optimal route: A -> A -> A (total travel time 0.0h)
```

If you see output like this, your setup is working! If you see errors, ask for help.

### 2. Try Examples

**Generate a CSV Report:**
```bash
python -c "
from src.features.report import generate_report
from src.scheduling.scheduler import Scheduler
from data.sample_data import engineers, jobs
from data.travel_matrix import travel_matrix

scheduler = Scheduler(engineers, jobs, travel_matrix)
assignments, routes, unassigned = scheduler.create_schedule()
generate_report(engineers, assignments, routes, travel_matrix)
print('Reports generated in reports/ directory')
"
```

Check the `reports/` folder - you'll see CSV files like `engineer_1_schedule.csv` with detailed timing information.

**Load Data from a JSON File:**
```bash
python -c "
from src.features.data_loader import load_data
from src.scheduling.scheduler import Scheduler

engineers, jobs, travel_matrix = load_data('data/benchmarks/benchmark_small_01.json')
scheduler = Scheduler(engineers, jobs, travel_matrix)
assignments, routes, unassigned = scheduler.create_schedule()
print(f'Loaded {len(engineers)} engineers, {len(jobs)} jobs')
print(f'Assigned {sum(len(jobs) for jobs in assignments.values())} jobs')
"
```
This loads data from a JSON file instead of hardcoded sample data, then runs the scheduler and prints a summary.

---

## The Three Tasks

### Task 1: Optimization of Scheduling / Routing

**What you need to do:**
Improve how jobs are assigned to engineers and how travel routes are calculated. The current system is slow and doesn't always find the best solution.

**Where to look:**
- `src/optimization/routing.py` - The routing algorithm (brute-force TSP)
- `src/optimization/matching.py` - The job matching algorithm (bucket/bin sort)

**What's the problem?**
1. **Routing:** The system tries every possible route (brute-force), which is very slow when there are many jobs
2. **Matching:** Jobs are assigned one-by-one to the closest engineer, which can overload some engineers and leave others with no work

**Example of current behavior:**
```python
# Current routing: tries all permutations (slow!)
# For 5 jobs, it tries 5! = 120 different routes
# For 10 jobs, it tries 10! = 3,628,800 routes!

# Current matching: assigns job to closest engineer
# Problem: Engineer A might get 10 jobs while Engineer B gets 0
```

**What you should do:**
1. Read the code in `src/optimization/routing.py` and `src/optimization/matching.py`
2. Understand what they do and why they're slow
3. Improve them using better algorithms (e.g., nearest neighbor, 2-opt for TSP; better matching strategies)
4. Test your changes using the commands below

**How to test:**
```bash
# Test correctness (skills, working hours, no impossible timelines)
python -m unittest tests.test_matching tests.test_routing tests.test_report_correctness -v

# Test solution quality (compares to optimal solutions)
python -m unittest tests.test_benchmarks -v
# Look for "assignment_accuracy" - closer to 1.0 is better (1.0 = perfect match)

# Test performance (runtime on large datasets - takes 5-10 minutes)
python -m unittest discover -s tests/performance -v
# Faster is better - check the printed time in seconds
```

**Success criteria:**
- All correctness tests pass (skills match, working hours respected, no impossible timelines)
- Solution quality improves (assignment_accuracy closer to 1.0 on benchmark instances)
- Performance improves (faster runtime on large datasets)

---

### Task 2: Reporting on Engineer Schedules

**What you need to do:**
Work with the CSV report generation feature. Understand how it works and ensure it meets all requirements.

**Where to look:**
- `src/features/report.py` - The report generation code
- `tests/test_report_correctness.py` - Tests that validate reports

**What the report should include:**
- One line per job per engineer
- Job details: ID, location, time, required skills
- Timing details: start time, end time, duration (all in minutes)
- Travel time to each job
- Total time per job

**Example report structure:**
```csv
engineer_id,engineer_name,job_id,job_location,job_time,required_skills,job_start_time_minutes,job_end_time_minutes,job_duration_minutes,travel_time_minutes,total_time_minutes
1,Alice,1,A,09:00,repair,0.0,120.0,120.0,0.0,120.0
1,Alice,3,A,11:00,install,120.0,180.0,60.0,0.0,60.0
```

**What you should do:**
1. Read `src/features/report.py` to understand how reports are generated
2. Run the report generation: see "Generate a CSV Report" section above
3. Check the generated CSV files in the `reports/` folder
4. Run the correctness tests: `python -m unittest tests.test_report_correctness -v`
5. Verify reports meet requirements: sequential timing, working-hours constraints, no duplicates

**How to test:**
```bash
# Generate a report
python -c "
from src.features.report import generate_report
from src.scheduling.scheduler import Scheduler
from data.sample_data import engineers, jobs
from data.travel_matrix import travel_matrix

scheduler = Scheduler(engineers, jobs, travel_matrix)
assignments, routes, unassigned = scheduler.create_schedule()
generate_report(engineers, assignments, routes, travel_matrix)
"

# Check the reports
ls reports/

# Run correctness tests
python -m unittest tests.test_report_correctness -v
```

**Success criteria:**
- Reports are generated correctly
- All correctness tests pass
- Reports include all required fields
- Timing is sequential and within working hours

---

### Task 3: External Job Data Integration

**What you need to do:**
Work with the external data loading feature. Understand how it loads data from JSON files and ensure it works correctly.

**Where to look:**
- `src/features/data_loader.py` - The data loading code
- `data/benchmarks/benchmark_small_01.json` - Example JSON file format
- `tests/test_data_loader.py` - Tests for data loading

**What the JSON format looks like:**
```json
{
  "engineers": [
    {
      "id": 1,
      "name": "Alice",
      "location": "A",
      "skills": ["repair", "install"],
      "working_hours": 8.0
    }
  ],
  "jobs": [
    {
      "id": 1,
      "location": "A",
      "time": "09:00",
      "required_skills": ["repair"],
      "length": 2.0
    }
  ],
  "travel_matrix": {
    "A": {"A": 0.0, "B": 1.0},
    "B": {"A": 1.0, "B": 0.0}
  }
}
```

**What you should do:**
1. Read `src/features/data_loader.py` to understand how data is loaded
2. Look at example JSON files in `data/benchmarks/` or `data/performance/`
3. Try loading data: see "Load Data from a JSON File" section above
4. Run the data loader tests: `python -m unittest tests.test_data_loader -v`
5. Verify loaded data works with the scheduler

**How to test:**
```bash
# Load and use external data
python -c "
from src.features.data_loader import load_data
from src.scheduling.scheduler import Scheduler

engineers, jobs, travel_matrix = load_data('data/benchmarks/benchmark_small_01.json')
scheduler = Scheduler(engineers, jobs, travel_matrix)
assignments, routes, unassigned = scheduler.create_schedule()
print(f'Loaded: {len(engineers)} engineers, {len(jobs)} jobs')
print(f'Assigned: {sum(len(jobs) for jobs in assignments.values())} jobs')
print(f'Unassigned: {len(unassigned)} jobs')
"

# Run data loader tests
python -m unittest tests.test_data_loader -v
```

**Success criteria:**
- Data loads correctly from JSON files
- All data loader tests pass
- Loaded data works with the scheduler
- Validation catches invalid data

---

## Project Structure

```
├── src/
│   ├── demo.py              # Demo script: python -m src.demo
│   ├── models/              # Engineer and Job classes
│   ├── scheduling/          # Main scheduler
│   ├── optimization/        # Matching and routing algorithms
│   │   ├── matching.py      # Task 1: Job assignment
│   │   └── routing.py       # Task 1: Route optimization
│   └── features/
│       ├── report.py        # Task 2: CSV reports
│       └── data_loader.py   # Task 3: Load JSON data
├── data/
│   ├── sample_data.py       # Sample engineers and jobs
│   ├── benchmarks/          # Small test cases with known solutions
│   └── performance/         # Large test cases for performance
├── tests/                   # All test files
└── reports/                 # Generated CSV reports (created at runtime)
```

---

## Getting Help

If you're stuck:
1. Read the code comments and docstrings
2. Look at the test files for usage examples
3. Try running small examples to understand behavior
4. Ask for clarification if needed
