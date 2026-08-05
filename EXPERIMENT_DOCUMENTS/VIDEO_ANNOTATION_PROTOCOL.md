# GENIUS Video Annotation Protocol

## Purpose

Logs are the factual activity backbone. Video is used only when it adds
material evidence about participant behaviour around AI use. The unit of final
coding is a **behavioural episode**, not a UI state or a duplicated log event.

## Per-participant workflow

1. **Validate time alignment.** Before linking video to logs, verify at least
   three independently identifiable anchors. Record a validated offset or
   piecewise mapping; leave log links out when the mapping is uncertain.
2. **Read the log timeline.** Generate `ai-XX_log_events.json` and inspect the
   timeline before opening the recording. Identify task/checkpoint boundaries,
   messages, failures, timeouts, interruptions, and agent-activity clusters.
3. **Form a behavioural map.** Divide the session into log-derived phases.
   For each phase, state the missing
   behavioural evidence: visible approval/dwell, response to a failure, manual
   edit, navigation, or context preceding a consequential message. Discard
   candidates where logs already answer the research question.
   Record `not_selected` where no useful question remains.
4. **Run sparse reconnaissance.** Generate five-second survey frames and
   change scores with `python SCRIPTS/annotate_video.py --participant ai-XX`.
   Review one quiet frame per minute. The survey and review queue are navigation
   artefacts, not final annotations.
5. **Inspect only viable episodes densely.** Begin at one-second frames;
   tighten only approval/click transitions that require precise dwell time.
   Required windows are approval candidates, failures/timeouts/interruptions,
   consequential messages, suspected manual edits, and checkpoint windows with
   an unresolved behavioural question.
6. **Decide each candidate.** Mark each `final_episode`, `not_useful`, or
   `ambiguous`. A final episode must state the research question, log anchors,
   video contribution, observable sequence, evidence limits, time bounds, and
   confidence. The video contribution may be log-linked, but must add material
   behavioural evidence beyond the logs.
7. **Add final events.** Add only `behavioural_episode` records to
   `ai-XX_annotation.json` and regenerate the timeline.
   Regenerate the timeline after each batch. Do not add generic screen-state,
   routine Kiro-working, or duplicated terminal/task events.
8. **Quality-check.** Recheck every critical event; independently recheck 10%
   of quiet one-minute samples and 20% of final critical annotations. Mark
   ambiguity rather than inferring intent, attention, comprehension, or trust.

## What video contributes

| Research question | Video evidence required |
|---|---|
| Trust calibration | Visible approval prompt, controls, transition, dwell bounds, visible review/scrolling |
| Human oversight | Participant-visible failure/result and directly observable action after it |
| Manual intervention | Visible edit/navigation with no matching Kiro `WriteFile` evidence |
| Prompt/strategy context | Visible typing/sending or verified reading/scrolling sequence before a consequential message |

## Cost and scope

Target effort is **4–8 hours for a two-hour recording** and **1.5–3 hours for
ai-01's 35.5-minute recording**. Continuous or generic state annotation is out
of scope: it costs 20+ hours per two-hour video and mostly duplicates logs.

For cross-participant comparison, complete the targeted workflow for every
participant. Reserve any richer, fine-grained coding for a purposive subset
chosen to represent contrasting workflows or failure modes.

## Final-event standard

Every final episode must answer a written research question and identify a
concrete contribution that the logs cannot supply (for example, a draft-to-send
sequence, visible review before an approval, or direct manual intervention).

Never render copied messages, commands, terminal results, task states, file
writes, generic Kiro-working states, or a static screen as final episodes.
Keep reconnaissance, rejected candidates, and unresolved ambiguity in
`ai-XX_review_queue.json`, never in the Video Annotations track.

## Critical Incident Codebook (meeting categories A–E)

Final episodes are coded against the research questions from the UK catch-ups.
Use the JSON fields below; do not duplicate log events as episodes.

### Category mapping

| Meeting category | What to capture | Typical `construct` values |
|---|---|---|
| **A — Timeline / task progress** | Current task or checkpoint; pass/fail attempt; retry, abandonment, idle | `checkpoint_attempt`, `task_abandonment`, `idle_period` |
| **B — AI-interaction behaviour** | Prompt purpose, model/mode if visible, tool use, accept/modify/reject | `prompt_strategy`, `approval_dwell`, `delegation` |
| **C — Human development behaviour** | Manual edit, test run, error inspection, window switching | `manual_intervention`, `test_execution`, `debugging` |
| **D — Context provided to AI** | Prompt specificity, error evidence, code locations cited | `context_quality`, `diagnostic_evidence` |
| **E — Critical incidents** | First major error, failed checkpoint, recovery, breakthrough, belief mismatch | `failure_awareness`, `belief_mismatch`, `strategy_change`, `recovery_attempt` |

### Required JSON fields per final episode

| Field | Purpose |
|---|---|
| `construct` | Category E incident type (see table above) |
| `research_question` | Which team RQ or sub-question this episode answers |
| `log_anchors` | `[{"log_event_id": N, "relationship": "…"}]` — links to `ai-XX_log_events.json` |
| `video_contribution` | Material evidence logs cannot supply (typing, terminal reading, dwell) |
| `analysis` | Checkpoint link, pass/fail, hypothesis, who declared abandonment |
| `wall_time_start` / `wall_time_end` | Study-clock wall times |
| `confidence` | `high`, `medium`, or `low` |
| `evidence_limits` | What cannot be inferred (intent, comprehension, trust) |

### Coding rules

1. **Log-first:** if logs fully answer the RQ, do not create a video episode.
2. **One episode per critical incident** — not continuous screen states.
3. **Always anchor to log ids** so timeline sync uses `resolve_ann_timing()`.
4. Label proxy measures (requests, credits, char counts) as estimates in write-ups, not in episode JSON.
