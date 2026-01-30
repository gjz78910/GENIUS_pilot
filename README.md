# GENIUS Pilot - Field Engineer Scheduling

Python system that assigns engineers to jobs and finds shortest travel routes.

## What It Does

1. Assigns jobs to engineers by skills and location
2. Finds shortest travel routes (TSP)

## Structure

```
├── src/                    # Main code
│   ├── models/            # Engineer and Job classes
│   ├── optimization/      # Matching and routing
│   ├── scheduling/        # Scheduler
│   └── features/          # Reports and data loading
├── data/                   # Test data and benchmarks
├── tests/                  # Unit and performance tests
├── EXPERIMENT_DOCUMENTS/   # Participant instructions
├── SCRIPTS/                # Experiment scripts
└── reports/                # Generated CSV reports
```

## Setup

```bash
# Using conda
conda env create -f environment.yml
conda activate genius_pilot
pip install -r requirements.txt

# Or using pip
pip install -r requirements.txt
```

## Run

```bash
# Run demo
python -m src.demo

# Run tests
python -m unittest discover -s tests
```

## Key Files

- `src/optimization/matching.py` - Job assignment
- `src/optimization/routing.py` - Route optimization
- `data/sample_data.py` - Sample data
- `tests/test_benchmarks.py` - Benchmark tests
- `tests/performance/test_scalability.py` - Performance tests

## For Participants

See `EXPERIMENT_DOCUMENTS/PARTICIPANT_INSTRUCTIONS.md` for full instructions.
