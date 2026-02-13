# Experiment Issues Report

## 1. Run Context
- Branch: `KCL-01`
- Participant/session: `Jing` / `pilot-test-1`
- Session type: `ai-assisted`
- Workspace used for execution: `/tmp/GENIUS_pilot_KCL-01`
- Original workspace preserved: `/Users/k2589922/Documents/Projects/GENIUS_pilot` (no mutations after safety snapshots)

## 2. Missing or Malformed Data
- No malformed JSON/JSONL files detected in `DATA_COLLECTION/`.
- Canonical checkpoint files (`Task1_cp1`, `Task1_cp2`, `Task1_cp3`, `Task2`, `Task3`) all include required fields (`command`, `return_code`, `success`, `test_statistics`) and all report success.
- Resource log (`resource_usage_Jing_pilot-test-1.jsonl`) is structurally valid with 7 monotonic samples.
- Gap: `task_timing_Jing_pilot-test-1.json` was not collected in this dry run, so `gocodegreen_data.csv` has `Working Hours: None`.

## 3. Redundant or Overlapping Data
- `test_metrics_Jing_pilot-test-1.json` overlaps with checkpoint outputs (`Task*_Jing_pilot-test-1.json`) in pass/fail reporting; keep both only if you need both a single aggregate test snapshot and checkpoint-granular evidence.
- `aggregated_Jing_pilot-test-1.json` currently does **not** ingest `Task1_cp*`, `Task2`, `Task3` files (by script design), so checkpoint artifacts remain separate.

## 4. Tooling/Documentation Inconsistencies Found and Patched
- Patched `SCRIPTS/collect_q_developer_metrics.py`:
  - Added CLI support for `--participant-id`, `--session-id`, `-o/--output`.
  - Now supports direct file output naming required by checklist workflow.
- Replaced `SCRIPTS/verify_data_separation.py` parser:
  - Correctly handles IDs + hyphenated sessions (e.g., `Jing_pilot-test-1`).
  - Eliminates false participant extraction from filenames like `Task1_cp3_*` and `scalability_checkpoint_c_status.json`.
- Patched docs for branch naming consistency:
  - `EXPERIMENT_DOCUMENTS/PARTICIPANT_INSTRUCTIONS.md`
  - `EXPERIMENT_DOCUMENTS/DATA_COLLECTION.md`
  - Updated from `participant/<ID>` examples to `participant-<ID>`, and documented custom dry-run branch support (e.g., `KCL-01`).

## 5. Remaining Risks
- Environment package installation for `pylint`, `radon`, `pydocstyle` failed due network resolution limits in this environment.
  - Impact: `code_quality_Jing.json` was produced, but static-analysis subsections are marked unavailable.
- Q Developer metrics show zero interactions in this dry run (`q_developer_metrics_Jing_pilot-test-1.json`), which is expected unless a real Q-assisted coding session occurs in VS Code logs.
