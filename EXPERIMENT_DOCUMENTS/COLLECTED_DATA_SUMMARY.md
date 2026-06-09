# GENIUS Pilot KCL-01 — Collected Data Summary

**Experiment date:** 2026-06-09  
**Group:** AI-assisted (Kiro), 6 VMs (ai-01 = organiser dry-run; ai-02–ai-06 = real participants)  
**Data pulled:** 2026-06-09 (session end)

---

## 1. Participant Overview

| VM | Role | Seniority | Main Language | Session Start | Session End | Pre-Survey | Post-Survey |
|----|------|-----------|---------------|---------------|-------------|------------|-------------|
| ai-01 | — (organiser dry-run) | — | — | — | — | No | No |
| ai-02 | Developer | Senior | Java | ~10:49 | ~14:47 | Yes | Yes |
| ai-03 | DevOps Engineer | Mid | Python | 14:09 | 16:08 | Yes | Yes |
| ai-04 | — | — | — | — | ~14:23 | **MISSING** (not submitted) | **MISSING** (not submitted) |
| ai-05 | AI Researcher | Junior | Python | 14:00 | 16:00 | Yes | Yes |
| ai-06 | — | — | — | — | ~14:03 | **MISSING** (not submitted) | Yes |

---

## 2. Code & Git

| VM | GitHub Branch | Participant Work Commit | Commit Tag | Uncommitted Changes |
|----|--------------|------------------------|------------|---------------------|
| ai-01 | `participant/ai-01` | None (dry-run, base only) | — | No |
| ai-02 | `participant/ai-02` | `45bb0ae` — Participant ai-02 work - S1 - 2026-06-09 14:44:38 | `participant-ai-02-S1-20260609-144438` | No |
| ai-03 | `participant/ai-03` | `d86391a` — Participant ai-03 work - S1 - 2026-06-09 14:40:13 | `participant-ai-03-S1-20260609-144013` | No |
| ai-04 | `participant/ai-04` | `d74e1ef` — Participant ai-04 work - S1 - 2026-06-09 14:22:36 | `participant-ai-04-S1-20260609-142236` | No |
| ai-05 | `participant/ai-05` | `a3c79b4` — Participant ai-05 work - S1 - 2026-06-09 14:15:10 | `participant-ai-05-S1-20260609-141510` | No |
| ai-06 | `participant/ai-06` | `11d36ad` — Participant ai-06 work - S1 - 2026-06-09 14:02:31 | `participant-ai-06-S1-20260609-140231` | No |

Local clone: `~/Downloads/GENIUS_experiment_data/{ai-01..ai-06}/`

---

## 3. DATA_COLLECTION Files (per participant, in GitHub branch)

| File | ai-01 | ai-02 | ai-03 | ai-04 | ai-05 | ai-06 |
|------|-------|-------|-------|-------|-------|-------|
| `aggregated_{id}_S1.json` | No | Yes | Yes | Yes | Yes | Yes |
| `kiro_metrics_{id}_S1.json` | No | Yes | Yes | Yes | Yes | Yes |
| `participant_state_{id}_S1.json` | No | Yes | Yes | Yes | Yes | Yes |
| `git_log_{id}_S1.txt` | No | Yes | Yes | Yes | Yes | Yes |
| `survey_{id}.json` (pre) | No | Yes | Yes | **No — not submitted** | Yes | **No — not submitted** |
| `survey_post_{id}.json` | No | Yes | Yes | **No — not submitted** | Yes | Yes |
| `participant_backups/*.tar.gz` | No | Yes (~6.1MB) | Yes (~6.1MB) | Yes (~6.1MB) | Yes (~6.1MB) | Yes (~6.1MB) |

---

## 4. Kiro Chat Logs (in S3: `experiment-data/{id}_S1/supplemental/`)

| VM | Chat API Log Size | Rotated Log (.1.log) | Session JSONs | Resource Usage |
|----|-------------------|----------------------|---------------|----------------|
| ai-01 | 8.1 MB | 29.9 MB (overflow) | 1 JSON (77 KB) | No |
| ai-02 | 23.5 MB | None | 4 JSONs | Yes (222 KB) |
| ai-03 | 5.3 MB | 29.6 MB (rotated) | 2 JSONs | Yes (221 KB) |
| ai-04 | 15.8 MB | None | 1 JSON (97 KB) | Yes (208 KB) |
| ai-05 | 21.9 MB | None | 1 JSON (37 KB) | Yes (200 KB) |
| ai-06 | 8.4 MB | None | 1 JSON (33 KB) | Yes (199 KB) |

> Note: ai-01 full Kiro logs archive also saved to S3: `ai-01/kiro-logs-full.tar.gz` (7.5 MB compressed).

---

## 5. Screen Recordings (in S3: `experiment-data/{id}_S1/videos/`)

| VM | Video Files | Total Size (approx.) | Notes |
|----|-------------|----------------------|-------|
| ai-01 | 1 archive (ai-01/S1/) | 158 MB | Full session archive |
| ai-02 | 9 segments | ~620 MB | Includes long 299 MB main segment |
| ai-03 | 4 segments | ~552 MB | 405 MB main segment |
| ai-04 | 4 segments | ~470 MB | 317 MB main segment |
| ai-05 | 4 segments | ~390 MB | 222 MB main segment |
| ai-06 | 7 segments | ~327 MB | Fragmented — multiple restarts |

> Videos are segmented (timestamped filenames) because watchdog restarted recording when Kiro was launched or DCV reconnected. Total video storage: ~2.9 GB across 5 real participants.

---

## 6. Full Project Archives (in S3: `{id}/S1/{id}-S1-rescue.tar.gz`)

These are complete snapshots of `/home/participant/GENIUS_pilot` taken at session close, including all working files, Kiro config, and anything not committed to git.

| VM | Archive | Size |
|----|---------|------|
| ai-01 | `ai-01/S1/ai-01-S1-rescue.tar.gz` | 24.1 MB |
| ai-02 | `ai-02/S1/ai-02-S1-rescue.tar.gz` | 25.2 MB |
| ai-03 | `ai-03/S1/ai-03-S1-rescue.tar.gz` | 25.1 MB |
| ai-04 | `ai-04/S1/ai-04-S1-rescue.tar.gz` | 25.1 MB |
| ai-05 | `ai-05/S1/ai-05-S1-rescue.tar.gz` | 25.2 MB |
| ai-06 | `ai-06/S1/ai-06-S1-rescue.tar.gz` | 25.2 MB |

---

## 7. What Is Analyzable

| Data Type | Available For | What You Can Analyze |
|-----------|--------------|----------------------|
| Pre-experiment survey | ai-02, ai-03, ai-05 | Background, experience, commute, DevOps/MLOps maturity |
| Post-experiment survey | ai-02, ai-03, ai-05, ai-06 | Task difficulty, tool experience, qualitative feedback |
| Kiro chat history (raw) | ai-01 through ai-06 | Prompt patterns, chat volume, conversation structure |
| Kiro session JSONs | ai-01 through ai-06 | Workspace sessions, agent interactions |
| Resource usage (CPU/RAM) | ai-02 through ai-06 | System load timeline during coding tasks |
| Participant code commits | ai-02 through ai-06 | What code was written/changed vs. baseline |
| Code backup archives | ai-02 through ai-06 | Full working tree snapshot at session end |
| Screen recordings | ai-02 through ai-06 | Coding process, tool usage, time-on-task |
| Git log | ai-02 through ai-06 | Commit frequency, timing |

---

## 8. Known Issues / Gaps

| Issue | Affected |
|-------|---------|
| No pre-survey | ai-04, ai-06 — confirmed absent in rescue archives; HTML form was present but never submitted |
| No post-survey | ai-04 — confirmed absent; participant never submitted either survey |
| ai-01 was organiser dry-run, not a real participant | ai-01 |
| ai-05, ai-06 originally provisioned as `manual-02`/`manual-03` — some filenames reference wrong ID | ai-05, ai-06 |
| Video segments are split (watchdog restarts) — need to concatenate for continuous playback | ai-02 through ai-06 |
| Participant code diff not extractable from shallow clone — use full rescue archive or git log file | All |

---

## 9. Data Locations Summary

| Location | Contents |
|----------|----------|
| `~/Downloads/GENIUS_experiment_data/{id}/` | Full git repo clone per participant (code + DATA_COLLECTION) |
| `github.com/gjz78910/GENIUS_pilot` branches `participant/ai-01..06` | Same, permanently on GitHub |
| S3 `experiment-data/{id}_S1/supplemental/` | Kiro chat logs, session JSONs, resource usage |
| S3 `experiment-data/{id}_S1/videos/` | Screen recording MP4 segments |
| S3 `{id}/S1/{id}-S1-rescue.tar.gz` | Full project directory snapshot |
| S3 `ai-01/kiro-logs-full.tar.gz` | All Kiro log files from ai-01 |
| Local `DATA_COLLECTION/ai-01/kiro-logs-full.tar.gz` | ai-01 Kiro logs downloaded locally |

S3 bucket: `genius-dcv-artifacts-684638912478-82c72ce8` (eu-west-2)
