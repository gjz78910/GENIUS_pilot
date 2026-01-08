# Project Structure

## Directory Organization

```
genIUS/
├── src/                    # Main application source code
│   ├── models/            # Data models (Engineer, Job)
│   ├── optimization/      # Core algorithms (matching, routing)
│   ├── scheduling/        # High-level scheduler orchestration
│   ├── features/          # Extension features (stubs)
│   └── main.py           # Application entry point
├── data/                  # Sample data and configuration
│   ├── sample_data.py    # Test engineers and jobs
│   └── travel_matrix.py  # Distance matrix between locations
├── tests/                 # Unit tests
│   ├── test_models.py    # Model validation tests
│   └── test_scheduler.py # Scheduler integration tests
├── .amazonq/             # Amazon Q configuration
│   └── rules/
│       └── memory-bank/  # Project documentation
├── README.md             # Project documentation
├── requirements.txt      # Python dependencies (empty - stdlib only)
└── .gitignore           # Git ignore patterns
```

## Core Components

### 1. Models Layer (`src/models/`)

**Purpose**: Define core data structures for the scheduling system

- **engineer.py**: Engineer entity with id, name, location, and skills
- **job.py**: Job entity with id, location, scheduled time, and required skills

**Responsibilities**:
- Data validation and normalization (e.g., lowercase skills)
- Encapsulate domain entities
- Provide clean interfaces for business logic

### 2. Optimization Layer (`src/optimization/`)

**Purpose**: Implement core scheduling algorithms

- **matching.py**: Job-to-engineer assignment algorithm
  - Skill-based filtering
  - Distance-based selection
  - Returns assignment mapping

- **routing.py**: Travel route optimization
  - Brute-force TSP implementation
  - Calculates shortest path through assigned jobs
  - Returns optimized job sequence and total distance

**Responsibilities**:
- Implement assignment logic
- Optimize travel routes
- Calculate distances and costs

### 3. Scheduling Layer (`src/scheduling/`)

**Purpose**: Orchestrate the complete scheduling workflow

- **scheduler.py**: Main scheduler class
  - Coordinates matching and routing
  - Manages engineer-job assignments
  - Produces final schedules with routes

**Responsibilities**:
- High-level workflow coordination
- Integration of matching and routing algorithms
- Schedule generation and validation

### 4. Features Layer (`src/features/`)

**Purpose**: Extended functionality (intentionally incomplete for experiments)

- **report.py**: Report generation (STUB)
  - Should generate CSV/text output
  - Format assignment results
  - Export schedules

- **data_loader.py**: External data loading (STUB)
  - Should load engineers from JSON/CSV
  - Should load jobs from files
  - Parse travel matrices

**Responsibilities**:
- I/O operations
- Data formatting and export
- External system integration

### 5. Data Layer (`data/`)

**Purpose**: Provide sample data and configuration

- **sample_data.py**: Hardcoded test data
  - 4 sample engineers (Alice, Bob, Charlie, Daisy)
  - 5 sample jobs with various skill requirements
  - Factory functions for creating test data

- **travel_matrix.py**: Distance configuration
  - Symmetric distance matrix
  - Locations: A, B, C, D
  - Used by routing algorithm

**Responsibilities**:
- Provide test data for development
- Define location relationships
- Support unit testing

### 6. Entry Point (`src/main.py`)

**Purpose**: Demonstrate system functionality

**Responsibilities**:
- Load sample data
- Initialize scheduler
- Execute scheduling workflow
- Display results to console

## Architectural Patterns

### Layered Architecture

```
┌─────────────────────────────────┐
│      Entry Point (main.py)      │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│   Scheduling Layer (scheduler)   │
└────────┬───────────┬─────────────┘
         │           │
┌────────▼─────┐ ┌──▼──────────────┐
│   Matching   │ │     Routing     │
│  (optimize)  │ │   (optimize)    │
└────────┬─────┘ └──┬──────────────┘
         │          │
┌────────▼──────────▼─────────────┐
│      Models (Engineer, Job)      │
└──────────────────────────────────┘
```

### Key Design Principles

1. **Separation of Concerns**: Each layer has distinct responsibilities
2. **Dependency Direction**: Higher layers depend on lower layers, not vice versa
3. **Data-Driven**: Models are pure data structures with minimal logic
4. **Algorithm Isolation**: Optimization algorithms are independent and testable
5. **Extensibility**: Stub features allow for future expansion

## Component Relationships

### Data Flow

1. **Input**: Engineers and Jobs loaded from data layer
2. **Matching**: Optimization layer assigns jobs to engineers
3. **Routing**: Optimization layer calculates optimal routes
4. **Scheduling**: Scheduler coordinates and combines results
5. **Output**: Console display (or reports via features layer)

### Dependencies

- **scheduler.py** → matching.py, routing.py, models
- **matching.py** → Engineer, Job, travel_matrix
- **routing.py** → travel_matrix
- **main.py** → scheduler, sample_data
- **tests/** → All components

## Module Structure

All packages include `__init__.py` for proper Python module structure:
- `src/__init__.py`
- `src/models/__init__.py`
- `src/optimization/__init__.py`
- `src/scheduling/__init__.py`
- `src/features/__init__.py`
- `data/__init__.py`
- `tests/__init__.py`

## Execution Model

**Command**: `python -m src.main`

**Workflow**:
1. Import sample data (engineers, jobs, travel matrix)
2. Create Scheduler instance
3. Call scheduler.schedule() method
4. Display assignments and routes
5. Show total travel distances

**Testing**: `python -m unittest discover -s tests`
