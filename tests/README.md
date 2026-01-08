# Unit Tests

Comprehensive unit tests organized by requirement.

## Test Organization

### test_engineer.py
- **Requirement 2**: Working Hours Management
- Model validation and data normalization
- Tests: 7 tests

### test_job.py
- **Requirement 2**: Job Length (Duration)
- Model validation and data normalization
- Tests: 7 tests

### test_matching.py
- **Requirement 1**: Skill Matching & Location Proximity
- **Requirement 2**: Working Hours & Capacity
- **Requirement 3**: Travel Time Integration
- **Requirement 4**: Overflow Handling
- Tests: 8 tests

### test_routing.py
- **Requirement 5**: Route Optimization (TSP)
- **Requirement 3**: Travel Time (route calculation)
- Tests: 9 tests

### test_scheduler_integration.py
- Integration of all requirements (1-5)
- End-to-end workflow testing
- Tests: 9 tests

## Running Tests

### Run all tests:
```bash
python -m unittest discover -s tests -v
```

### Run specific test file:
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

## Coverage Goals

Target: **>90% coverage** for all modules:
- `src/models/engineer.py`
- `src/models/job.py`
- `src/optimization/matching.py`
- `src/optimization/routing.py`
- `src/scheduling/scheduler.py`

## Test Requirements Mapping

| Requirement | Test Files | Test Count |
|-------------|-----------|------------|
| 1. Skill Matching & Location Proximity | test_matching.py | 3 tests |
| 2. Working Hours & Capacity | test_engineer.py, test_job.py, test_matching.py | 6 tests |
| 3. Travel Time Integration | test_matching.py, test_routing.py | 2 tests |
| 4. Overflow Handling | test_matching.py, test_scheduler_integration.py | 2 tests |
| 5. Route Optimization | test_routing.py, test_scheduler_integration.py | 11 tests |
| Integration & Edge Cases | All test files | 16 tests |

**Total: 40 tests**
