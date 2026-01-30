# Data Collection Guide

Simple guide to collect all data needed for GoCodeGreen carbon footprint calculation.

---

## BEFORE EXPERIMENT DAY (Do these days/weeks before)

**1. Collect system info:**
```bash
python SCRIPTS/collect_system_info.py --participant-id <ID>
```
Output: `DATA_COLLECTION/system_info_<ID>.json`

**2. Have participant fill survey:**
- Use `DATA_COLLECTION/pre_experiment_survey.md`
- Save as `DATA_COLLECTION/survey_<ID>.md`

**3. Install dependencies:**
```bash
pip install -r requirements.txt
# or
conda env update -f environment.yml
```
**Recommended:** Run all scripts from the `genius_pilot` conda env so `psutil` is available.
```bash
conda activate genius_pilot
```
If you plan to run code-quality checks, also install: `pylint`, `radon`, `pydocstyle`.

---

## ON EXPERIMENT DAY (During the session)

**1. Start resource monitoring (run in background):**
```bash
python SCRIPTS/monitor_resources.py --participant-id <ID> --session-id <SESSION> -i 60 &
```
Press Ctrl+C to stop when participant finishes. (Requires `psutil`.)

**2. Track tasks (optional):**
```bash
python SCRIPTS/task_timer.py --participant-id <ID> --session-id <SESSION> -i
```
Commands: `start <task>`, `end`, `save` (use `save` or Ctrl+C to write the JSON file)

**3. Stop monitoring when participant finishes:**
- Press Ctrl+C in the monitoring terminal, or
- Find process: `ps aux | grep monitor_resources` then `kill <process_id>`

---

## AFTER EXPERIMENT DAY (Run these after the session ends)

Run these scripts in order (can be done same day or later):

**1. Git activity:**
```bash
python SCRIPTS/git_activity_logger.py --participant-id <ID>
```

**2. CI/CD metrics:**
```bash
python SCRIPTS/extract_cicd_metrics.py --participant-id <ID>
```
Note: This script is GitLab-focused. If there is no `.gitlab-ci.yml` or GitLab API token,
the output will be limited to local repo signals.

**3. Q Developer metrics (AI participants only):**
```bash
python SCRIPTS/collect_q_developer_metrics.py --participant-id <ID> --session-id <SESSION>
```

**4. Test metrics:**
```bash
python SCRIPTS/collect_test_metrics.py --participant-id <ID> --session-id <SESSION>
```
By default it skips performance tests. Add `--include-performance` only if you want the long run.

**5. Code quality:**
```bash
python SCRIPTS/analyze_code_quality.py --participant-id <ID>
```

**6. Energy estimate:**
```bash
python SCRIPTS/estimate_energy.py DATA_COLLECTION/resource_usage_<ID>_<SESSION>.jsonl \
  --system-info DATA_COLLECTION/system_info_<ID>.json --participant-id <ID>
```

**7. Carbon footprint:**
```bash
python SCRIPTS/calculate_carbon_footprint.py DATA_COLLECTION/energy_estimate_<ID>.json \
  --location UK --participant-id <ID>
```
If you want network or travel emissions included, add:
`--network-data <GB>` and/or `--travel-data <path_to_travel.json>`. Defaults are 0.

**8. Aggregate all data:**
```bash
python SCRIPTS/aggregate_experiment_data.py <ID> --session-id <SESSION>
```

**9. Fill GoCodeGreen template:**
```bash
python SCRIPTS/fill_gocodegreen_template.py DATA_COLLECTION/aggregated_<ID>_<SESSION>.json \
  --session-type manual  # or "ai-assisted"
```

## Compare Manual vs AI (After both participants finish)

**Compare baseline:**
```bash
python SCRIPTS/compare_baseline.py \
  DATA_COLLECTION/aggregated_<MANUAL_ID>_<SESSION>.json \
  DATA_COLLECTION/aggregated_<AI_ID>_<SESSION>.json
```

**Generate success criteria report:**
```bash
python SCRIPTS/generate_success_criteria_report.py \
  DATA_COLLECTION/aggregated_<MANUAL_ID>_<SESSION>.json \
  DATA_COLLECTION/aggregated_<AI_ID>_<SESSION>.json
```
Use your real participant IDs/session IDs, or rename files to `aggregated_manual_*.json`
and `aggregated_ai_*.json` if that is easier.

---

## What Gets Collected

- **System info:** CPU, memory, GPU, OS specs (BEFORE)
- **Resource usage:** CPU%, memory, network, disk I/O (ON - every 60 seconds)
- **Task timing:** Time spent per task, idle time (ON - optional)
- **Git activity:** Commits, lines changed, branch activity (AFTER)
- **CI/CD:** Pipeline runs, test times, pass/fail rates (AFTER; GitLab config/API only)
- **Q Developer:** AI queries, suggestions accepted/rejected (AFTER; best-effort from VS Code logs)
- **Test metrics:** Execution time, pass/fail, memory usage (AFTER; performance tests optional)
- **Code quality:** Quality score, complexity, documentation (AFTER; requires extra tools)
- **Energy:** Estimated from CPU/memory/GPU usage (AFTER)
- **Carbon:** CO2 emissions from energy; network/travel only if you provide those inputs (AFTER)

---

## Output Files

All data saved to `DATA_COLLECTION/`:
- `system_info_<ID>.json` (BEFORE)
- `resource_usage_<ID>_<SESSION>.jsonl` (ON)
- `task_timing_<ID>_<SESSION>.json` (ON - optional)
- `git_activity_<ID>.json` (AFTER)
- `cicd_metrics_<ID>.json` (AFTER)
- `q_developer_metrics_<ID>_<SESSION>.json` (AFTER)
- `test_metrics_<ID>_<SESSION>.json` (AFTER)
- `code_quality_<ID>.json` (AFTER)
- `energy_estimate_<ID>.json` (AFTER)
- `carbon_footprint_<ID>.json` (AFTER)
- `aggregated_<ID>_<SESSION>.json` (AFTER)
- `gocodegreen_data.csv` (AFTER - final output for GoCodeGreen)

---

## Verify Data Collection

**After collecting all data, verify it's stored correctly:**
```bash
# Verify data separation between participants
python SCRIPTS/verify_data_separation.py

# List all participants found
python SCRIPTS/verify_data_separation.py --list-participants

# Check specific participant
python SCRIPTS/verify_data_separation.py --participant-id <ID>
```

**What it checks:**
- All files have participant IDs in names
- No cross-contamination between participants
- Required files exist
- File naming is consistent

---

## Environment Control Notes

**Before starting monitoring:**
- Close unnecessary applications (browsers, media players, etc.)
- Run: `python SCRIPTS/list_background_processes.py` to see what's running
- See `EXPERIMENT_DOCUMENTS/EXPERIMENT_CHECKLIST.md` for a longer prep checklist

**Why it matters:**
- Background processes affect energy consumption measurements
- Extra network activity interferes with data collection
- Keep environment consistent across participants

---

## Troubleshooting

- **Monitoring stops:** Check `psutil` installed: `pip install psutil`
- **System info fails on macOS:** Run from the normal terminal (not a restricted shell) or try updating `psutil`
- **Code quality fails:** Install tools: `pip install pylint radon pydocstyle`
- **Q Developer metrics not found:** Check VS Code extension logs manually, or use screen recording
- **Energy seems wrong:** Values are estimates - may need calibration for your hardware
- **Missing data files:** Run `verify_data_separation.py` to check what's missing
- **Can't find participant data:** Check `DATA_COLLECTION/` folder, verify participant ID is correct
