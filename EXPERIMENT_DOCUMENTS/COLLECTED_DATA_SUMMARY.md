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

## 5. Kiro Analytics

All participants used **Kiro Pro** (1000 credits/month, $0.04/credit overage). Default model: `auto` (Kiro routes internally). All sessions within the free monthly quota — **no overage charges**.

| VM | Credits Used | Model Selection | Auto Calls | Opus 4.8 Calls | Chat Messages | Agent Actions | Autocomplete |
|----|:------------:|-----------------|:----------:|:--------------:|:-------------:|:-------------:|:------------:|
| ai-01 | 63.14 | auto / Autopilot | 22,183 | — | 28 | 28 | 0 |
| ai-02 | 155.94 | **claude-opus-4.8** (3 sessions) / Supervised | 2,033 | 530 | 27 | 27 | 0 |
| ai-03 | 151.84 | auto / Autopilot | 4,998 | — | 18 | 18 | 0 |
| ai-04 | 155.94 | auto / Autopilot | 2,776 | — | 26 | 26 | 0 |
| ai-05 | 155.94 | auto / Autopilot | 3,009 | — | 15 | 15 | 0 |
| ai-06 | 96.05 | auto / Autopilot | 1,036 | — | 13 | 13 | 0 |

> Chat messages and agent actions are user-turn counts from kiro_session JSONs (true AI interactions).  
> kiro_metrics also records log-derived inflated counts: 119/231/149/189/149/102 chat events; 837/676/739/436/483/190 agent events.  
> LLM API requests (q-client.log): 10/130/103/95/90/56 for ai-01–ai-06.  
> Autocomplete log was 0 bytes for all participants — inline autocomplete was not used.  
> Raw logs per participant: `q-client.log`, `kiro_llm_promptcompletion.log`, `tokens_generated.jsonl` in `{id}_S1/kiro_logs/`.  
> Credit rate multipliers: `auto` = 1×, Claude Opus 4.8 = 2.2×, Claude Sonnet = 1.3×.  
> ai-02 used Supervised mode (human approval per step); all others used Autopilot mode.

---

## 6. Task Checkpoint Results

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

## 7. What Is Analyzable

### 7.1 Task Performance & Code Quality

**Research question:** Did participants complete the tasks, and how correct/complete was their code?

| Metric | Data Source | Notes | Data Available |
|--------|-------------|-------|:--------------:|
| Checkpoint pass/fail (5 per participant) | `supplemental/Task{N}_{id}_S1.json` | ai-02, ai-06 failed Task1_cp3 (scalability) | Yes |
| Tests run per checkpoint | Same — `test_statistics.tests_run` | ai-01: 47/65/74 tests; others: 13/19/28 — different test suite coverage | Yes |
| Test failure detail | Same — `failures`, `errors` counts | All failures at Task1_cp3 only | Yes |
| Code correctness per task | Checkpoint pass × tests run | Task1 (routing), Task2 (scheduling), Task3 (reporting) | Yes |

**Key observations:** 4 of 6 achieved perfect pass rates. Scalability checkpoint (Task1_cp3) was the only discriminating test — requiring efficient 2-opt routing under time constraints. Test suite depth varies dramatically: ai-01 ran 3–4× more tests than others.

---

### 7.2 AI Interaction Intensity & Patterns

**Research question:** How extensively and how did participants use AI assistance?

| Metric | Data Source | Notes | Data Available |
|--------|-------------|-------|:--------------:|
| User chat turns | kiro_session JSON `chatMessages` | 28 / 27 / 18 / 26 / 15 / 13 (ai-01–ai-06) | Yes |
| LLM API requests made | `q-client.log` (`ListConversationsCommand` counts) | 10 / 130 / 103 / 95 / 90 / 56 | Yes |
| Kiro sessions opened | kiro_session JSON session count | 1 / 4 / 2 / 1 / 1 / 1 | Yes |
| Agent actions triggered | kiro_session JSON `agentExecutions` | Same count as chat turns (1:1 ratio — each chat turn became an agent action) | Yes |
| AI autonomy mode | kiro_session JSON `autonomyMode` | ai-02: Supervised; all others: Autopilot | Yes |
| Chat content types | kiro_session JSON `chatMessages[].content` | Can be coded: implement / debug / explain / refactor / other | Partial — **manual**: raw text in local session JSONs; semantic classification by human |
| Agent tools used per session | kiro_session JSON `agentExecutions[].toolCalls` | Tool types: file_read, file_write, terminal, search | Yes |
| Prompt length distribution | kiro_session JSON or Chat API log | Character/word counts per user message | Yes |
| Response length distribution | Chat API log `5-Q Chat API.log` | Token counts per response; correlate with task complexity | Yes |
| Conversation depth | Sessions: messages per conversation | ai-02 had 4 conversations (multi-session); others: 1–2 | Yes |

**Inflated log counts** (from `kiro_metrics_{id}_S1.json`): chat_messages 119/231/149/189/149/102 — these count log events per request (not user turns); useful for comparing relative logging intensity.

**Agent intent classification** (from `Kiro_Logs.log` `[Agent Classifier]` events — "chat" = question/explain, "do" = implement/run, "spec" = generate spec document):

| VM | Chat % | Do % | Spec % | Total classified |
|----|:------:|:----:|:------:|:---------------:|
| ai-01 | 0% | 67% | 33% | 3 |
| ai-02 | 48% | 52% | 0% | 27 |
| ai-03 | — | — | — | (spec agent triggered directly — see 7.12) |
| ai-04 | 62% | 31% | 8% | 26 |
| ai-05 | 27% | 73% | 0% | 15 |
| ai-06 | 62% | 31% | 8% | 13 |

> ai-01 almost entirely "do" mode (agent tasks); ai-05 similarly "do"-heavy. ai-02/04/06 split between chat and do. ai-02 (Supervised mode) had higher chat% — consistent with a more question-and-verify pattern vs autonomous agent execution.

---

### 7.3 AI Efficiency & Credit Economics

**Research question:** How much did AI assistance cost per unit of output, and was it cost-effective?

| Metric | Formula / Source | ai-01 | ai-02 | ai-03 | ai-04 | ai-05 | ai-06 | Data Available |
|--------|-----------------|-------|-------|-------|-------|-------|-------|:--------------:|
| Credits consumed | `kiro_analytics_{id}_S1.json` | 63.1 | 155.9 | 151.8 | 155.9 | 155.9 | 96.1 | Yes |
| Credits per chat message | credits ÷ chat turns | 2.3 | 5.8 | 8.4 | 6.0 | 10.4 | 7.4 | Yes |
| Credits per checkpoint passed | credits ÷ tasks passed (5 or 4) | 12.6 | 39.0 | 30.4 | 31.2 | 31.2 | 24.0 | Yes |
| Model multiplier impact | ai-02 used Opus 4.8 (2.2×) vs auto (1×) | — | +2.2× rate | — | — | — | — | Yes |
| Overage cost | credits > 1000 | $0 | $0 | $0 | $0 | $0 | $0 | Yes |

All sessions within the free monthly 1000-credit quota. Hypothetical overage at $0.04/credit: ai-01's 63 credits would cost $2.52 at pay-per-use; ai-02's 156 would cost $6.24.

---

### 7.4 Code Change Analysis

**Research question:** What did participants actually build — volume and nature of changes?

| Participant | Files Changed | Lines Added | Lines Deleted | Net Lines | Data Available |
|-------------|:-------------:|:-----------:|:-------------:|:---------:|:--------------:|
| ai-01 | 6 | +946 | -30 | +916 | Yes |
| ai-02 | 4 | +1,062 | -146 | +916 | Yes |
| ai-03 | 4 | +542 | -85 | +457 | Yes |
| ai-04 | 7 | +319 | -9 | +310 | Yes |
| ai-05 | 4 | +320 | -152 | +168 | Yes |
| ai-06 | 4 | +303 | -78 | +225 | Yes |

> Source: git diff against baseline commit `f1bc878` (main HEAD at experiment start) for ai-02–ai-06 (from participant work commit); backup tarball diff for ai-01.  
> All changes are in `src/` and `tests/` only (excludes DATA_COLLECTION/).

**Further analyzable:**
- File-level breakdown: which src modules were modified (routing.py, matching.py, report.py, data_loader.py)
- Test file additions vs source file changes (ratio of test to implementation code)
- Diff quality: code correctness inferred from checkpoint pass rate + lines changed
- `.kiro/specs/` directory (in participant backups): AI-generated task specs; compare spec intent vs actual implementation

---

### 7.5 Session Duration & Productivity

**Research question:** How efficiently did participants complete the work, and how does time correlate with output?

| VM | Session Duration | Chat Msgs | Code Lines Added | LLM Requests | Lines/Min | Data Available |
|----|:----------------:|:---------:|:----------------:|:------------:|:---------:|:--------------:|
| ai-01 | ~91 min | 28 | +946 | 10 | 10.4 | Yes |
| ai-02 | ~44 min | 27 | +1,062 | 130 | 24.1 | Yes |
| ai-03 | ~128 min | 18 | +542 | 103 | 4.2 | Yes |
| ai-04 | ~22 min | 26 | +319 | 95 | 14.5 | Yes |
| ai-05 | ~15 min | 15 | +320 | 90 | 21.3 | Yes |
| ai-06 | ~2 min | 13 | +303 | 56 | 151.5 | Yes |

> Session duration = git participant work commit timestamp − session start (09:00 for ai-01, 14:00 for all others).  
> ai-06's 2-minute duration and 303 lines suggests pre-prepared code or copy-paste; warrants screen recording review.  
> ai-05's 15 minutes for 320 lines is also notably fast.

**Further analyzable:**
- Credits per minute of session
- LLM API requests per minute (measures AI interaction cadence)
- Agent file_changes (kiro_metrics) ÷ duration = AI-driven edit rate

---

### 7.6 Individual Differences & Background Correlations

**Research question:** How do participant backgrounds predict AI usage and task performance?

| Dimension | Data Source | Variables | Data Available |
|-----------|-------------|-----------|:--------------:|
| DevOps/MLOps maturity | Pre-survey `survey_{id}.json` | Scale 1–5; ai-03 = 5/3 (outlier — DevOps engineer) | Yes |
| Seniority level | Pre-survey | Junior (ai-05), Mid (ai-01/03/04/06), Senior (ai-02) | Yes |
| Primary language | Pre-survey | Python (ai-03–06), Java (ai-02), Go/Elixir (ai-01) | Yes |
| AI tool prior experience | Pre-survey (AI tooling section) | Frequency/tools used before experiment | Yes |
| Commute mode | Pre-survey | Car/public transport — sustainability context | Yes |

**Correlations to test:**
- Seniority vs credits used (hypothesis: seniors use AI more strategically = fewer credits)
- Primary language match (Python) vs task performance — ai-01 (Go/Elixir) and ai-02 (Java) coding in Python; did this affect outcomes?
- DevOps maturity vs error count (kiro_metrics errors)
- MLOps maturity vs agent mode preference (Supervised vs Autopilot)
- Prior AI tool experience vs interaction pattern (prompt length, conversation depth)

---

### 7.7 AI Model & Configuration Choice Impact

**Research question:** Did model selection or autonomy mode affect outcomes or cost?

| Factor | ai-02 | All Others | Data Available |
|--------|-------|-----------|:--------------:|
| Model | claude-opus-4.8 (explicit, 3/4 sessions) | auto (Kiro routes internally) | Yes |
| Autonomy mode | Supervised (human approval per step) | Autopilot | Yes |
| Credit rate multiplier | 2.2× | 1× | Yes |
| Credits consumed | 155.94 | 63–156 (range) | Yes |
| LLM API requests | 130 | 10–103 | Yes |
| Chat turns | 27 | 13–28 | Yes |
| Checkpoint pass rate | 4/5 (failed scalability) | 4/5 or 5/5 | Yes |

**Analysis:** ai-02 explicitly selected Opus 4.8 and Supervised mode, which: (a) increased credit cost per interaction, (b) generated far more LLM API requests (130 vs 10–103 for auto participants), (c) required human approval at each agent step (visible in screen recording). Post-survey notes: "Had trouble with the scalability issue: the AI took the wrong path early" — suggesting Supervised mode did not prevent suboptimal paths.

---

### 7.8 Resource Usage Timeline

**Research question:** How did AI interactions correlate with system load?

| Metric | Data Source | Notes | Data Available |
|--------|-------------|-------|:--------------:|
| CPU usage over time | `resource_usage_{id}_S1.jsonl` (1Hz samples) | Spikes during agent file writes / test runs | Yes |
| RAM usage over time | Same | Baseline ~1–2 GB; spikes during Python test execution | Yes |
| GPU usage | Same | Expected 0 — no ML training in tasks | Yes |
| CPU/RAM spike correlation with AI events | Cross-reference with kiro_session JSON timestamps | When agent ran tests: CPU spike; when writing files: I/O | **Yes — computed below** |

**CPU and RAM at AI call times vs overall session average** (computed from q-client.log timestamps × resource_usage_jsonl):

| VM | CPU avg at AI calls | CPU session avg | CPU lift | RAM avg at AI calls | RAM session avg |
|----|:-------------------:|:---------------:|:--------:|:-------------------:|:---------------:|
| ai-01 | 39.5% | 32.7% | +6.8pp | 38.3% | 36.1% |
| ai-02 | 71.0% | 20.8% | +50.2pp | 41.4% | 31.0% |
| ai-03 | 54.7% | 17.4% | +37.3pp | 37.8% | 28.6% |
| ai-04 | 34.2% | 10.8% | +23.4pp | 36.7% | 27.8% |
| ai-05 | 69.7% | 13.4% | +56.3pp | 37.8% | 26.7% |
| ai-06 | 36.8% | 11.0% | +25.8pp | 33.8% | 25.9% |

> "CPU lift" = CPU during AI calls minus session average. High lift (ai-02: +50pp, ai-05: +56pp) indicates the agent was actively running tests/writes during its turns. Low lift (ai-01: +7pp) reflects ai-01's long idle session with steady background activity.  
> Matched 251–131/56 of AI calls to resource records within a 30s window.  
> All participants: GPU usage = 0% throughout (no ML workloads).

---

### 7.9 Error Patterns & Recovery

**Research question:** How many errors occurred and how did participants use AI to recover?

**kiro_metrics error counts** (stderr events from terminal/test output — not Kiro extension errors):

| VM | kiro_metrics Errors | LLM Requests | Errors per LLM Request | Task Outcome | Data Available |
|----|:-------------------:|:------------:|:----------------------:|:------------:|:--------------:|
| ai-01 | 1,666 | 10 | 166.6 | 5/5 pass | Yes |
| ai-02 | 391 | 130 | 3.0 | 4/5 pass | Yes |
| ai-03 | 632 | 103 | 6.1 | 5/5 pass | Yes |
| ai-04 | 305 | 95 | 3.2 | 5/5 pass | Yes |
| ai-05 | 339 | 90 | 3.8 | 5/5 pass | Yes |
| ai-06 | 170 | 56 | 3.0 | 4/5 pass | Yes |

> kiro_metrics `errors` counts stderr events from terminal commands run by the agent (test failures, tracebacks, warnings). These are NOT the same as Kiro extension errors below.  
> ai-01's extreme ratio reflects accumulated test output across a long single session; all checkpoints still passed.

**Kiro extension errors** (from `Kiro_Logs.log`, excluding auth startup errors present on all VMs):

| VM | Total Kiro Errors | Model Throttle | Agent Execution Stuck | Test/Assert | Other | Data Available |
|----|:-----------------:|:--------------:|:---------------------:|:-----------:|:-----:|:--------------:|
| ai-01 | 4 | 1 | 0 | 3 | 0 | Yes |
| ai-02 | 13 | 13 | 0 | 0 | 0 | Yes |
| ai-03 | 115 | 1 | 113 | 1 | 0 | Yes |
| ai-04 | 20 | 20 | 0 | 0 | 0 | Yes |
| ai-05 | 6 | 6 | 0 | 0 | 0 | Yes |
| ai-06 | 9 | 9 | 0 | 0 | 0 | Yes |

> **ai-03 critical finding**: 113 "Execution is not running, current state: yielded" errors — the agent's execution engine got stuck in a yielded/suspended state repeatedly across the session, requiring Kiro to cancel and restart each execution. This explains ai-03's 128-min session (longest of all), the 2 sessions, and the post-survey note about model uncertainty. Despite this, ai-03 passed all 5 checkpoints.  
> **ai-02/04/05/06 model throttle errors**: model rate limiting during the session. ai-02 (Opus 4.8 explicit) and ai-04 both hit 13–20 throttle errors; ai-05/06 hit 6–9. ai-01 barely throttled (1 event) despite highest auto-call count.

**Error → AI request latency** (time between a Kiro error and the next LLM API call — proxy for how quickly participants asked AI for help after an error):

| VM | Errors → AI call | Median latency | Within 60s | Data Available |
|----|:----------------:|:--------------:|:----------:|:--------------:|
| ai-01 | 4/4 | 10s | 75% | Yes |
| ai-02 | 13/13 | 12s | 69% | Yes |
| ai-03 | 115/115 | 15s | 80% | Yes |
| ai-04 | 20/20 | 4s | 85% | Yes |
| ai-05 | 6/6 | 3s | 100% | Yes |
| ai-06 | 9/9 | 1s | 100% | Yes |

> Every error was followed by an AI call. Shorter-session participants (ai-05: 3s, ai-06: 1s) asked immediately; longer-session participants (ai-01: 10s, ai-03: 15s) paused briefly before asking. 69–100% of errors prompted an AI call within 60 seconds.

---

### 7.10 Qualitative & Survey Analysis

**Research question:** What were participants' subjective experiences and strategies?

| Source | Analyzable Content | Data Available |
|--------|--------------------|:--------------:|
| Pre-survey (`survey_{id}.json`) | Background, prior AI experience, DevOps/MLOps maturity, commute | Yes — all 6 |
| Post-survey (`survey_post_{id}.json`) | AI usefulness rating, task-specific feedback, frustrations, suggestions | Yes — all 6 |
| Post-survey free text | See Section 2 highlights; full text in JSON for thematic analysis | Yes — all 6 |
| Kiro spec files (`.kiro/specs/`) | Agent-generated task decomposition specs; quality/accuracy assessment | Partial — ai-01 **Yes** (in backup); ai-02–06 **VM needed** (`.kiro/` not included in their backup tarballs) |

**Coding scheme for post-survey themes:**
- AI helpfulness: high (ai-01, ai-04, ai-05) / mixed (ai-02, ai-03) / unclear (ai-06)
- Frustration sources: wrong direction early (ai-02), slow doc generation (ai-01), model uncertainty (ai-03)
- Tasks where AI excelled: bug pinpointing (ai-04), refactoring (ai-01), initial scaffolding
- Tasks where AI underperformed: scalability (ai-02), prolonged doc generation (ai-01)

---

### 7.11 Screen Recording Analysis

**Research question:** How did participants allocate time between coding, AI chat, and testing?

| Metric | How to Measure | Data Available |
|--------|----------------|:--------------:|
| Time in Kiro chat panel | Screen region classification — identify Kiro chat window open | Partial — **manual**: recordings already downloaded |
| Time in code editor | Screen region — VS Code / editor focus | Partial — **manual**: recordings already downloaded |
| Time in terminal | Terminal window visible and active | Partial — **manual**: recordings already downloaded |
| Number of AI chat interactions (manual count) | Count message send events visible on screen | Partial — **manual**: recordings already downloaded |
| Scrolling / review behaviour | Passive reading vs active typing | Partial — **manual**: recordings already downloaded |
| Copy-paste of AI output | Ctrl+C/V events visible; clipboard content | Partial — **manual**: recordings already downloaded |
| Kiro agent taking actions on screen | Agent progress bar / file modification indicators | Partial — **manual**: recordings already downloaded |

> Screen recordings are in `{id}_S1/videos/`. Duration and timestamps can be cross-referenced with git commit timestamps and resource usage.  
> ai-06 and ai-05 warrant close review given their very short session durations (2 min and 15 min).

---

### 7.12 .kiro/specs Analysis

**Research question:** How did the AI decompose tasks, and did the spec match the implementation?

Kiro's "Specs" feature generates a task breakdown before coding. **Only ai-01 used it** — confirmed by checking all 6 VMs and backup tarballs. ai-02–06 have no `.kiro/specs` anywhere on disk.

**ai-01 spec creation timeline** (from file modification timestamps in Kiro globalStorage, UTC):

| Spec | Document | Created (UTC) | BST | Elapsed (from 08:00 UTC session start) |
|------|----------|:-------------:|:---:|:--------------------------------------:|
| nearest-neighbor-2opt-routing | `.config.kiro` | 08:53 | 09:53 | +53 min |
| nearest-neighbor-2opt-routing | `requirements.md` | 08:57 | 09:57 | +57 min |
| nearest-neighbor-2opt-routing | `design.md` | 08:59 | 09:59 | +59 min |
| nearest-neighbor-2opt-routing | `tasks.md` | 09:00 | 10:00 | +60 min |
| two-pass-matching | `.config.kiro` | 09:33 | 10:33 | +93 min |
| two-pass-matching | `design.md` | 09:38 | 10:38 | +98 min |
| two-pass-matching | `tasks.md` | 09:40 | 10:40 | +100 min |
| report-generation-fix | `.config.kiro` | 09:58 | 10:58 | +118 min |
| report-generation-fix | `design.md` | 10:00 | 11:00 | +120 min |
| report-generation-fix | `tasks.md` | 10:01 | 11:01 | +121 min |

> ai-01 created specs for all 3 tasks at ~60, 93, and 118 minutes into the session. Each spec took ~7 minutes to generate (config → requirements → design → tasks). First spec aligned with Task 1 (routing). ai-03 triggered `spec-generation` agent at 13:31 BST but no spec files were written to disk — likely cancelled.

| Metric | What to Look For | Data Available |
|--------|-----------------|:--------------:|
| Spec accuracy (ai-01) | Did the AI correctly identify required modules and functions? | Partial — **manual**: spec text already local (backup tarball) |
| Spec completeness (ai-01) | Did it cover all 3 tasks? | Yes — confirmed 3 specs: routing, matching, report |
| Spec vs implementation divergence (ai-01) | Lines in spec not implemented; code beyond spec | Partial — **manual**: spec text and code diff both local |
| Spec creation times (ai-01) | When was spec created vs when did coding start? | **Yes — computed above** |
| ai-02–06 spec usage | Did they use specs? | Yes — **none did** (confirmed on VMs) |

---

### 7.13 Sustainability / Carbon Proxy

**Research question:** What is the environmental footprint of this AI-assisted coding session?

| Dimension | Data Source | Notes | Data Available |
|-----------|-------------|-------|:--------------:|
| AI compute energy proxy | Kiro credits / prompt tokens from `kiro_analytics_{id}_S1.json` | ~0.002 kWh per 1000 prompt tokens (literature estimate, high uncertainty) | Yes |
| Commute carbon | Pre-survey `city_home`, `commute_car`, `commute_public_transport`, `car_trips_per_day` | Intra-city distance estimated by city: Ipswich ~5 km, London ~12 km, Oxford ~8 km | Yes |
| Cloud VM energy | Session duration × t3.medium avg 5 W, UK grid 0.207 kg CO₂/kWh | eu-west-2 = UK region | Yes |
| Aggregate calculation | All inputs combined | **Computed below** | Yes |

**Computed carbon estimates per participant per session:**

| VM | Commute mode | Commute kg CO₂ | VM kWh | VM kg CO₂ | AI energy kWh | AI kg CO₂ | **Total kg CO₂** |
|----|:-------------|:--------------:|:------:|:---------:|:-------------:|:---------:|:----------------:|
| ai-01 | car ~5 km/day | 0.855 | 0.0076 | 0.0016 | 0.044 | 0.009 | **0.866** |
| ai-02 | remote (no commute) | 0.000 | 0.0037 | 0.0008 | 0.004 | 0.001 | **0.002** |
| ai-03 | remote (no commute) | 0.000 | 0.0107 | 0.0022 | 0.010 | 0.002 | **0.004** |
| ai-04 | car ~10 km/day | 1.710 | 0.0018 | 0.0004 | 0.006 | 0.001 | **1.712** |
| ai-05 | car ~10 km/day | 1.710 | 0.0013 | 0.0003 | 0.006 | 0.001 | **1.712** |
| ai-06 | bus ~10 km/day | 0.890 | 0.0002 | 0.0000 | 0.002 | 0.000 | **0.890** |

> Key finding: commute CO₂ dominates by ~100×. For car commuters (ai-01/04/05), the entire cloud VM + AI inference adds <1% to the daily carbon footprint versus not commuting.  
> ai-02 and ai-03 (remote workers) had near-zero session CO₂ (0.002–0.004 kg).  
> Assumptions: car = 0.171 kg CO₂/km (UK BEIS 2024), bus = 0.089 kg/km, UK grid = 0.207 kg CO₂/kWh.

---

### 7.14 Summary: Key Comparisons Enabled

| Comparison | Participants | Data Sources | Data Available |
|------------|-------------|-------------|:--------------:|
| Autopilot vs Supervised mode | ai-02 vs rest | Credits, LLM requests, file changes, checkpoint results, screen recordings | Yes |
| Opus 4.8 vs auto model | ai-02 vs rest | Credits × 2.2 multiplier; output quality (checkpoint results) | Yes |
| Short sessions vs long sessions | ai-06/ai-05 vs ai-01/ai-03 | Code output, checkpoints, credits — efficiency per minute | Yes |
| Python-native vs non-Python participants | ai-03–06 vs ai-01 (Go/Elixir), ai-02 (Java) | Task performance, prompt patterns, error rates | Yes |
| High-DevOps-maturity vs low | ai-03 (5/5) vs ai-02/ai-04/ai-05/ai-06 (1/5) | AI usage strategy, error patterns, task performance | Yes |
| Single long context vs multi-session | ai-01/ai-04–06 (1 session) vs ai-02 (4), ai-03 (2) | Context management, credit efficiency | Yes |

