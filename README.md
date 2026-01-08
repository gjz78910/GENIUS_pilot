# Scheduling Tool - GENIUS Pilot Experiment

A Python scheduling system that assigns field engineers to jobs and optimises travel routes.

---

## For Participants

### What This System Does

1. **Assigns jobs to engineers** based on:
   - Skill match (engineer must have all required skills)
   - Location proximity (closest engineer gets the job)

2. **Optimises travel routes** using brute-force TSP (travelling salesperson)

### Project Structure

```
├── src/
│   ├── demo.py              # Demo script: python -m src.demo
│   ├── models/
│   │   ├── engineer.py      # Engineer: id, name, location, skills, working_hours
│   │   └── job.py           # Job: id, location, time, required_skills, length
│   ├── scheduling/
│   │   └── scheduler.py     # Ties assignment + routing together
│   ├── optimization/
│   │   ├── matching.py      # Assigns jobs to engineers
│   │   └── routing.py       # Finds shortest travel route
│   └── features/
│       ├── report.py        # CSV report generation
│       └── data_loader.py   # Load data from JSON files
├── data/
│   ├── sample_data.py       # Random data generator (10 engineers, 100 jobs)
│   ├── travel_matrix.py      # Travel time matrix
│   ├── benchmarks/          # Benchmark instances with known optimal solutions
│   └── external/            # Example JSON data files
├── tests/
│   ├── test_benchmarks.py    # Benchmark validation tests
│   ├── test_report_correctness.py  # Report correctness tests
│   ├── test_data_loader.py   # Data loading tests
│   └── performance/          # Performance tests (separate from correctness)
└── reports/                  # Generated CSV reports (created at runtime)
```

### Setup

**Using Conda (Recommended):**

```bash
# Create conda environment
conda env create -f environment.yml

# Activate environment
conda activate genius_pilot

# Install dependencies (if any)
pip install -r requirements.txt
```

**Using Python directly:**

```bash
# Ensure Python 3.8+ is installed
python --version

# Install dependencies
pip install -r requirements.txt
```

### Run the System

```bash
python -m src.demo
```

### Run Tests

```bash
# Run all correctness tests
python -m unittest discover -s tests -p "test_*.py"

# Run benchmark tests
python -m unittest tests.test_benchmarks

# Run performance tests (may take longer)
python -m unittest discover -s tests/performance
```

### Generate CSV Reports

```python
from src.features.report import generate_report
from src.scheduling.scheduler import Scheduler
from data.sample_data import engineers, jobs
from data.travel_matrix import travel_matrix

scheduler = Scheduler(engineers, jobs, travel_matrix)
assignments, routes, unassigned = scheduler.create_schedule()

generate_report(engineers, assignments, routes, travel_matrix)
# Reports will be written to reports/engineer_{id}_schedule.csv
```

### Load External Data

```python
from src.features.data_loader import load_data
from src.scheduling.scheduler import Scheduler

engineers, jobs, travel_matrix = load_data("data/external/example_data.json")
scheduler = Scheduler(engineers, jobs, travel_matrix)
assignments, routes, unassigned = scheduler.create_schedule()
```

### Key Files to Understand

| File | Purpose |
|------|---------|
| `src/optimization/matching.py` | Job assignment algorithm |
| `src/optimization/routing.py` | Route optimisation (TSP) |
| `data/sample_data.py` | Sample engineers and jobs |
| `data/travel_matrix.py` | Travel distances |

### Sample Data

**Engineers:**
| ID | Name | Location | Skills |
|----|------|----------|--------|
| 1 | Alice | A | repair, install |
| 2 | Bob | B | install |
| 3 | Charlie | C | repair, maintain |
| 4 | Daisy | D | maintain, repair, install |

**Jobs:**
| ID | Location | Time | Required Skills |
|----|----------|------|-----------------|
| 1 | D | 09:00 | repair |
| 2 | B | 10:00 | install |
| 3 | C | 11:00 | maintain |
| 4 | A | 12:00 | install |
| 5 | A | 13:00 | repair, install |

**Travel Matrix (distances):**
```
    A    B    C    D
A   0   10   15   20
B  10    0   35   25
C  15   35    0   30
D  20   25   30    0
```

---

## For Experiment Conductors

### Pre-Session Checklist

- [ ] Python 3.8+ installed
- [ ] VS Code (or IDE) ready with Amazon Q Developer (for AI group)
- [ ] Screen recording software running
- [ ] This folder cloned/copied to participant machine

### Verify Setup Works

Run these commands to confirm:

```bash
# Check Python version
python --version

# Run tests (should pass all 4)
python -m unittest discover -s tests

# Run main program (should show assignments)
python -m src.demo
```

Expected test output:
```
Ran 4 tests in 0.001s
OK
```

### Benchmark Instances

Small benchmark instances with known optimal solutions are available in `data/benchmarks/`:
- `benchmark_small_01.json` - 2 engineers, 3 jobs
- `benchmark_small_02.json` - 3 engineers, 5 jobs
- `benchmark_small_03.json` - 2 engineers, 4 jobs (with unassignable jobs)

These can be used to validate solution quality and measure "distance to optimal".

### Performance Test Instances

Larger performance test instances are available in `data/performance/` for scalability testing:
- `performance_1000_jobs.json` - 50 engineers, 1000 jobs, 200 locations
- `performance_5000_jobs.json` - 100 engineers, 5000 jobs, 500 locations
- `performance_10000_jobs.json` - 200 engineers, 10000 jobs, 1000 locations

These instances are used by performance tests to measure runtime efficiency and scalability.

### CSV Reporting

The system generates per-engineer CSV reports with timing information in minutes:
- One file per engineer: `reports/engineer_{id}_schedule.csv`
- Columns: engineer_id, engineer_name, job_id, job_location, job_time, required_skills, job_start_time_minutes, job_end_time_minutes, job_duration_minutes, travel_time_minutes, total_time_minutes
- Reports validate: sequential timing, working-hours constraints, no missing/duplicate jobs
- Includes all required fields per experiment design: job ID, location, time, required skills, and travel time

### External Data Loading

Load data from JSON files using `src.features.data_loader.load_data()`:
- Format: JSON object with "engineers", "jobs", and "travel_matrix" keys
- See `data/external/example_data.json` for example format
- Full format specification documented in `data_loader.py` docstring
- Validates: required fields, location references, duplicate IDs
