# GENIUS Pilot - Field Engineer Scheduling

Python system that assigns engineers to jobs and finds shortest travel routes.

---

## For Participants

See `EXPERIMENT_DOCUMENTS/PARTICIPANT_INSTRUCTIONS.md` for full instructions on setup, tasks, and success criteria.

**Quick start:**

```bash
conda activate genius_pilot
python -m src.demo
```

---

## For Experiment Organizers

### Setup

1. Clone repo and create conda environment: `conda env create -f environment.yml`
2. Activate: `conda activate genius_pilot`
3. Install dependencies: `pip install -r requirements.txt`
4. Run demo to verify: `python -m src.demo`
5. Run tests to confirm baseline: `python -m unittest tests.test_matching tests.test_routing tests.test_benchmarks tests.test_report_correctness tests.test_data_loader -v`
6. Review `EXPERIMENT_DOCUMENTS/EXPERIMENT_CHECKLIST.md` for the full experiment protocol
7. Collect pre-experiment data (system info, survey) — see `EXPERIMENT_DOCUMENTS/DATA_COLLECTION.md`

### Key Documents

- `EXPERIMENT_DOCUMENTS/EXPERIMENT_CHECKLIST.md` — Full experiment protocol
- `EXPERIMENT_DOCUMENTS/PARTICIPANT_INSTRUCTIONS.md` — What participants see
- `EXPERIMENT_DOCUMENTS/DATA_COLLECTION.md` — Data collection guide

### Between Participants

1. Store work: `./SCRIPTS/store_participant_work.sh <ID> <SESSION>`
2. Reset environment: `./SCRIPTS/reset_environment.sh <ID> <SESSION>`
3. Verify reset: `python -m src.demo`

### Project Structure

```
├── src/                    # Main source code
│   ├── models/            # Engineer and Job classes
│   ├── optimization/      # Matching and routing algorithms
│   ├── scheduling/        # High-level scheduler
│   └── features/          # Reports and data loading
├── data/                   # Sample data and benchmarks
├── tests/                  # Unit and performance tests
├── EXPERIMENT_DOCUMENTS/   # Experiment protocol and participant instructions
├── SCRIPTS/                # Data collection and environment management scripts
└── reports/                # Generated CSV reports
```
