#!/usr/bin/env python3
"""Summarise automatic GENIUS evidence against stakeholder questions.

This report deliberately separates log-supported facts from questions that need
targeted video or manual qualitative review.
"""

import json
from datetime import datetime
from pathlib import Path

PARTICIPANTS = [f"ai-{number:02d}" for number in range(1, 7)]
ROOT = Path("/Users/k2589922/Documents/Projects/GENIUS_experiment_data")
OUTPUT = Path(__file__).parent / "output"


def load(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def checkpoint(participant):
    data = load(ROOT / participant / "task_checkpoints" / "Task1_cp3.json", {})
    stats = data.get("test_statistics", {})
    return {"success": data.get("success"), "return_code": data.get("return_code"),
            "duration_seconds": data.get("duration_seconds"),
            "tests_run": stats.get("tests_run"), "failures": stats.get("failures"),
            "errors": stats.get("errors")}


def metrics(participant):
    data = load(ROOT / participant / "kiro" / "kiro_metrics.json", {})
    analytics = load(ROOT / participant / "kiro" / "kiro_analytics.json", {})
    source = data.get("chat_api") or data.get("data") or {}
    sessions = sorted((ROOT / participant / "kiro" / "sessions").glob("*.json"))
    modes = sorted({load(path, {}).get("autonomyMode") for path in sessions if load(path, {}).get("autonomyMode")})
    return {"requests": source.get("request_count", source.get("kiro_requests")),
            "credits_used": source.get("credits_used", source.get("kiro_credits_used")),
            "estimated_input_tokens": source.get("estimated_input_tokens", source.get("kiro_estimated_input_tokens")),
            "estimated_output_tokens": source.get("estimated_output_tokens", source.get("kiro_estimated_output_tokens")),
            "request_models": source.get("request_models", {}), "autonomy_modes": modes,
            "session_files": len(sessions),
            "analytics_credits_used_session": analytics.get("credits", {}).get("credits_used_session"),
            "analytics_prompt_tokens": analytics.get("tokens", {}).get("total_prompt_tokens")}


def participant_row(participant):
    log = load(OUTPUT / f"{participant}_log_events.json", {})
    events = log.get("events", [])
    commands = [event for event in events if event.get("event_category") == "terminal_command"]
    scalability = [event for event in commands if "test_scalability" in event.get("command", "")]
    outcomes = {kind: sum(event.get("outcome") == kind for event in commands)
                for kind in ("pass", "fail", "timeout", "interrupted")}
    return {"participant": participant, "event_count": len(events),
            "participant_messages": sum(event.get("event_category") == "participant_message" for event in events),
            "agent_triggers": sum(event.get("event_category") == "agent_trigger" for event in events),
            "terminal_outcomes": outcomes, "scalability_commands": [
                {key: event.get(key) for key in ("wall_time", "command", "outcome", "duration_ms", "initiator")}
                for event in scalability],
            "task1_cp3": checkpoint(participant), "kiro_metrics": metrics(participant)}


def main():
    rows = [participant_row(participant) for participant in PARTICIPANTS]
    ai02 = next(row for row in rows if row["participant"] == "ai-02")
    ai06 = next(row for row in rows if row["participant"] == "ai-06")
    questions = [
        {"question": "Did participants attempt and pass the scalability checkpoint?",
         "status": "answered_automatically",
         "evidence": "Post-session Task1_cp3 records provide pass/fail, duration, test count, failures, and errors for all six participants."},
        {"question": "Did AI06 run the scalability command during the recorded session?",
         "status": "answered_automatically",
         "evidence": f"AI06 has {len(ai06['scalability_commands'])} logged terminal command(s) containing test_scalability. "
                     "This answers command occurrence only; it does not establish noticing or understanding."},
        {"question": "What happened after failures, timeouts, or interruptions?",
         "status": "partly_answered",
         "evidence": "Logs provide command outcomes, timestamps, initiators, subsequent commands, and later messages; they do not show visible inspection, diagnosis, or attention."},
        {"question": "How did AI-use intensity and configuration vary?",
         "status": "answered_automatically",
         "evidence": "Kiro metrics provide request counts, estimated tokens, credits, request-model fields, and recorded autonomy modes where available."},
        {"question": "Does AI02's supervised/stronger-model/high-usage pattern explain its failed scalability outcome?",
         "status": "partly_answered",
         "evidence": f"AI02 metrics record modes {ai02['kiro_metrics']['autonomy_modes']}, models {list(ai02['kiro_metrics']['request_models'])}, and Task1_cp3 outcome {ai02['task1_cp3']['success']}. The small, confounded sample does not support a causal explanation."},
        {"question": "What message categories or prompting strategies were used?",
         "status": "partly_answered",
         "evidence": "The automatic baseline retains timestamped message text and agent types. It does not assign qualitative implement/debug/explain/refactor/confirm labels without a separately validated coding method."},
        {"question": "Did participants notice failures, review approvals, manually intervene, or change strategy?",
         "status": "requires_targeted_video_manual_review",
         "evidence": "These are behavioural/interpretive questions. They cannot be inferred reliably from commands, messages, or outcomes alone."},
    ]
    report = {"generated_at": datetime.now().isoformat(timespec="seconds"),
              "scope": "automatic log-derived baseline; no behavioural video inference", "participants": rows,
              "stakeholder_questions": questions,
              "limits": ["Estimated token values are not complete tool-call token counts.",
                         "AI01's recovered session spans a rotated chat log; its current Chat_API-derived request and credit totals are partial and are not comparable to the other rows.",
                         "Absence of a logged command is not evidence of understanding, intent, or attention.",
                         "No causal claim is made from six participants with differing models, autonomy modes, and histories."]}
    (OUTPUT / "stakeholder_evidence_report.json").write_text(json.dumps(report, indent=2) + "\n")
    lines = ["# Stakeholder Evidence Report", "", "## Scope", "",
             "Automatic log-derived evidence only. No participant behaviour is inferred from video.", "",
             "## Per-participant automatic evidence", "",
             "| Participant | Events | Messages | Agent triggers | Scalability commands | Task1_cp3 | Requests | Credits | Autonomy |",
             "|---|---:|---:|---:|---:|---|---:|---:|---|"]
    for row in rows:
        metric, cp = row["kiro_metrics"], row["task1_cp3"]
        lines.append(f"| {row['participant']} | {row['event_count']} | {row['participant_messages']} | {row['agent_triggers']} | {len(row['scalability_commands'])} | {'pass' if cp['success'] else 'fail'} | {metric['requests'] or '—'} | {metric['credits_used'] or '—'} | {', '.join(metric['autonomy_modes']) or '—'} |")
    lines += ["", "## Stakeholder questions", ""]
    for item in questions:
        lines += [f"### {item['question']}", "", f"**{item['status']}** — {item['evidence']}", ""]
    lines += ["## Limits", ""] + [f"- {item}" for item in report["limits"]]
    (OUTPUT / "stakeholder_evidence_report.md").write_text("\n".join(lines) + "\n")
    print("Wrote stakeholder_evidence_report.json and stakeholder_evidence_report.md")


if __name__ == "__main__":
    main()
