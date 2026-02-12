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
- **AI chatbots** (ChatGPT, Claude, Gemini, etc.) 


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



## Getting Started

### Time Limit

You have **2 hours** total for this experiment.

Work at your normal pace, but keep an eye on time.
If you cannot finish everything, complete as much as you can in 2 hours.

### Setup

Activate the conda environment:

```bash
conda activate genius_pilot
```

Run this command to confirm you are on your participant branch:
```bash
git branch --show-current
```
Expected output:
```bash
participant/<ID>
```

> **Note:** A resource monitoring script is running in a separate terminal. Please use **your own terminal** for all your work — do not close or interfere with the other terminal.


### Project Structure

```
├── src/                    # Main source code
│   ├── models/            # Data classes (Engineer, Job)
│   ├── optimization/      # Algorithms for matching and routing
│   ├── scheduling/        # High-level scheduler
│   └── features/          # Reports, data loading, etc.
├── data/                   # Sample data and benchmark files
├── tests/                  # Unit tests and performance tests
│   └── performance/       # Scalability tests
└── reports/                # Generated CSV reports
```

Take a few minutes to explore the code.

### Task 1 quick check: demo, then tests

```bash
python -c "from src.models.engineer import Engineer; from src.models.job import Job; from src.scheduling.scheduler import Scheduler; engineers=[Engineer(1,'Alice','A',['repair'],8.0),Engineer(2,'Bob','B',['install'],8.0)]; jobs=[Job(1,'A','09:00',['repair'],1.0),Job(2,'B','10:00',['install'],1.0),Job(3,'B','11:00',['repair'],1.0)]; travel={'A':{'A':0.0,'B':0.5},'B':{'A':0.5,'B':0.0}}; a,r,u=Scheduler(engineers,jobs,travel).create_schedule(); print('Assignments:', {k:[j.id for j in v] for k,v in a.items()}); print('Routes:', r); print('Unassigned:', [j.id for j in u])"
```
This shows:
- job assignments
- routes
- any unassigned jobs

```bash
python -m unittest tests.test_matching tests.test_routing tests.test_benchmarks -v
```

- `ok` means that part works
- `FAIL` or `ERROR` means that part still needs to be fixed

### Task 2 quick check: demo, then tests

```bash
python -c "from data.sample_data import engineers,jobs; from data.travel_matrix import travel_matrix; from src.scheduling.scheduler import Scheduler; from src.features.report import generate_report; a,r,u=Scheduler(engineers,jobs,travel_matrix).create_schedule(); generate_report(engineers,a,r,travel_matrix); print('Report files created in reports/')"
```
This shows:
- report CSV files are created in `reports/`

```bash
python -m unittest tests.test_report_correctness -v
```

- `ok` means reporting works
- `FAIL` or `ERROR` means reporting logic is wrong or missing

### Task 3 quick check: demo, then tests

```bash
python -c "from src.features.data_loader import load_data; e,j,t=load_data('data/external/example_data.json'); print(f'Loaded {len(e)} engineers, {len(j)} jobs, {len(t)} locations')"
```
This shows:
- external data can be loaded
- how many engineers, jobs, and locations were loaded

```bash
python -m unittest tests.test_data_loader -v
```

- `ok` means input handling is correct
- `FAIL` or `ERROR` means validation is missing or incorrect

Read error messages carefully. They tell you what to fix.



## The Three Tasks

### Task 1: Improve Matching & Routing

**What you need to do:**
Improve how jobs are assigned/matched to engineers and how travel routes are calculated. 
The current system is slow and doesn't always find the best solution.

**What's the problem?**
1. **Routing:** The system tries every possible route (brute-force), which is very slow when there are many jobs
2. **Matching:** Jobs are assigned one-by-one to the closest engineer, which can overload some engineers and leave others with no work

**What you should do:**
1. Explore the codebase to find the routing and matching code
2. Understand what the algorithms do and why they're slow
3. Improve routing code, run and pass Checkpoint A below
4. Improve matching code, run and pass Checkpoint B below
5. Run Checkpoint C below, and make sure Checkpoint A and B tests still pass


## ✅ Success Criteria

### 1. Checkpoint A (Routing)

**To pass Checkpoint A:**
- Run `python -m unittest tests.test_routing tests.test_routing_checkpoint_a tests.test_benchmarks.TestBenchmarksWithOptimal.test_benchmark_small_01 tests.test_benchmarks.TestBenchmarksWithOptimal.test_benchmark_small_02 tests.test_benchmarks.TestBenchmarksWithOptimal.test_benchmark_small_03 tests.test_benchmarks.TestBenchmarksWithOptimal.test_brute_force_routing_optimal -v`, and:
  - every test shows `ok`
  - route quality is reasonable in benchmark output (`travel_time_ratio <= 1.5`)

---

### 2. Checkpoint B (Matching)

**To pass Checkpoint B:**
- Run `python -m unittest tests.test_matching tests.test_benchmarks.TestBenchmarksWithOptimal.test_benchmark_small_04 tests.test_benchmarks.TestBenchmarksWithOptimal.test_benchmark_small_05 tests.test_routing -v`, and:
  - every test shows `ok`
  - printed benchmark metrics meet:
    - `assignment_accuracy = 1.0`
    - `travel_time_ratio <= 1.5`
  - all jobs are assigned in both tests (no unassigned jobs)

---

### 3. Checkpoint C (Scalability)

**To pass Checkpoint C:**
- Run `python -m unittest tests.performance.test_scalability tests.test_routing tests.test_matching tests.test_benchmarks -v`, and:
    - **Test 1 (EASY):** Should pass with original code (by default finish < 3s)
    - **Test 2 (MODERATE):** Needs some optimization (finish < 5s to pass)
    - **Test 3 (HARD):** Needs significant optimization (finish < 10s to pass)
    - **Test 4 (VERY HARD):** Needs major optimization (finish < 15s to pass)
    - **Test 5 (EXTREMELY HARD):** Requires full optimization (finish < 30s to pass)
  - **Your target:** pass at least three tests
  - this command also confirms your scalability changes did not break routing, matching, and benchmark behavior

---

### Task 2: Reporting on Engineer Schedules

**What you need to do:**
The CSV report code has bugs and a missing feature. Some tests will fail. Fix the code so all tests pass.

**Start by running the tests to see what fails:**
```bash
python -m unittest tests.test_report_correctness -v
```

Read the failure messages carefully — they tell you what is wrong and will guide you to the relevant code.

**Steps:**
1. Run the tests to see which ones fail
2. Read the error messages to understand what behavior is expected
3. Find and fix the bugs in the report code
4. Run the tests again until all pass

## ✅ Success Criteria

```bash
python -m unittest tests.test_report_correctness -v
```
**Pass:** All tests show `ok`

---

### Task 3: External Job Data Integration

**What you need to do:**
The data loader is missing some input validation. Some tests will fail. Add the missing validation so all tests pass.

**Start by running the tests to see what fails:**
```bash
python -m unittest tests.test_data_loader -v
```

Read the failure messages carefully — they tell you what validation is missing and will guide you to the relevant code.

**Steps:**
1. Run the tests to see which ones fail
2. Read the error messages to understand what validation is expected
3. Find the data loading code and add the missing validation checks
4. Run the tests again until all pass

## ✅ Success Criteria

```bash
python -m unittest tests.test_data_loader -v
```
**Pass:** All tests show `ok`

## Final Submission

After you finish all tasks and all test commands, submit your work:
```bash
git add .
git commit -m "Final submission"
git push
```

---
