# Participant Instructions

## ⚠️ IMPORTANT: What You CAN and CANNOT Use

**Your assigned condition will determine which tools you can use:**

### If you are in the MANUAL coding condition:
**✅ YOU CAN USE:**
- Google search
- Stack Overflow
- Python documentation
- Any online tutorials or guides

**❌ YOU CANNOT USE:**
- **NO AI chatbots** (ChatGPT, Claude, Gemini, etc.)
- **NO AI coding assistants in your IDE** (Q Developer, GitHub Copilot, etc.)
- **NO AI code completion tools**
- **NO AI-powered search engines** (Perplexity AI, etc.)

**Why?** This part of the study is about coding without AI assistance. We want to see how you solve problems using traditional methods.

### If you are in the AI-ASSISTED coding condition:
**✅ YOU CAN USE:**
- **Amazon Q Developer AI assistant** in VS Code (installed and ready to use)
- **AI chatbots** (ChatGPT, Claude, Gemini, etc.) - if you want
- Google search
- Stack Overflow
- Any online tutorials or guides


## What This System Does

This is a **field engineer scheduling system** that:
- Assigns jobs to engineers based on their skills and location
- Finds the best travel route for each engineer to visit their assigned jobs
- Generates reports showing each engineer's schedule
- Can load data from external files

**Simple Example:**

Imagine you have a company that sends engineers to customers' homes or offices to fix things.

- **Engineer Alice** is currently at **Location A**
- Alice knows how to do **repair work** and **installation work**
- A customer at **Location A** needs their internet router **repaired**
- The system looks at all available engineers and says: "Alice is at Location A, she knows how to repair things, and the job is also at Location A - perfect match!"
- The system assigns this job to Alice
- If Alice has multiple jobs, the system figures out the best order to visit them (like Google Maps finding the fastest route)
- At the end, the system creates a schedule showing: "Alice will be at Location A from 9:00 AM to 11:00 AM, then travel to Location B for her next job..."



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



## ✅ Success Criteria

### 1. Correctness Tests

```bash
python -m unittest tests.test_matching tests.test_routing tests.test_report_correctness -v
```

**What you'll see:** All tests show `ok` (pass) or `FAIL` (fail)

**Pass:** All tests must pass - this means your code follows all rules (skills, working hours, constraints)

---

### 2. Quality Benchmarks

```bash
python -m unittest tests.test_benchmarks -v
```

**Look for printed metrics:** The tests will print `assignment_accuracy` and `travel_time_ratio`

**Target for all benchmarks:**
- `assignment_accuracy = 1.0`
- `travel_time_ratio ≤ 1.5` (optimal = 1.0)

**Your goal:** Maintain these values (don't make quality worse!)

**Example output:**
```
Benchmark 1 Metrics:
  assignment_accuracy: 1.000 (target: 1.0)
  travel_time_ratio: 1.000 (target: ≤ 1.5)
```

---

### 3. Performance Tests (Progressive Difficulty)

```bash
python -m unittest discover -s tests/performance -v
```

**Pass:**
- **Test 1 (EASY):** Should pass with original code (< 10s)
- **Test 2 (MODERATE):** Needs some optimization (~50-60s original, < 5s optimized)
- **Test 3 (HARD):** Needs significant optimization (> 10 minutes original, < 10s optimized)
- **Test 4 (VERY HARD):** Needs major optimization (> 30 minutes original, < 15s optimized)
- **Test 5 (EXTREMELY HARD):** Requires full optimization (> 1 hour original, < 20s optimized)

**Your target:** Optimize routing progressively so all tests pass in reasonable time

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

## ✅ Success Criteria

```bash
python -m unittest tests.test_report_correctness -v
```
**Pass:** All tests show `ok`

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

## ✅ Success Criteria

```bash
python -m unittest tests.test_data_loader -v
```
**Pass:** All tests show `ok`

---

## How to Know You've Succeeded

### Quick Check

After completing your task, run:
```bash
# Run all correctness tests
python -m unittest discover -s tests -p "test_*.py" -v
```

**If you see:**
```
----------------------------------------------------------------------
Ran 10 tests in 0.234s

OK
```
✅ **Success!** All tests pass.

**If you see:**
```
----------------------------------------------------------------------
Ran 10 tests in 0.234s

FAILED (failures=2)
```
⚠️ **Some issues** - Read the error messages and fix them.

### Understanding Test Results

- **"ok"** = Test passed ✅ - You're good!
- **"FAIL"** = Test failed - Read the error message, it tells you what's wrong
- **"ERROR"** = Test crashed - There's a bug in your code, check the error message

**Example good output:**
```
test_skill_matching ... ok
test_working_hours ... ok
----------------------------------------------------------------------
Ran 2 tests in 0.001s
OK
```
✅ This means success!

**Example bad output:**
```
test_skill_matching ... FAIL
test_working_hours ... ok
----------------------------------------------------------------------
Ran 2 tests in 0.001s
FAILED (failures=1)
```
⚠️ One test failed - read the error message above to see what's wrong

