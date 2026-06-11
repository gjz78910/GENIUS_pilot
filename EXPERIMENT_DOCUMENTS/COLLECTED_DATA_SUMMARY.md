# GENIUS Pilot KCL-01 — Collected Data Summary

**Experiment date:** 2026-06-09  
**Group:** AI-assisted coding with Kiro  
**Participants:** ai-01–ai-06 (6 participants)  

---

## 1. Participant Overview

| VM | Role | Seniority | Main Language | Session Start | Session End | DevOps Maturity | MLOps Maturity | Pre-Survey | Post-Survey |
|----|------|-----------|---------------|---------------|-------------|-----------------|----------------|------------|-------------|
| ai-01 | Developer | Mid | Go/Elixir | 09:00 | ~10:31 | 4/5 | 2/5 | Yes | Yes |
| ai-02 | Developer | Senior | Java | 14:00 | ~14:47 | 1/5 | 1/5 | Yes | Yes |
| ai-03 | DevOps Engineer | Mid | Python | 14:00 | 16:08 | 5/5 | 3/5 | Yes | Yes |
| ai-04 | Developer | Mid | Python | 14:00 | ~14:23 | 1/5 | 1/5 | Yes | Yes |
| ai-05 | AI Researcher | Junior | Python | 14:00 | 16:00 | 1/5 | 2/5 | Yes | Yes |
| ai-06 | Developer | Mid | Python | 14:00 | ~14:03 | 1/5 | 4/5 | Yes | Yes |


---

## 2. Post-Survey Highlights

| VM | Used AI Extensively | Notes (excerpt) |
|----|---------------------|-----------------|
| ai-01 | Yes | "During refactoring it was very useful... During bug fixes it started creating docs which took a lot of time — would have been quicker to fix manually." |
| ai-02 | Yes | "Had trouble with the scalability issue: the AI took the wrong path early..." |
| ai-03 | Yes | "Was unclear what model was being used, may have gotten quicker results with a better model." |
| ai-04 | Yes | "I used the AI to pinpoint where errors were occurring, so relied on it more for the test failures tasks. I used it for ideas in the earlier tasks, and for longer explanations to help optimisation." |
| ai-05 | Yes | *(no notes)* |
| ai-06 | Yes | "I enjoyed the experience, it reminded me a lot of applying for jobs after university..." |

---

## 3. Code & Git

| VM | Branch | Participant Work Commit | Commit Timestamp | Clean at End |
|----|--------|------------------------|------------------|--------------|
| ai-01 | `participant/ai-01` | `c4d77c9` | 2026-06-09 ~10:31 | Yes |
| ai-02 | `participant/ai-02` | `45bb0ae` | 2026-06-09 14:44:38 | Yes |
| ai-03 | `participant/ai-03` | `d86391a` | 2026-06-09 14:40:13 | Yes |
| ai-04 | `participant/ai-04` | `d74e1ef` | 2026-06-09 14:22:36 | Yes |
| ai-05 | `participant/ai-05` | `a3c79b4` | 2026-06-09 14:15:10 | Yes |
| ai-06 | `participant/ai-06` | `11d36ad` | 2026-06-09 14:02:31 | Yes |

---

## 4. Data Inventory

| Data File | ai-01 | ai-02 | ai-03 | ai-04 | ai-05 | ai-06 |
|-----------|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|
| `aggregated_{id}_S1.json` | Yes | Yes | Yes | Yes | Yes | Yes |
| `kiro_metrics_{id}_S1.json` | Yes | Yes | Yes | Yes | Yes | Yes |
| `participant_state_{id}_S1.json` | Yes | Yes | Yes | Yes | Yes | Yes |
| `git_log_{id}_S1.txt` | Yes | Yes | Yes | Yes | Yes | Yes |
| `survey_{id}.json` (pre) | Yes | Yes | Yes | Yes | Yes | Yes |
| `survey_post_{id}.json` | Yes | Yes | Yes | Yes | Yes | Yes |
| `participant_backups/*.tar.gz` | Yes | Yes | Yes | Yes | Yes | Yes |
| Kiro Chat API log | Yes | Yes | Yes | Yes | Yes | Yes |
| Kiro session JSON(s) | Yes | Yes | Yes | Yes | Yes | Yes |
| `resource_usage_{id}_S1.jsonl` | Yes | Yes | Yes | Yes | Yes | Yes |
| `session_metadata_{id}-S1.json` | Yes | Yes | Yes | Yes | Yes | Yes |
| `system_info_{id}.json` | Yes | Yes | Yes | Yes | Yes | Yes |
| Screen recordings | Yes | Yes | Yes | Yes | Yes | Yes |
| Task checkpoint results (5 files) | Yes | Yes | Yes | Yes | Yes | Yes |

---

## 5. Task Checkpoint Results

Pass/fail for each task checkpoint run post-session against participant code.

| VM | Task1_cp1 | Task1_cp2 | Task1_cp3 | Task2 | Task3 |
|----|:---------:|:---------:|:---------:|:-----:|:-----:|
| ai-01 | Pass | Pass | Pass | Pass | Pass |
| ai-02 | Pass | Pass | **Fail** | Pass | Pass |
| ai-03 | Pass | Pass | Pass | Pass | Pass |
| ai-04 | Pass | Pass | Pass | Pass | Pass |
| ai-05 | Pass | Pass | Pass | Pass | Pass |
| ai-06 | Pass | Pass | **Fail** | Pass | Pass |

> Task1_cp3 tests scalability performance. ai-02 and ai-06 failed this checkpoint.  
> ai-01 ran a more comprehensive test suite (47/65/74 tests per checkpoint vs 13/19/28 for others).

---

## 6. What Is Analyzable


| Data Type | Available For | What You Can Analyze |
|-----------|--------------|----------------------|
| Pre-experiment survey | All 6 | Background, experience, commute, DevOps/MLOps maturity |
| Post-experiment survey | All 6 | Kiro usage patterns, qualitative feedback |
| Kiro chat history (raw) | All 6 | Prompt patterns, volume, conversation structure |
| Kiro session JSONs | All 6 | Workspace sessions, agent task breakdown |
| Resource usage (CPU/RAM) | All 6 | System load timeline during coding tasks |
| Participant code commits | All 6 | Code changes made during session |
| Participant code backup | All 6 | Full working tree snapshot at session end |
| Screen recordings | All 6 | Coding process, Kiro interaction, time-on-task |
| Git activity log | All 6 | Commit frequency, timing, files changed |
| Task checkpoint results | All 6 | Pass/fail per task (Task1_cp1, Task1_cp2, Task1_cp3, Task2, Task3) |

