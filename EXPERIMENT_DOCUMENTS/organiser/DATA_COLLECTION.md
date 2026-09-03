# Data Collection Guide

Simple guide to collect all data needed for GoCodeGreen carbon footprint calculation.

---

## Execution Documents

Use these documents during the session:
- **For participants:** `EXPERIMENT_DOCUMENTS/PARTICIPANT_INSTRUCTIONS_AI.html`
- **For organizers:** `EXPERIMENT_DOCUMENTS/organiser/DATA_COLLECTION.md` (this file)
- **For AWS remote VMs:** `EXPERIMENT_DOCUMENTS/organiser/AWS_REMOTE_EXPERIMENT_RUNBOOK.md`

---

## ID Naming Convention

Throughout this guide, replace `<ID>` with your chosen participant identifier.
Use `<SESSION>` only if you run the same participant more than once.

- **`<ID>`** — Participant identifier. Use a short code, e.g. `P001`, `P002`, `P003`, ...
- **`<SESSION>` (optional)** — Session identifier. Use only for repeated runs, e.g. `S1`, `S2`, `pilot1`.

**Examples:**
```bash
# Participant P001 (single run)
python SCRIPTS/collect_system_info.py --participant-id P001
python SCRIPTS/monitor_resources.py --participant-id P001 -i 60
./SCRIPTS/submit_participant_work.sh P001 SESSION1
```

The command automatically writes a verified full-history Git bundle under
`DATA_COLLECTION/git_state/`. Keep this bundle with the session archive: it is
the portable source for reconstructing exact commits and pre-prompt file states
during replay analysis.
For repeated runs of the same participant, add a session label like `S1`.

Keep IDs consistent across all scripts.
If you use `<SESSION>`, use the same value everywhere for that run.

---

## BEFORE EXPERIMENT DAY (Do these days/weeks before)

**0. Prepare participant Git workspace (organizer only):**
```bash
git clone <YOUR_REPO_URL> experiment_<ID>
cd experiment_<ID>
git checkout main
git pull
rm -rf .git
git init
git checkout -b participant-<ID>
git add .
git commit -m "Start point for <ID>"
git remote add origin <YOUR_REPO_URL>
git push -u origin participant-<ID>
```
This gives the participant:
- latest code from `main`
- a clean Git history for this participant only
- a separate branch that does not affect `main`

**1. Collect system info:**
```bash
python SCRIPTS/collect_system_info.py --participant-id <ID>
```
Output: `DATA_COLLECTION/system_info_<ID>.json`

**2. Generate session config for the HTML pages (organiser only):**

Run this on each VM (or via SSM) after the environment is set up. It reads
`/etc/genius/session.env` and writes `EXPERIMENT_DOCUMENTS/session_config.js`
so that the participant's HTML pages auto-fill their participant ID, session
type, and branch name — the participant does not type or remember anything.

```bash
python SCRIPTS/generate_session_config.py
```

To run via SSM for a remote VM:
```bash
AWS_PROFILE=genius-dcv aws ssm send-command \
  --region eu-west-2 \
  --instance-ids <instance-id> \
  --document-name AWS-RunShellScript \
  --parameters 'commands=["sudo -u participant -H bash -lc \"cd ~/GENIUS_pilot && conda activate genius_pilot && python SCRIPTS/generate_session_config.py\""]'
```

Output: `EXPERIMENT_DOCUMENTS/session_config.js` (read by both HTML pages at load time)

**3. Have participant fill the survey (via HTML form):**
- Participant opens `EXPERIMENT_DOCUMENTS/PARTICIPANT_INSTRUCTIONS_AI.html`
- The pre-experiment survey link in Section 2 opens `Pre_Experiment_Survey.html`
- Participant ID and session type are pre-filled and locked from `session_config.js`
- On submit, the form downloads `survey_<ID>.json` to `~/Downloads/`
- Participant runs: `mv ~/Downloads/survey_<ID>.json ~/GENIUS_pilot/DATA_COLLECTION/`
- Output saved as `DATA_COLLECTION/survey_<ID>.json`

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

**1. Verify the background collection services:**
```bash
sudo systemctl is-active genius-resource-monitor.service
/usr/local/bin/genius-collection-health snapshot
```
Expected: the resource monitor is `active`. It runs as a restartable system
service and does not depend on an open terminal.

**2. Start screen recording (participant, after DCV desktop is visible):**
```bash
/usr/local/bin/genius-screen-recorder start
/usr/local/bin/genius-screen-recorder status
```
Expected: `running`, plus a display size of at least `1280x720` (usually `1920x1080`).

Do not start recording before the participant has connected via DCV — early starts capture a small cropped window. If the DCV tab disconnects briefly, a watchdog restarts recording automatically once the full desktop is back.

**3. Capture a final health snapshot when the participant finishes:**
```bash
/usr/local/bin/genius-collection-health snapshot
```

The unified submission/end-session flow stops the resource service after its
final runtime data has been copied.

**4. Stop screen recording when participant finishes:**
```bash
/usr/local/bin/genius-screen-recorder stop
/usr/local/bin/genius-screen-recorder status
```
Expected: `stopped`. On AWS VMs, `stop` also merges multiple segments into one file if recording restarted during the session.

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

**3. Claude Code metrics (AI participants only):**
```bash
python SCRIPTS/collect_claude_code_metrics.py --participant-id <ID>
```
This also runs automatically on AWS remote VMs via the end-session script.
Treat local usage fields as best-effort. Bedrock invocation logs or provider
billing remain authoritative for token and cost accounting.

**4. Checkpoint/task test result files (canonical, run after the session on final codebase):**
```bash
python SCRIPTS/run_experiment_test_checkpoints.py --participant-id <ID>
```
This produces:
- `Task1_cp1_<ID>.json`
- `Task1_cp2_<ID>.json`
- `Task1_cp3_<ID>.json`
- `Task2_<ID>.json`
- `Task3_<ID>.json`

**5. Aggregate test metrics (optional):**
```bash
python SCRIPTS/collect_test_metrics.py --participant-id <ID>
```
Use this only if you also want one combined `test_metrics_<ID>.json` file
(duration/resource/coverage summary). By default it skips performance tests.
Add `--include-performance` only if you want the long run.

**6. Code quality:**
```bash
python SCRIPTS/analyze_code_quality.py --participant-id <ID>
```

**7. Energy estimate:**
```bash
python SCRIPTS/estimate_energy.py DATA_COLLECTION/resource_usage_<ID>.jsonl \
  --system-info DATA_COLLECTION/system_info_<ID>.json --participant-id <ID>
```

**8. Carbon footprint:**
```bash
python SCRIPTS/calculate_carbon_footprint.py DATA_COLLECTION/energy_estimate_<ID>.json \
  --location UK --participant-id <ID>
```
If you want network or travel emissions included, add:
`--network-data <GB>` and/or `--travel-data <path_to_travel.json>`. Defaults are 0.

**9. Aggregate all data:**
```bash
python SCRIPTS/aggregate_experiment_data.py <ID>
```

**10. Fill GoCodeGreen template:**
```bash
python SCRIPTS/fill_gocodegreen_template.py DATA_COLLECTION/aggregated_<ID>.json \
  --session-type ai-assisted
```

## Compare AI-Assisted Sessions (After participants finish)

**Compare baseline:**
```bash
python SCRIPTS/compare_baseline.py \
  DATA_COLLECTION/aggregated_<ID_1>.json \
  DATA_COLLECTION/aggregated_<ID_2>.json
```

**Generate comparison report:**
```bash
python SCRIPTS/generate_success_criteria_report.py \
  DATA_COLLECTION/aggregated_<ID_1>.json \
  DATA_COLLECTION/aggregated_<ID_2>.json
```

---

## What Gets Collected

- **System info:** CPU, memory, GPU, OS specs (BEFORE)
- **Resource usage:** CPU%, memory, network, disk I/O (ON - every 60 seconds)
- **Screen recordings:** Full-desktop MP4 from DCV session (ON; participant starts/stops via `genius-screen-recorder`)
- **Checkpoint/task test results:** per checkpoint/task pass/fail JSON outputs (AFTER, from final codebase)
- **Git activity:** Commits, lines changed, branch activity (AFTER)
- **CI/CD:** Pipeline runs, test times, pass/fail rates (AFTER; GitLab config/API only)
- **Claude Code:** AI conversations, turns, tool uses, local usage fields when present, and VS Code extension diagnostics (AFTER; best-effort from Claude Code transcripts and VS Code logs)
- **Test metrics:** Execution time, pass/fail, memory usage (AFTER; performance tests optional)
- **Code quality:** Quality score, complexity, documentation (AFTER; requires extra tools)
- **Energy:** Estimated from CPU/memory/GPU usage (AFTER)
- **Carbon:** CO2 emissions from energy; network/travel only if you provide those inputs (AFTER)

---

## Output Files

All data saved to `DATA_COLLECTION/`:
- `system_info_<ID>.json` (BEFORE)
- `resource_usage_<ID>.jsonl` (ON, single-run default)
- `screen_recordings/*.mp4` (ON; AWS end-session copies from `~/Videos/` to `DATA_COLLECTION/screen_recordings/`)
- `screen_recording_segments.json` (ON; log of recording restarts, if any)
- `Task1_cp1_<ID>.json` (AFTER, single-run default)
- `Task1_cp2_<ID>.json` (AFTER, single-run default)
- `Task1_cp3_<ID>.json` (AFTER, single-run default)
- `Task2_<ID>.json` (AFTER, single-run default)
- `Task3_<ID>.json` (AFTER, single-run default)
- `git_activity_<ID>.json` (AFTER)
- `cicd_metrics_<ID>.json` (AFTER)
- `claude_code_metrics_<ID>.json` (AFTER, single-run default)
- `test_metrics_<ID>.json` (AFTER, optional aggregate single-run default)
- `code_quality_<ID>.json` (AFTER)
- `energy_estimate_<ID>.json` (AFTER)
- `carbon_footprint_<ID>.json` (AFTER)
- `aggregated_<ID>.json` (AFTER, single-run default)
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
- See `EXPERIMENT_DOCUMENTS/organiser/EXPERIMENT_CHECKLIST.html` for the full organiser checklist

**Why it matters:**
- Background processes affect energy consumption measurements
- Extra network activity interferes with data collection
- Keep environment consistent across participants

---

## Troubleshooting

- **Monitoring stops:** Check `psutil` installed: `pip install psutil`
- **Recording shows `stopped` or small size (800×600):** Participant must connect via DCV first, then run `genius-screen-recorder stop` and `start` again. See `AWS_REMOTE_EXPERIMENT_RUNBOOK.md`.
- **Recording stopped mid-session:** Watchdog should auto-resume within ~15 seconds once DCV is back. Check `systemctl status genius-recorder-watchdog.timer` on the VM.
- **Multiple MP4 parts:** Normal after a DCV reconnect. `genius-screen-recorder stop` merges them; end-session uploads all parts plus `_merged.mp4` if present.
- **System info fails on macOS:** Run from the normal terminal (not a restricted shell) or try updating `psutil`
- **Code quality fails:** Install tools: `pip install pylint radon pydocstyle`
- **Claude Code metrics not found:** Check `DATA_COLLECTION/claude_code_history/manifest.txt`, VS Code extension logs, and the screen recording
- **Energy seems wrong:** Values are estimates - may need calibration for your hardware
- **Missing data files:** Run `verify_data_separation.py` to check what's missing
- **Can't find participant data:** Check `DATA_COLLECTION/` folder, verify participant ID is correct
