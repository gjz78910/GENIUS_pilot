# Tests Overview

This folder contains unit, integration, benchmark, and performance tests used by the
participant tasks in `EXPERIMENT_DOCUMENTS/PARTICIPANT_INSTRUCTIONS.md`.

## Test Organization

### test_engineer.py
- Model validation and working-hours rules

### test_job.py
- Job validation and duration rules

### test_matching.py
- Skill matching, capacity, and travel-time integration

### test_routing.py
- Route optimization and travel-time calculation

### test_report_correctness.py
- CSV report correctness and ordering requirements

### test_data_loader.py
- External data validation rules

### test_benchmarks.py
- Benchmark quality metrics (accuracy and travel-time ratio)

### tests/performance/
- Scalability tests (can be slow)

### test_scheduler_integration.py
- End-to-end scheduling integration tests

## Running Tests

### Run all tests (including performance):
```bash
python -m unittest discover -s tests -v
```

### Run correctness tests for Task 1 (matching/routing):
```bash
python -m unittest tests.test_matching tests.test_routing -v
```

### Run Task 2 (reporting) tests:
```bash
python -m unittest tests.test_report_correctness -v
```

### Run Task 3 (data loader) tests:
```bash
python -m unittest tests.test_data_loader -v
```

### Run benchmark tests:
```bash
python -m unittest tests.test_benchmarks -v
```

### Run performance tests (slow):
```bash
python -m unittest discover -s tests/performance -v
```

### Run a specific test file:
```bash
python -m unittest tests.test_matching -v
```

### Run with coverage:
```bash
python run_tests_with_coverage.py
```

Or manually:
```bash
pip install coverage
coverage run -m unittest discover -s tests -v
coverage report -m
coverage html  # Generates htmlcov/index.html
```

## Coverage (Optional)

If you want coverage locally:
```bash
python run_tests_with_coverage.py
```
