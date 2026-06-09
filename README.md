# GENIUS Pilot - Field Engineer Scheduling

Python system that assigns engineers to jobs and finds shortest travel routes.

---

## For Participants

**Open your instructions file in a browser and follow the steps there.**

| Your group | File to open |
|---|---|
| Manual coding | `EXPERIMENT_DOCUMENTS/PARTICIPANT_INSTRUCTIONS_MANUAL.html` |
| AI-assisted coding | `EXPERIMENT_DOCUMENTS/PARTICIPANT_INSTRUCTIONS_AI.html` |

The instructions will guide you through everything: setup, the three tasks, and submitting your work. All steps are interactive — check each one off as you go.

---

## For Experiment Organizers

### Setup

1. Clone repo and create conda environment: `conda env create -f environment.yml`
2. Activate: `conda activate genius_pilot`
3. Install dependencies: `pip install -r requirements.txt`
4. Run demo to verify: `python -m src.demo`
5. Run tests to confirm baseline: `python -m unittest tests.test_matching tests.test_routing tests.test_benchmarks tests.test_report_correctness tests.test_data_loader -v`
6. Review `EXPERIMENT_DOCUMENTS/organiser/EXPERIMENT_CHECKLIST.html` for the full experiment protocol
7. Collect pre-experiment data (system info, survey) — see `EXPERIMENT_DOCUMENTS/organiser/DATA_COLLECTION.md`

### Key Documents

**Organiser only** (in `EXPERIMENT_DOCUMENTS/organiser/`):
- `EXPERIMENT_CHECKLIST.html` — Session checklist (open in browser)
- `DATA_COLLECTION.md` — Data collection guide
- `AWS_REMOTE_EXPERIMENT_RUNBOOK.md` — AWS VM setup and management

**Participant-facing** (in `EXPERIMENT_DOCUMENTS/`):
- `PARTICIPANT_INSTRUCTIONS_MANUAL.html` — Instructions, manual group
- `PARTICIPANT_INSTRUCTIONS_AI.html` — Instructions, AI group

**Organiser only** — surveys and config (in `EXPERIMENT_DOCUMENTS/organiser/`):
- `Pre_Experiment_Survey.html` — Pre-experiment survey
- `Post_Experiment_Survey.html` — Post-experiment survey
- `session_config.js` — Auto-generated participant session config

### Run an Experiment Session

To prepare VMs for a new session, run from the `main` branch:

```bash
# Create participant git branches and print the terraform roster block
./SCRIPTS/prepare_vms.sh --type manual --count 4 --session S1
./SCRIPTS/prepare_vms.sh --type ai     --count 4 --session S1
```

Then create an experiment branch, configure Terraform, and apply:

```bash
git checkout -b <experiment-branch>        # e.g. KCL-S1
# Paste the roster block printed above into:
#   infrastructure/aws-dcv/terraform/terraform.tfvars
# Set dcv_allowed_cidrs = ["0.0.0.0/0"] (participants join from unknown IPs)
# Set repo_ref to current main HEAD commit hash
cd infrastructure/aws-dcv/terraform
AWS_PROFILE=genius-dcv terraform apply
```

Follow `EXPERIMENT_DOCUMENTS/organiser/AWS_REMOTE_EXPERIMENT_RUNBOOK.md` for all subsequent steps (readiness checks, screen recorder patch, Kiro setup, end-session data collection).

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
