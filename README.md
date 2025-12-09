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
│   ├── main.py              # Run this to see the system work
│   ├── models/
│   │   ├── engineer.py      # Engineer: id, name, location, skills
│   │   └── job.py           # Job: id, location, time, required_skills
│   ├── scheduling/
│   │   └── scheduler.py     # Ties assignment + routing together
│   ├── optimization/
│   │   ├── matching.py      # Assigns jobs to engineers
│   │   └── routing.py       # Finds shortest travel route
│   └── features/
│       ├── report.py        # STUB - not implemented
│       └── data_loader.py   # STUB - not implemented
├── data/
│   ├── sample_data.py       # 4 engineers, 5 jobs
│   └── travel_matrix.py     # Distances between locations A, B, C, D
└── tests/
    ├── test_models.py
    └── test_scheduler.py
```

### Run the System

```bash
python -m src.main
```

### Run Tests

```bash
python -m unittest discover -s tests
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
python -m src.main
```

Expected test output:
```
Ran 4 tests in 0.001s
OK
```

### Experiment Tasks

Participants may be asked to:

1. **Read and understand** the existing code
2. **Extend matching logic** (e.g., add workload balancing)
3. **Extend routing logic** (e.g., handle time constraints)
4. **Implement report.py** (generate CSV/text output)
5. **Implement data_loader.py** (load from JSON/CSV files)

### Feature Stubs

Two files are intentionally unfinished for development tasks:

- `src/features/report.py` - Should generate assignment reports
- `src/features/data_loader.py` - Should load data from files

### Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | Run from project root: `python -m src.main` |
| Tests fail | Check Python 3.8+ is used |
| Import errors | Ensure you're in the `GENIUS_pilot` directory |

---

## Technical Notes

- No external dependencies (standard library only)
- Skills are case-insensitive (auto-converted to lowercase)
- TSP is brute-force (works for small job sets only)
- Travel matrix must have all location pairs defined
