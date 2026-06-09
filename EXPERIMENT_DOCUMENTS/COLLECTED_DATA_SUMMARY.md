# GENIUS Pilot KCL-01 — Collected Data Summary

**Experiment date:** 2026-06-09  
**Group:** AI-assisted coding with Kiro  
**Participants:** ai-01–ai-06 (6 participants)  
**Data collected and downloaded:** 2026-06-09  

---

## 1. Participant Overview

| VM | Role | Seniority | Main Language | Session Start | Session End | DevOps Maturity | MLOps Maturity | Pre-Survey | Post-Survey |
|----|------|-----------|---------------|---------------|-------------|-----------------|----------------|------------|-------------|
| ai-01 | Developer | Mid | Go/Elixir | 09:00 | ~10:31 | 4/5 | 2/5 | Yes | Yes |
| ai-02 | Developer | Senior | Java | ~10:49 | ~14:47 | 1/5 | 1/5 | Yes | Yes |
| ai-03 | DevOps Engineer | Mid | Python | 14:09 | 16:08 | 5/5 | 3/5 | Yes | Yes |
| ai-04 | — | — | — | — | ~14:23 | — | — | **Not submitted** | **Not submitted** |
| ai-05 | AI Researcher | Junior | Python | 14:00 | 16:00 | 1/5 | 2/5 | Yes | Yes |
| ai-06 | — | — | — | — | ~14:03 | — | — | **Not submitted** | Yes |

> ai-04 and ai-06 had the survey forms available but never submitted them. Data is unrecoverable.

---

## 2. Post-Survey Highlights

| VM | Used AI Extensively | Notes (excerpt) |
|----|---------------------|-----------------|
| ai-01 | Yes | "During refactoring it was very useful... During bug fixes it started creating docs which took a lot of time — would have been quicker to fix manually." |
| ai-02 | Yes | "Had trouble with the scalability issue: the AI took the wrong path early..." |
| ai-03 | Yes | "Was unclear what model was being used, may have gotten quicker results with a better model." |
| ai-05 | Yes | *(no notes)* |
| ai-06 | Yes | "I enjoyed the experience, it reminded me a lot of applying for jobs after university..." |

---

## 3. Code & Git

All participant branches on GitHub: `github.com/gjz78910/GENIUS_pilot`  
Local clones: `~/Downloads/GENIUS_experiment_data/{id}/`

| VM | Branch | Participant Work Commit | Commit Timestamp | Clean at End |
|----|--------|------------------------|------------------|--------------|
| ai-01 | `participant/ai-01` | `b10e37a` | 2026-06-09 ~10:31 | Yes |
| ai-02 | `participant/ai-02` | `45bb0ae` | 2026-06-09 14:44:38 | Yes |
| ai-03 | `participant/ai-03` | `d86391a` | 2026-06-09 14:40:13 | Yes |
| ai-04 | `participant/ai-04` | `d74e1ef` | 2026-06-09 14:22:36 | Yes |
| ai-05 | `participant/ai-05` | `a3c79b4` | 2026-06-09 14:15:10 | Yes |
| ai-06 | `participant/ai-06` | `11d36ad` | 2026-06-09 14:02:31 | Yes |

---

## 4. DATA_COLLECTION Files (in each GitHub branch and local clone)

| File | ai-01 | ai-02 | ai-03 | ai-04 | ai-05 | ai-06 |
|------|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|
| `aggregated_{id}_S1.json` | Yes | Yes | Yes | Yes | Yes | Yes |
| `kiro_metrics_{id}_S1.json` | Yes | Yes | Yes | Yes | Yes | Yes |
| `participant_state_{id}_S1.json` | Yes | Yes | Yes | Yes | Yes | Yes |
| `git_log_{id}_S1.txt` | Yes | Yes | Yes | Yes | Yes | Yes |
| `survey_{id}.json` (pre) | Yes | Yes | Yes | **No** | Yes | **No** |
| `survey_post_{id}.json` | Yes | Yes | Yes | **No** | Yes | Yes |
| `participant_backups/*.tar.gz` | Yes | Yes | Yes | Yes | Yes | Yes |

---

## 5. Kiro Chat Logs

Stored locally in `~/Downloads/GENIUS_experiment_data/{id}_S1/supplemental/`

| VM | Chat API Log | Rotated Log (.1.log) | Session JSONs | Resource Usage |
|----|-------------|----------------------|---------------|----------------|
| ai-01 | 8.1 MB | 29.9 MB | 1 | — |
| ai-02 | 23.5 MB | — | 4 | 222 KB |
| ai-03 | 5.3 MB | 29.6 MB | 2 | 221 KB |
| ai-04 | 15.8 MB | — | 1 | 208 KB |
| ai-05 | 21.9 MB | — | 1 | 200 KB |
| ai-06 | 8.4 MB | — | 1 | 199 KB |

**Total raw Kiro chat log volume:** ~115 MB

---

## 6. Screen Recordings

Stored locally in `~/Downloads/GENIUS_experiment_data/{id}_S1/videos/`

| VM | Local Segments | Local Size | Full Set (S3) |
|----|---------------|------------|---------------|
| ai-01 | 1 | ~158 MB | ~158 MB |
| ai-02 | 3 | ~134 MB | ~620 MB (9 segments) |
| ai-03 | 1 | ~132 MB | ~552 MB (4 segments) |
| ai-04 | 1 | ~130 MB | ~470 MB (4 segments) |
| ai-05 | 1 | ~130 MB | ~390 MB (4 segments) |
| ai-06 | 1 | ~130 MB | ~327 MB (7 segments) |

Full recordings on S3: `experiment-data/{id}_S1/videos/` (~2.9 GB total)  
Videos are split into segments — concatenate with `ffmpeg -f concat` for continuous playback.

---

## 7. What Is Analyzable

| Data Type | Available For | What You Can Analyze |
|-----------|--------------|----------------------|
| Pre-experiment survey | ai-01, ai-02, ai-03, ai-05 (4/6) | Background, experience, commute, DevOps/MLOps maturity |
| Post-experiment survey | ai-01, ai-02, ai-03, ai-05, ai-06 (5/6) | Kiro usage patterns, qualitative feedback |
| Kiro chat history (raw) | All 6 | Prompt patterns, volume, conversation structure |
| Kiro session JSONs | All 6 | Workspace sessions, agent task breakdown |
| Resource usage (CPU/RAM) | ai-02–ai-06 | System load timeline during coding tasks |
| Participant code commits | All 6 | Code changes made during session |
| Participant code backup | All 6 | Full working tree snapshot at session end |
| Screen recordings | All 6 | Coding process, Kiro interaction, time-on-task |
| Git activity log | All 6 | Commit frequency, timing, files changed |

---

## 8. Known Issues

| Issue | Affected |
|-------|---------|
| No surveys submitted | ai-04 — neither pre nor post survey |
| No pre-survey | ai-06 — skipped pre-survey only |
| Resource/metadata files mislabelled `manual-02`/`manual-03` | ai-05, ai-06 — VMs were repurposed from manual group |
| Full video set not downloaded locally | ai-02–ai-06 — remaining segments on S3 only (~2.5 GB) |
