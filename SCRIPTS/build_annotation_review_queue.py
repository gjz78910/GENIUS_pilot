#!/usr/bin/env python3
"""Build a cost-controlled human review queue for GENIUS screen recordings.

It never changes the primary annotation JSON.  The generated queue separates
log-derived evidence from video questions, and uses local AVFoundation frame
extraction rather than an API-based frame annotator.
"""

import argparse
import html
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE_DATA = Path("/Users/k2589922/Documents/Projects/GENIUS_experiment_data")
OUTPUT = Path(__file__).parent / "output"
CHECKPOINTS = {
    "routing": "test_routing_checkpoint_a",
    "nearest_neighbour": "TestNearestNeighborTSP",
    "two_opt": "TestTwoOptImprove",
    "matching": "tests.test_matching",
    "report": "test_report_correctness",
    "scalability": "tests.performance.test_scalability",
}


def clip(start, end, duration):
    return round(max(0.0, start), 3), round(min(duration, end), 3)


def matching_indices(events, predicate):
    return [index for index, event in enumerate(events) if predicate(event)]


def sparse_evidence(survey, start, end):
    samples = [sample for sample in survey["samples"]
               if start <= sample["video_sec"] <= end]
    if not samples:
        return []
    anchors = [min(samples, key=lambda item: abs(item["video_sec"] - point))
               for point in (start, (start + end) / 2, end)]
    highest_change = max(samples, key=lambda item: item["change_score"])
    selected = {item["frame_file"]: item for item in anchors + [highest_change]}
    return [{"video_sec": item["video_sec"], "frame_file": item["frame_file"],
             "change_score": item["change_score"]}
            for item in sorted(selected.values(), key=lambda item: item["video_sec"])]


def build_behavioural_map(events, survey, duration):
    """Create a small, research-led review plan instead of one task per log event."""
    typed = lambda event: event.get("event_category") == "terminal_command" and event.get("initiator") == "participant_typed"
    timeout = lambda event: event.get("event_category") == "terminal_command" and event.get("outcome") == "timeout"
    interrupted = lambda event: event.get("event_category") == "terminal_command" and event.get("outcome") == "interrupted"
    failed = lambda event: event.get("event_category") == "terminal_command" and terminal_status(event) == "fail"
    message = lambda event: event.get("event_category") == "participant_message"

    map_rows = [
        {
            "id": "phase-routing-nn",
            "range_sec": [0, 643],
            "log_anchor_ids": matching_indices(events, lambda event: 0 <= event.get("video_sec", -1) <= 643),
            "log_summary": "Routing and nearest-neighbour implementation, test execution, and early approvals.",
            "research_question": None,
            "relevance_decision": "not_selected",
            "reason": "The log timeline already explains routine task progression; inspect only if sparse review finds direct manual intervention.",
        },
        {
            "id": "phase-two-opt-recovery",
            "range_sec": [610, 1020],
            "log_anchor_ids": matching_indices(events, lambda event: 610 <= event.get("video_sec", -1) <= 1020),
            "log_summary": "A timeout is followed by a cluster of participant-typed targeted tests and commands.",
            "research_question": "Does the recording show review, diagnosis, or manual recovery behaviour between the timeout and the later targeted commands?",
            "relevance_decision": "selected",
        },
        {
            "id": "phase-checkpoint-benchmark",
            "range_sec": [1061, 1460],
            "log_anchor_ids": matching_indices(events, lambda event: 1061 <= event.get("video_sec", -1) <= 1460),
            "log_summary": "Routing checkpoint and benchmark failures, followed by Kiro writes and further tests.",
            "research_question": "After failed checks, is result inspection, task-checking, intervention, or a visible transition away from the problem shown?",
            "relevance_decision": "selected",
        },
        {
            "id": "phase-matching-strategy",
            "range_sec": [1511, 2098],
            "log_anchor_ids": matching_indices(events, lambda event: 1511 <= event.get("video_sec", -1) <= 2098),
            "log_summary": "Participant reports failures, discusses refactoring, then moves into matching specification work.",
            "research_question": "Is a strategy-formulation sequence visibly developed before or while the participant re-engages Kiro?",
            "relevance_decision": "selected",
        },
    ]

    candidate_specs = [
        ("episode-001", "failure_recovery", 680, 1035, "phase-two-opt-recovery",
         "Does the recording show review, diagnosis, or manual recovery behaviour after the timeout?",
         matching_indices(events, lambda event: (timeout(event) and 680 <= event.get("video_sec", -1) <= 1035) or
                         (typed(event) and 800 <= event.get("video_sec", -1) <= 1035))),
        ("episode-002", "checkpoint_response", 1095, 1230, "phase-checkpoint-benchmark",
         "After the routing checkpoint failure, is result inspection, task-checking, or intervention visible?",
         matching_indices(events, lambda event: failed(event) and 1095 <= event.get("video_sec", -1) <= 1230) +
         matching_indices(events, lambda event: typed(event) and 1095 <= event.get("video_sec", -1) <= 1230)),
        ("episode-003", "failure_response", 1345, 1465, "phase-checkpoint-benchmark",
         "After the benchmark failure, is a visible response or transition away from the problem shown?",
         matching_indices(events, lambda event: failed(event) and 1345 <= event.get("video_sec", -1) <= 1465)),
        ("episode-004", "strategy_formulation", 1480, min(2010, duration), "phase-matching-strategy",
         "Is a strategy-formulation sequence visible before or while the participant re-engages Kiro?",
         matching_indices(events, lambda event: message(event) and 1480 <= event.get("video_sec", -1) <= 2010)),
    ]
    candidates = []
    for candidate_id, construct, start, end, phase_id, question, anchors in candidate_specs:
        candidates.append({
            "id": candidate_id,
            "construct": construct,
            "phase_id": phase_id,
            "start_sec": start,
            "end_sec": end,
            "research_question": question,
            "log_anchor_ids": sorted(set(anchors)),
            "sparse_evidence": sparse_evidence(survey, start, end),
            "review_status": "pending_sparse_review",
            "decision": None,
            "decision_reason": None,
            "final_event_id": None,
        })
    return map_rows, candidates


def terminal_status(event):
    if event.get("outcome") in {"timeout", "interrupted"}:
        return event["outcome"]
    parsed = (event.get("test_result") or {}).get("outcome")
    if parsed in {"pass", "fail", "import_error"}:
        return "fail" if parsed in {"fail", "import_error"} else "pass"
    return event.get("outcome", "unknown")


def build_checkpoint_coding(events, participant):
    records = []
    for checkpoint_id, needle in CHECKPOINTS.items():
        attempts = [event for event in events if event.get("event_category") == "terminal_command"
                    and needle in event.get("command", "")]
        records.append({
            "checkpoint_id": checkpoint_id,
            "checkpoint_test": needle,
            "attempted": bool(attempts),
            "log_attempts": [{
                "video_sec": event.get("video_sec"),
                "wall_time": event.get("wall_time"),
                "status": terminal_status(event),
                "command": event.get("command"),
                "duration_ms": event.get("duration_ms"),
            } for event in attempts],
            "video_review": {
                "participant_noticed_result": "not_reviewed",
                "dwell_on_result_sec": None,
                "understood_failure": "not_inferred",
                "action_after_result": "not_reviewed",
                "manual_edits_observed": "not_reviewed",
                "notes": "Complete only from reviewed video evidence.",
            },
        })
    return {
        "participant": participant,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": "derived_from_terminal_logs",
        "checkpoints": records,
    }


def render_report(participant, queue, survey_path, frame_root):
    rows = []
    for candidate in queue["episode_candidates"]:
        thumbs = []
        for sample in candidate["sparse_evidence"]:
            relative = frame_root / sample["frame_file"]
            thumbs.append(
                f'<figure><img src="{html.escape(str(relative))}" loading="lazy">'
                f'<figcaption>t={sample["video_sec"]:.0f}s; change={sample["change_score"]:.3f}</figcaption></figure>'
            )
        rows.append(
            "<section><h2>%s · %ss–%ss · %s</h2><p><b>Question:</b> %s</p>"
            "<p><b>Log anchors:</b> %s · <b>Review:</b> %s</p><div class=thumbs>%s</div></section>" % (
                candidate["id"], candidate["start_sec"], candidate["end_sec"], candidate["construct"],
                html.escape(candidate["research_question"]),
                html.escape(", ".join(map(str, candidate["log_anchor_ids"])) or "none"),
                html.escape(candidate["review_status"]),
                "".join(thumbs),
            )
        )
    return """<!doctype html><meta charset=utf-8><title>GENIUS review queue</title>
<style>body{font:15px system-ui;margin:24px;color:#18212b}section{border:1px solid #ccd5df;padding:12px;margin:14px 0;border-radius:8px}h1{margin-bottom:4px}.thumbs{display:flex;gap:12px;flex-wrap:wrap}figure{margin:0}img{width:300px;border:1px solid #aab6c4}figcaption{font-size:12px;color:#536170}</style>
<h1>GENIUS """ + html.escape(participant) + """: video review queue</h1>
<p>Review research episodes, not individual log events. Add a final item only when video adds material behavioural evidence beyond the logs.</p>""" + "\n".join(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--participant", required=True)
    parser.add_argument("--interval", type=float, default=5.0, help="Survey frame interval in seconds")
    parser.add_argument("--start", type=float, help="Optional dense-window start second")
    parser.add_argument("--end", type=float, help="Optional dense-window end second")
    parser.add_argument("--change-threshold", type=float, default=0.055)
    parser.add_argument("--max-window", type=float, default=150,
                        help="Maximum seconds in one review task.")
    parser.add_argument("--skip-survey", action="store_true", help="Build from a previously generated survey JSON")
    args = parser.parse_args()
    if (args.start is None) != (args.end is None):
        raise SystemExit("Use --start and --end together for a dense review window.")

    log_path = OUTPUT / f"{args.participant}_log_events.json"
    if not log_path.exists():
        raise SystemExit(f"Missing log backbone: {log_path}. Run extract_log_events.py first.")
    log_data = json.loads(log_path.read_text())
    events = log_data.get("events", [])
    video_dir = BASE_DATA / args.participant / "videos"
    videos = sorted(video_dir.glob("*.mp4"), key=lambda path: path.stat().st_size, reverse=True)
    if not videos:
        raise SystemExit(f"No MP4 found in {video_dir}")

    is_window = args.start is not None
    suffix = (f"_{args.start:g}_{args.end:g}" if is_window else "")
    frame_dir = OUTPUT / (f"{args.participant}_review_frames/window{suffix}" if is_window
                          else f"{args.participant}_review_frames")
    survey_path = OUTPUT / f"{args.participant}_video_survey{suffix}.json"
    if not args.skip_survey:
        # Reconnaissance is deliberately cheap (default 5 seconds); a bounded
        # review window is the separate, one-second evidence pass.
        extraction_interval = 1.0 if is_window else args.interval
        command = ["swift", str(Path(__file__).with_name("video_survey.swift")), str(videos[0]), str(frame_dir), str(extraction_interval)]
        if is_window:
            command += [str(args.start), str(args.end)]
        result = subprocess.run(command, check=True, text=True, capture_output=True)
        survey_path.write_text(result.stdout)
        if result.stderr.strip():
            print(result.stderr, file=sys.stderr)
    if not survey_path.exists():
        raise SystemExit(f"Missing survey: {survey_path}; rerun without --skip-survey.")
    survey = json.loads(survey_path.read_text())
    duration = survey["duration_sec"]

    # Dense-window extraction is an inspection artefact only: do not rebuild
    # the full queue or checkpoint file from a partial sample.
    if is_window:
        print(f"Dense survey: {survey_path} ({len(survey['samples'])} frames)")
        return

    behavioural_map, episode_candidates = build_behavioural_map(events, survey, duration)
    # A queue is an audit record, not a disposable suggestion list. Preserve a
    # completed reviewer decision if the same candidate is rebuilt from logs.
    queue_path = OUTPUT / f"{args.participant}_review_queue.json"
    prior_queue = json.loads(queue_path.read_text()) if queue_path.exists() else {}
    prior_candidates = {item.get("id"): item for item in prior_queue.get("episode_candidates", [])}
    for candidate in episode_candidates:
        prior = prior_candidates.get(candidate["id"], {})
        if prior.get("decision") in {"final_episode", "not_useful", "ambiguous"}:
            for key in ("review_status", "decision", "decision_reason", "final_event_id"):
                candidate[key] = prior.get(key)
    quiet_checks = [{
        "id": f"quiet-{second:04d}", "video_sec": second, "decision": "quiet",
        "review_status": "pending", "annotation_result": None,
    } for second in range(0, int(duration) + 1, 60)]
    prior_quiet = {item.get("id"): item for item in prior_queue.get("quiet_state_checks", [])}
    for check in quiet_checks:
        prior = prior_quiet.get(check["id"], {})
        if prior.get("review_status") == "qa_rechecked":
            check["review_status"] = "qa_rechecked"
            check["annotation_result"] = prior.get("annotation_result")

    existing = json.loads((OUTPUT / f"{args.participant}_annotation.json").read_text()) if (OUTPUT / f"{args.participant}_annotation.json").exists() else {}
    queue = {
        "participant": args.participant,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "protocol": "research_led_episode_review_v2",
        "video": {"path": str(videos[0]), "duration_sec": duration},
        "survey": survey,
        "time_alignment": prior_queue.get("time_alignment", {
            "status": "requires_validation",
            "method": "Confirm at least three visible, independently identifiable anchors before linking a final episode to logs.",
            "anchors": [],
            "linking_rule": "Do not add log anchors to a final episode while alignment is uncertain.",
        }),
        "behavioural_map": behavioural_map,
        "episode_candidates": episode_candidates,
        "quiet_state_checks": quiet_checks,
        "existing_video_annotation_ranges": [{
            "start_sec": event.get("video_sec_start"), "end_sec": event.get("video_sec_end"),
            "review_status": event.get("review_status", "unreviewed_existing_annotation")
        } for event in existing.get("events", [])],
        "quality_assurance": prior_queue.get("quality_assurance", {
            "quiet_sample_fraction": 0.10, "critical_sample_fraction": 0.20, "status": "pending"
        }),
    }
    queue_path.write_text(json.dumps(queue, indent=2))
    checkpoint_path = OUTPUT / f"{args.participant}_checkpoint_coding.json"
    checkpoint_path.write_text(json.dumps(build_checkpoint_coding(events, args.participant), indent=2))
    report_path = OUTPUT / f"{args.participant}_review_queue.html"
    report_path.write_text(render_report(args.participant, queue, survey_path, Path(frame_dir.name)))
    print(f"Survey: {survey_path} ({len(survey['samples'])} frames)")
    print(f"Review queue: {queue_path} ({len(episode_candidates)} research episodes, {len(quiet_checks)} quiet checks)")
    print(f"Checkpoint coding: {checkpoint_path}")
    print(f"Contact-sheet report: {report_path}")


if __name__ == "__main__":
    main()
