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

| Metric | Data Source | Notes |
|--------|-------------|-------|
| Checkpoint pass/fail (5 per participant) | `supplemental/Task{N}_{id}_S1.json` | ai-02, ai-06 failed Task1_cp3 (scalability) |
| Tests run per checkpoint | Same — `test_statistics.tests_run` | ai-01: 47/65/74 tests; others: 13/19/28 — different test suite coverage |
| Test failure detail | Same — `failures`, `errors` counts | All failures at Task1_cp3 only |
| Code correctness per task | Checkpoint pass × tests run | Task1 (routing), Task2 (scheduling), Task3 (reporting) |

**Key observations:** 4 of 6 achieved perfect pass rates. Scalability checkpoint (Task1_cp3) was the only discriminating test — requiring efficient 2-opt routing under time constraints. Test suite depth varies dramatically: ai-01 ran 3–4× more tests than others.

---

### 7.2 AI Interaction Intensity & Patterns

**Research question:** How extensively and how did participants use AI assistance?

| Metric | Data Source | Notes |
|--------|-------------|-------|
| User chat turns | kiro_session JSON `chatMessages` | 28 / 27 / 18 / 26 / 15 / 13 (ai-01–ai-06) |
| LLM API requests made | `q-client.log` (`ListConversationsCommand` counts) | 10 / 130 / 103 / 95 / 90 / 56 |
| Kiro sessions opened | kiro_session JSON session count | 1 / 4 / 2 / 1 / 1 / 1 |
| Agent actions triggered | kiro_session JSON `agentExecutions` | Same count as chat turns (1:1 ratio — each chat turn became an agent action) |
| AI autonomy mode | kiro_session JSON `autonomyMode` | ai-02: Supervised; all others: Autopilot |
| Chat content types | kiro_session JSON `chatMessages[].content` | Can be coded: implement / debug / explain / refactor / other |
| Agent tools used per session | kiro_session JSON `agentExecutions[].toolCalls` | Tool types: file_read, file_write, terminal, search |
| Prompt length distribution | kiro_session JSON or Chat API log | Character/word counts per user message |
| Response length distribution | Chat API log `5-Q Chat API.log` | Token counts per response; correlate with task complexity |
| Conversation depth | Sessions: messages per conversation | ai-02 had 4 conversations (multi-session); others: 1–2 |

**Inflated log counts** (from `kiro_metrics_{id}_S1.json`): chat_messages 119/231/149/189/149/102 — these count log events per request (not user turns); useful for comparing relative logging intensity.

---

### 7.3 AI Efficiency & Credit Economics

**Research question:** How much did AI assistance cost per unit of output, and was it cost-effective?

| Metric | Formula / Source | ai-01 | ai-02 | ai-03 | ai-04 | ai-05 | ai-06 |
|--------|-----------------|-------|-------|-------|-------|-------|-------|
| Credits consumed | `kiro_analytics_{id}_S1.json` | 63.1 | 155.9 | 151.8 | 155.9 | 155.9 | 96.1 |
| Credits per chat message | credits ÷ chat turns | 2.3 | 5.8 | 8.4 | 6.0 | 10.4 | 7.4 |
| Credits per checkpoint passed | credits ÷ tasks passed (5 or 4) | 12.6 | 39.0 | 30.4 | 31.2 | 31.2 | 24.0 |
| Model multiplier impact | ai-02 used Opus 4.8 (2.2×) vs auto (1×) | — | +2.2× rate | — | — | — | — |
| Overage cost | credits > 1000 | $0 | $0 | $0 | $0 | $0 | $0 |

All sessions within the free monthly 1000-credit quota. Hypothetical overage at $0.04/credit: ai-01's 63 credits would cost $2.52 at pay-per-use; ai-02's 156 would cost $6.24.

---

### 7.4 Code Change Analysis

**Research question:** What did participants actually build — volume and nature of changes?

| Participant | Files Changed | Lines Added | Lines Deleted | Net Lines |
|-------------|:-------------:|:-----------:|:-------------:|:---------:|
| ai-01 | 6 | +946 | -30 | +916 |
| ai-02 | 4 | +1,062 | -146 | +916 |
| ai-03 | 4 | +542 | -85 | +457 |
| ai-04 | 7 | +319 | -9 | +310 |
| ai-05 | 4 | +320 | -152 | +168 |
| ai-06 | 4 | +303 | -78 | +225 |

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

| VM | Session Duration | Chat Msgs | Code Lines Added | LLM Requests | Lines/Min |
|----|:----------------:|:---------:|:----------------:|:------------:|:---------:|
| ai-01 | ~91 min | 28 | +946 | 10 | 10.4 |
| ai-02 | ~44 min | 27 | +1,062 | 130 | 24.1 |
| ai-03 | ~128 min | 18 | +542 | 103 | 4.2 |
| ai-04 | ~22 min | 26 | +319 | 95 | 14.5 |
| ai-05 | ~15 min | 15 | +320 | 90 | 21.3 |
| ai-06 | ~2 min | 13 | +303 | 56 | 151.5 |

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

| Dimension | Data Source | Variables |
|-----------|-------------|-----------|
| DevOps/MLOps maturity | Pre-survey `survey_{id}.json` | Scale 1–5; ai-03 = 5/3 (outlier — DevOps engineer) |
| Seniority level | Pre-survey | Junior (ai-05), Mid (ai-01/03/04/06), Senior (ai-02) |
| Primary language | Pre-survey | Python (ai-03–06), Java (ai-02), Go/Elixir (ai-01) |
| AI tool prior experience | Pre-survey (AI tooling section) | Frequency/tools used before experiment |
| Commute mode | Pre-survey | Car/public transport — sustainability context |

**Correlations to test:**
- Seniority vs credits used (hypothesis: seniors use AI more strategically = fewer credits)
- Primary language match (Python) vs task performance — ai-01 (Go/Elixir) and ai-02 (Java) coding in Python; did this affect outcomes?
- DevOps maturity vs error count (kiro_metrics errors)
- MLOps maturity vs agent mode preference (Supervised vs Autopilot)
- Prior AI tool experience vs interaction pattern (prompt length, conversation depth)

---

### 7.7 AI Model & Configuration Choice Impact

**Research question:** Did model selection or autonomy mode affect outcomes or cost?

| Factor | ai-02 | All Others |
|--------|-------|-----------|
| Model | claude-opus-4.8 (explicit, 3/4 sessions) | auto (Kiro routes internally) |
| Autonomy mode | Supervised (human approval per step) | Autopilot |
| Credit rate multiplier | 2.2× | 1× |
| Credits consumed | 155.94 | 63–156 (range) |
| LLM API requests | 130 | 10–103 |
| Chat turns | 27 | 13–28 |
| Checkpoint pass rate | 4/5 (failed scalability) | 4/5 or 5/5 |

**Analysis:** ai-02 explicitly selected Opus 4.8 and Supervised mode, which: (a) increased credit cost per interaction, (b) generated far more LLM API requests (130 vs 10–103 for auto participants), (c) required human approval at each agent step (visible in screen recording). Post-survey notes: "Had trouble with the scalability issue: the AI took the wrong path early" — suggesting Supervised mode did not prevent suboptimal paths.

---

### 7.8 Resource Usage Timeline

**Research question:** How did AI interactions correlate with system load?

| Metric | Data Source | Notes |
|--------|-------------|-------|
| CPU usage over time | `resource_usage_{id}_S1.jsonl` (1Hz samples) | Spikes during agent file writes / test runs |
| RAM usage over time | Same | Baseline ~1–2 GB; spikes during Python test execution |
| GPU usage | Same | Expected 0 — no ML training in tasks |
| CPU/RAM spike correlation with AI events | Cross-reference with kiro_session JSON timestamps | When agent ran tests: CPU spike; when writing files: I/O |

**Further analyzable:**
- Identify periods of high activity (agent runs) vs idle (reading/thinking)
- Estimate "agent-active" time vs "human-active" time from CPU patterns
- Validate session duration estimates against resource activity end time

---

### 7.9 Error Patterns & Recovery

**Research question:** How many errors occurred and how did participants use AI to recover?

| VM | kiro_metrics Errors | LLM Requests | Errors per LLM Request | Task Outcome |
|----|:-------------------:|:------------:|:----------------------:|:------------:|
| ai-01 | 1,666 | 10 | 166.6 | 5/5 pass |
| ai-02 | 391 | 130 | 3.0 | 4/5 pass |
| ai-03 | 632 | 103 | 6.1 | 5/5 pass |
| ai-04 | 305 | 95 | 3.2 | 5/5 pass |
| ai-05 | 339 | 90 | 3.8 | 5/5 pass |
| ai-06 | 170 | 56 | 3.0 | 4/5 pass |

> `errors` in kiro_metrics counts stderr events in logs (includes Python warnings, test failures, stack traces).  
> ai-01's extreme ratio (166 errors per LLM request) reflects a single large session that accumulated test errors over time, not necessarily more failure — they still passed all 5 checkpoints.

**Further analyzable:**
- Error timeline: when did errors cluster? (cross-reference with kiro_session timestamps)
- Error type classification: Python tracebacks vs test failures vs system warnings
- Error → AI request latency: did participants immediately ask AI after an error?

---

### 7.10 Qualitative & Survey Analysis

**Research question:** What were participants' subjective experiences and strategies?

| Source | Available | Analyzable Content |
|--------|-----------|-------------------|
| Pre-survey (`survey_{id}.json`) | All 6 | Background, prior AI experience, DevOps/MLOps maturity, commute |
| Post-survey (`survey_post_{id}.json`) | All 6 | AI usefulness rating, task-specific feedback, frustrations, suggestions |
| Post-survey free text | All 6 | See Section 2 highlights; full text in JSON for thematic analysis |
| Kiro spec files (`.kiro/specs/`) | ai-01 (confirmed), others in backups | Agent-generated task decomposition specs; quality/accuracy assessment |

**Coding scheme for post-survey themes:**
- AI helpfulness: high (ai-01, ai-04, ai-05) / mixed (ai-02, ai-03) / unclear (ai-06)
- Frustration sources: wrong direction early (ai-02), slow doc generation (ai-01), model uncertainty (ai-03)
- Tasks where AI excelled: bug pinpointing (ai-04), refactoring (ai-01), initial scaffolding
- Tasks where AI underperformed: scalability (ai-02), prolonged doc generation (ai-01)

---

### 7.11 Screen Recording Analysis

**Research question:** How did participants allocate time between coding, AI chat, and testing?

| Metric | How to Measure |
|--------|---------------|
| Time in Kiro chat panel | Screen region classification — identify Kiro chat window open |
| Time in code editor | Screen region — VS Code / editor focus |
| Time in terminal | Terminal window visible and active |
| Number of AI chat interactions (manual count) | Count message send events visible on screen |
| Scrolling / review behaviour | Passive reading vs active typing |
| Copy-paste of AI output | Ctrl+C/V events visible; clipboard content |
| Kiro agent taking actions on screen | Agent progress bar / file modification indicators |

> Screen recordings are in `{id}_S1/videos/`. Duration and timestamps can be cross-referenced with git commit timestamps and resource usage.  
> ai-06 and ai-05 warrant close review given their very short session durations (2 min and 15 min).

---

### 7.12 .kiro/specs Analysis

**Research question:** How did the AI decompose tasks, and did the spec match the implementation?

Kiro's "Specs" feature generates a task breakdown before coding. Present in participant backups (confirmed in ai-01's backup: `.kiro/specs/nearest-neighbor-2opt-routing/`, `.kiro/specs/report-g...`).

| Metric | What to Look For |
|--------|-----------------|
| Spec accuracy | Did the AI correctly identify required modules and functions? |
| Spec completeness | Did it cover all 3 tasks or only the first one? |
| Spec vs implementation divergence | Lines in spec that weren't implemented; code written beyond spec |
| Spec creation time | From session JSON timestamps — when was spec created vs when did coding start? |

---

### 7.13 Sustainability / Carbon Proxy

**Research question:** What is the environmental footprint of this AI-assisted coding session?

| Dimension | Data Source | Notes |
|-----------|-------------|-------|
| AI compute energy proxy | Kiro credits consumed (63–156 credits per session) | Credits as proxy for GPU-compute time; Anthropic's Claude API energy cost estimates available |
| Commute carbon | Pre-survey commute mode + distance | Car vs public transport vs cycling; multiply by CO₂/km estimates |
| Cloud VM energy | AWS EC2 instance-hours (t3.medium in eu-west-2) | ~3.5W TDP; eu-west-2 carbon intensity ~0.225 kg CO₂/kWh |
| Aggregate | (AI compute + VM) vs commute avoided | AI-assisted session from home vs commuting to office |

---

### 7.14 Summary: Key Comparisons Enabled

| Comparison | Participants | Data Available |
|------------|-------------|----------------|
| Autopilot vs Supervised mode | ai-02 vs rest | Credits, LLM requests, file changes, checkpoint results, screen recordings |
| Opus 4.8 vs auto model | ai-02 vs rest | Credits × 2.2 multiplier; output quality (checkpoint results) |
| Short sessions vs long sessions | ai-06/ai-05 vs ai-01/ai-03 | Code output, checkpoints, credits — efficiency per minute |
| Python-native vs non-Python participants | ai-03–06 vs ai-01 (Go/Elixir), ai-02 (Java) | Task performance, prompt patterns, error rates |
| High-DevOps-maturity vs low | ai-03 (5/5) vs ai-02/ai-04/ai-05/ai-06 (1/5) | AI usage strategy, error patterns, task performance |
| Single long context vs multi-session | ai-01/ai-04–06 (1 session) vs ai-02 (4), ai-03 (2) | Context management, credit efficiency |

