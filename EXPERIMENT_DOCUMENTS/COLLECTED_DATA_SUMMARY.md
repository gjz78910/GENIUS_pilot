# GENIUS Pilot KCL-01 — Collected Data Summary

**Experiment date:** 2026-06-09  
**Group:** AI-assisted coding with Kiro  
**Participants:** 6 VMs — ai-01–ai-06 (all real participants)  
**Data confirmed collected and downloaded:** 2026-06-09  

---

## 1. Participant Overview

| VM | Role | Seniority | Main Language | Session Start | Session End | DevOps Maturity | MLOps Maturity | Pre-Survey | Post-Survey |
|----|------|-----------|---------------|---------------|-------------|-----------------|----------------|------------|-------------|
| ai-01 | Developer | Mid | Go/Elixir | 09:00 | 17:00 | 4/5 | 2/5 | Yes | Yes |
| ai-02 | Developer | Senior | Java | ~10:49 | ~14:47 | 1/5 | 1/5 | Yes | Yes |
| ai-03 | DevOps Engineer | Mid | Python | 14:09 | 16:08 | 5/5 | 3/5 | Yes | Yes |
| ai-04 | — | — | — | — | ~14:23 | — | — | **Not submitted** | **Not submitted** |
| ai-05 | AI Researcher | Junior | Python | 14:00 | 16:00 | 1/5 | 2/5 | Yes | Yes |
| ai-06 | — | — | — | — | ~14:03 | — | — | **Not submitted** | Yes |

> ai-04 and ai-06 had the survey HTML forms available on their VM but never submitted them. Data is unrecoverable.

---

## 2. Post-Survey Highlights (AI tool usage)

| VM | Used AI During Session | Used Extensively | Notes (excerpt) |
|----|----------------------|-----------------|-----------------|
| ai-01 | Yes | Yes | "During refactoring it was very useful... During bug fixes it started creating docs which took a lot of time — would have been quicker to fix manually." |
| ai-02 | Yes | Yes | "Had trouble with the scalability issue: the AI took the wrong path early..." |
| ai-03 | Yes | Yes | "Was unclear what model was being used, may have gotten quicker results with a better model." |
| ai-05 | Yes | Yes | *(no notes)* |
| ai-06 | Yes | Yes | "I enjoyed the experience, it reminded me a lot of applying for jobs after university..." |

---

## 3. Code & Git

All participant branches on GitHub: `github.com/gjz78910/GENIUS_pilot`

| VM | Branch | Participant Work Commit | Commit Timestamp | Clean at End |
|----|--------|------------------------|------------------|--------------|
| ai-01 | `participant/ai-01` | In `ai-01_S1` session archive | 2026-06-09 ~10:31 | Yes |
| ai-02 | `participant/ai-02` | `45bb0ae` | 2026-06-09 14:44:38 | Yes |
| ai-03 | `participant/ai-03` | `d86391a` | 2026-06-09 14:40:13 | Yes |
| ai-04 | `participant/ai-04` | `d74e1ef` | 2026-06-09 14:22:36 | Yes |
| ai-05 | `participant/ai-05` | `a3c79b4` | 2026-06-09 14:15:10 | Yes |
| ai-06 | `participant/ai-06` | `11d36ad` | 2026-06-09 14:02:31 | Yes |

Local clones: `~/Downloads/GENIUS_experiment_data/{ai-01..ai-06}/`

---

## 4. DATA_COLLECTION Files

Two copies exist locally for each participant: the git clone (`{id}/DATA_COLLECTION/`) and the S1 session folder (`{id}_S1/data/`).

| File | ai-01 | ai-02 | ai-03 | ai-04 | ai-05 | ai-06 |
|------|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|
| `aggregated_{id}_S1.json` | Yes* | Yes | Yes | Yes | Yes | Yes |
| `kiro_metrics_{id}_S1.json` | Yes* | Yes | Yes | Yes | Yes | Yes |
| `participant_state_{id}_S1.json` | Yes* | Yes | Yes | Yes | Yes | Yes |
| `git_log_{id}_S1.txt` | Yes* | Yes | Yes | Yes | Yes | Yes |
| `survey_{id}.json` (pre) | Yes* | Yes | Yes | **No** | Yes | **No** |
| `survey_post_{id}.json` | Yes* | Yes | Yes | **No** | Yes | Yes |
| `participant_backups/*.tar.gz` | Yes* | Yes (~6.1MB) | Yes (~6.1MB) | Yes (~6.1MB) | Yes (~6.1MB) | Yes (~6.1MB) |

*ai-01 data is in `ai-01_S1/` (session archive), not in the git branch.

---

## 5. Kiro Chat Logs

Stored locally in `~/Downloads/GENIUS_experiment_data/{id}_S1/supplemental/`

| VM | Chat API Log | Rotated Log (.1.log) | Session JSONs | Resource Usage JSONL | Notes |
|----|-------------|----------------------|---------------|----------------------|-------|
| ai-01 | 8.1 MB | 29.9 MB | 1 | No | In `ai-01_S1/` archive |
| ai-02 | 23.5 MB | None | 4 | 222 KB | — |
| ai-03 | 5.3 MB | 29.6 MB | 2 | 221 KB | Both log files downloaded |
| ai-04 | 15.8 MB | None | 1 | 208 KB | — |
| ai-05 | 21.9 MB | None | 1 | 200 KB | Resource file labelled `manual-02` (VM was repurposed) |
| ai-06 | 8.4 MB | None | 1 | 199 KB | Resource file labelled `manual-03` (VM was repurposed) |

**Total Kiro chat log volume:** ~115 MB raw across all participants.

---

## 6. Screen Recordings

Stored locally in `~/Downloads/GENIUS_experiment_data/{id}_S1/videos/`

| VM | Segments Downloaded | Total Size | Largest Segment | Notes |
|----|---------------------|------------|-----------------|-------|
| ai-01 | 1 (full archive) | ~158 MB | — | In `ai-01_S1/` archive |
| ai-02 | 3 (partial*) | ~134 MB local | 299 MB main on S3 | Full set on S3 = ~620 MB, 9 segments |
| ai-03 | 1 (partial*) | ~132 MB local | 405 MB main on S3 | Full set on S3 = ~552 MB, 4 segments |
| ai-04 | 1 (partial*) | ~130 MB local | 317 MB main on S3 | Full set on S3 = ~470 MB, 4 segments |
| ai-05 | 1 (partial*) | ~130 MB local | 222 MB main on S3 | Full set on S3 = ~390 MB, 4 segments |
| ai-06 | 1 (partial*) | ~130 MB local | 158 MB main on S3 | Full set on S3 = ~327 MB, 7 segments |

*Only the first segment was downloaded in the earlier session export. Full recordings remain on S3.  
**Full video storage on S3:** ~2.9 GB across 5 real participants.  
**Note:** Videos are split into segments due to watchdog restarting ffmpeg when Kiro launched or DCV reconnected. Concatenate with `ffmpeg -f concat` for continuous playback.

---

## 7. Full Project Rescue Archives (S3 only — not downloaded locally)

Complete snapshots of `/home/participant/GENIUS_pilot` taken at session close. Contains working tree including uncommitted files, `.kiro` config, and anything not in git.

| VM | S3 Path | Size |
|----|---------|------|
| ai-01 | `ai-01/S1/ai-01-S1-rescue.tar.gz` | 24.1 MB |
| ai-02 | `ai-02/S1/ai-02-S1-rescue.tar.gz` | 25.2 MB |
| ai-03 | `ai-03/S1/ai-03-S1-rescue.tar.gz` | 25.1 MB |
| ai-04 | `ai-04/S1/ai-04-S1-rescue.tar.gz` | 25.1 MB |
| ai-05 | `ai-05/S1/ai-05-S1-rescue.tar.gz` | 25.2 MB |
| ai-06 | `ai-06/S1/ai-06-S1-rescue.tar.gz` | 25.2 MB |

S3 bucket: `genius-dcv-artifacts-684638912478-82c72ce8` (eu-west-2)

---

## 8. What Is Analyzable

| Data Type | Available For | What You Can Analyze |
|-----------|--------------|----------------------|
| Pre-experiment survey | ai-01, ai-02, ai-03, ai-05 (4/6) | Background, experience level, commute mode, DevOps/MLOps maturity |
| Post-experiment survey | ai-01, ai-02, ai-03, ai-05, ai-06 (5/6) | Kiro usage patterns, qualitative session feedback |
| Kiro chat history (raw API log) | All 6 | Prompt patterns, volume, conversation structure, tool calls |
| Kiro session JSONs | All 6 | Workspace sessions, agent task breakdown |
| Resource usage (CPU/RAM) | ai-02 through ai-06 | System load timeline correlated with coding activity |
| Participant code commits | ai-02 through ai-06 | What code was changed vs. baseline |
| Code backup archives | ai-02 through ai-06 | Full working tree snapshot at session end |
| Screen recordings | All 6 | Coding process, Kiro interaction, time-on-task |
| Git activity log | All 6 | Commit frequency, timing, files changed |

---

## 9. Known Issues

| Issue | Affected |
|-------|---------|
| No surveys at all | ai-04 — participant never submitted pre or post survey |
| No pre-survey | ai-06 — participant skipped pre-survey; post-survey completed |
| ai-01 participant work not committed to git branch | ai-01 — code changes are in the `ai-01_S1` session archive, not in `participant/ai-01` branch |
| Resource/metadata files mislabelled `manual-02`/`manual-03` | ai-05, ai-06 — VMs were repurposed from manual group provisioning |
| Screen recordings are split into segments | ai-02–ai-06 — concatenate for continuous playback |
| Full video set not downloaded locally | ai-02–ai-06 — only first segment local; full set on S3 (~2.9 GB) |

---

## 10. Local Data Layout

```
~/Downloads/GENIUS_experiment_data/
├── ai-01/               ← git clone of participant/ai-01 branch (dry-run, no participant work)
├── ai-01_S1/            ← full session archive (surveys, aggregated data, Kiro logs, 1 video)
├── ai-02/               ← git clone of participant/ai-02 (code + DATA_COLLECTION)
├── ai-02_S1/
│   ├── data/            ← surveys, aggregated JSON, kiro metrics, git log
│   ├── supplemental/    ← raw kiro chat log, session JSONs, resource usage
│   └── videos/          ← 3 video segments (partial; full set on S3)
├── ai-03/  ai-03_S1/
├── ai-04/  ai-04_S1/
├── ai-05/  ai-05_S1/
└── ai-06/  ai-06_S1/
```
