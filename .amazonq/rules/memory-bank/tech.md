# Technology Stack

## Programming Languages

### Python 3.8+
- **Primary Language**: All application code written in Python
- **Minimum Version**: Python 3.8
- **Rationale**: Standard library only, no external dependencies

## Dependencies

### Standard Library Only
- **No External Packages**: Project uses only Python standard library
- **requirements.txt**: Empty file (present for convention)
- **Key Modules Used**:
  - `itertools`: For permutations in TSP algorithm
  - `unittest`: For testing framework
  - `typing`: For type hints (Optional, List, Dict, Set)

## Build System

### Module-Based Execution
- **No Build Step**: Pure Python, no compilation required
- **Module Execution**: Run using `python -m` syntax
- **Package Structure**: Proper `__init__.py` files for all packages

## Development Commands

### Running the Application

```bash
# Execute main program
python -m src.main

# Expected output: Job assignments and optimized routes
```

### Running Tests

```bash
# Run all tests
python -m unittest discover -s tests

# Run specific test file
python -m unittest tests.test_models
python -m unittest tests.test_scheduler

# Expected: 4 tests pass
```

### Verification Commands

```bash
# Check Python version
python --version

# Verify project structure
ls -R src/ data/ tests/

# Check imports work
python -c "from src.models.engineer import Engineer; print('OK')"
```

## Project Configuration

### Python Path
- **Execution Root**: Project root directory (`genIUS/`)
- **Module Imports**: Use absolute imports from `src`, `data`, `tests`
- **Example**: `from src.models.engineer import Engineer`

### File Structure Requirements
- All packages must have `__init__.py`
- Run commands from project root
- Use `-m` flag for module execution

## Development Environment

### Recommended Setup
- **IDE**: VS Code with Python extension
- **Optional**: Amazon Q Developer plugin (for AI-assisted development)
- **Python Environment**: Virtual environment recommended but not required

### Environment Setup

```bash
# Optional: Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# No packages to install (stdlib only)
```

## Code Quality Tools

### Built-in Testing
- **Framework**: unittest (Python standard library)
- **Test Location**: `tests/` directory
- **Test Files**: `test_models.py`, `test_scheduler.py`
- **Coverage**: Models and scheduler integration

### Type Hints
- **Usage**: Optional type hints throughout codebase
- **Types Used**: `Optional`, `List`, `Dict`, `Set`, `Tuple`
- **No Type Checker**: Not enforced, documentation only

## Version Control

### Git Configuration
- **.gitignore**: Excludes Python cache files
  - `__pycache__/`
  - `*.pyc`
  - `*.pyo`
  - `.pytest_cache/`
  - `venv/`

## Platform Compatibility

### Operating Systems
- **Linux**: Fully supported
- **macOS**: Fully supported
- **Windows**: Fully supported

### Python Compatibility
- **Minimum**: Python 3.8
- **Tested**: Python 3.8+
- **Features Used**: Type hints, f-strings, dataclasses-style classes

## Performance Characteristics

### Algorithm Complexity
- **Matching**: O(n × m) where n = engineers, m = jobs
- **Routing (TSP)**: O(n!) brute-force permutations
- **Limitation**: TSP only practical for < 10 jobs per engineer

### Scalability Constraints
- **Small Scale**: Designed for small job sets
- **Brute Force**: Not suitable for production-scale routing
- **Memory**: Minimal, all data in-memory

## Data Formats

### Internal Representation
- **Engineers**: Python objects with attributes
- **Jobs**: Python objects with attributes
- **Travel Matrix**: Nested dictionary `{location: {location: distance}}`
- **Skills**: Sets of lowercase strings

### Future Data Formats (Stubs)
- **JSON**: Planned for data_loader.py
- **CSV**: Planned for report.py and data_loader.py
- **Text**: Planned for report.py output

## Debugging and Troubleshooting

### Common Issues

**ModuleNotFoundError**
```bash
# Solution: Run from project root with -m flag
cd /path/to/genIUS
python -m src.main
```

**Import Errors**
```bash
# Solution: Ensure __init__.py files exist
find . -name "__init__.py"
```

**Test Failures**
```bash
# Solution: Verify Python version
python --version  # Should be 3.8+
```

### Logging and Output
- **Console Output**: Print statements in main.py
- **No Logging Framework**: Simple print-based output
- **Test Output**: unittest default reporter

## Development Workflow

### Typical Development Cycle
1. Edit source files in `src/`
2. Run tests: `python -m unittest discover -s tests`
3. Run application: `python -m src.main`
4. Verify output matches expectations

### Adding New Features
1. Create new module in appropriate package
2. Add `__init__.py` if creating new package
3. Write unit tests in `tests/`
4. Import and integrate in scheduler or main
5. Run full test suite

## Experiment-Specific Setup

### For AI-Assisted Development Group
- Amazon Q Developer plugin installed in VS Code
- Screen recording software running
- Project cloned to participant machine

### For Control Group
- Standard Python development environment
- No AI assistance tools
- Same project structure and requirements
