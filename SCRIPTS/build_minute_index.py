#!/usr/bin/env python3
"""Build a per-minute session index by reusing logs, video survey, and episodes.

This is NOT full behavioural video coding. Each minute gets:
  - log events that fall in that window (multiple allowed)
  - screen activity proxy from 5s survey change scores
  - links to existing behavioural_episode annotations
  - a review hint: log_only | coded_episode | consider_video_review

Usage:
    python3 SCRIPTS/build_minute_index.py --participant ai-01
"""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

OUTPUT = Path(__file__).parent / "output"
SESSION_DATE = "2026-06-09"

SUMMARY_CATEGORIES = {
    "participant_message", "terminal_command", "file_write", "agent_trigger",
}


def load_json(path):
    if path.exists():
        return json.loads(path.read_text())
    return None


def wall_from_sec(video_start_wall, sec):
    base = datetime.strptime(f"{SESSION_DATE} {video_start_wall}", "%Y-%m-%d %H:%M:%S")
    return (base + timedelta(seconds=float(sec))).strftime("%H:%M:%S")


def event_brief(event):
    cat = event.get("event_category", "?")
    if cat == "participant_message":
        text = (event.get("text") or "")[:80]
        return f"message: {text}"
    if cat == "terminal_command":
        cmd = (event.get("command") or "")[:60]
        outcome = event.get("outcome") or event.get("exit_code")
        return f"terminal ({outcome}): {cmd}"
    if cat == "file_write":
        return f"write: {event.get('file_name') or event.get('file_path', '?')}"
    if cat == "agent_trigger":
        return f"agent: {event.get('agent_type', 'trigger')}"
    return cat


def minute_activity(survey_samples, start, end):
    in_window = [s for s in survey_samples if start <= s["video_sec"] < end]
    if not in_window:
        return {"max_change_score": None, "mean_change_score": None, "samples": 0}
    scores = [s.get("change_score") or 0 for s in in_window]
    return {
        "max_change_score": round(max(scores), 4),
        "mean_change_score": round(sum(scores) / len(scores), 4),
        "samples": len(in_window),
    }


def overlapping_episodes(episodes, start, end):
    hits = []
    for ep in episodes:
        es = ep.get("timeline_sec_start", ep.get("video_sec_start", 0))
        ee = ep.get("timeline_sec_end", ep.get("video_sec_end", es))
        if es < end and ee > start:
            hits.append({
                "id": ep.get("id"),
                "description": ep.get("event_description"),
                "construct": ep.get("construct"),
            })
    return hits


def review_hint(start, minute_events, episodes, activity, video_end_sec):
    if start >= video_end_sec:
        return "off_video"
    if episodes:
        return "coded_episode"
    interesting = [
        e for e in minute_events
        if (
            e.get("event_category") == "terminal_command"
            and e.get("outcome") in {"fail", "timeout", "interrupted"}
        )
        or e.get("event_category") == "participant_message"
    ]
    high_change = (activity.get("max_change_score") or 0) >= 0.05
    if interesting and high_change:
        return "consider_video_review"
    if minute_events:
        return "log_only"
    if high_change:
        return "low_log_high_activity"
    return "quiet"


def build_minute_index(participant):
    log_path = OUTPUT / f"{participant}_log_events.json"
    ann_path = OUTPUT / f"{participant}_annotation.json"
    survey_path = OUTPUT / f"{participant}_video_survey.json"

    log_data = load_json(log_path)
    if not log_data:
        raise SystemExit(f"Missing {log_path}")

    ann_data = load_json(ann_path) or {}
    survey_data = load_json(survey_path) or {"samples": []}

    video_start = ann_data.get("video_start_wall") or log_data.get("video_start_wall", "09:00:00")
    video_duration = survey_data.get("duration_sec")
    if not video_duration:
        video_duration = max(
            (e.get("video_sec", 0) for e in log_data.get("events", [])),
            default=0,
        )
    video_duration = min(float(video_duration), max(
        (e.get("video_sec", 0) for e in log_data.get("events", [])),
        default=float(video_duration),
    ))

    events = [e for e in log_data.get("events", []) if not e.get("pre_video")]
    episodes = [
        e for e in ann_data.get("events", [])
        if e.get("event_category") == "behavioural_episode"
    ]
    survey_samples = survey_data.get("samples", [])

    total_minutes = int(video_duration // 60) + 1
    minutes = []

    for m in range(total_minutes):
        start = m * 60
        end = start + 60
        minute_events = [
            e for e in events
            if start <= e.get("video_sec", -1) < end
        ]
        summary_events = [e for e in minute_events if e.get("event_category") in SUMMARY_CATEGORIES]
        activity = minute_activity(survey_samples, start, end)
        ep_overlap = overlapping_episodes(episodes, start, end)
        hint = review_hint(start, summary_events, ep_overlap, activity, video_duration)

        minutes.append({
            "minute_index": m,
            "video_sec_start": start,
            "video_sec_end": end,
            "wall_time_start": wall_from_sec(video_start, start),
            "wall_time_end": wall_from_sec(video_start, end),
            "event_count": len(minute_events),
            "summary_event_count": len(summary_events),
            "events": [
                {
                    "id": e.get("id"),
                    "category": e.get("event_category"),
                    "brief": event_brief(e),
                }
                for e in summary_events
            ],
            "activity": activity,
            "behavioural_episodes": ep_overlap,
            "review_hint": hint,
        })

    out = {
        "participant": participant,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "method": "log_derived_minute_index_v1",
        "notes": (
            "Per-minute buckets aggregate log events. Multiple events per minute are listed. "
            "behavioural_episode entries reuse ai-XX_annotation.json. "
            "consider_video_review = candidate for human episode coding, not auto-coded behaviour."
        ),
        "video_duration_sec": round(video_duration, 1),
        "video_start_wall": video_start,
        "total_minutes": total_minutes,
        "stats": {
            "minutes_with_events": sum(1 for row in minutes if row["event_count"]),
            "minutes_coded_episode": sum(1 for row in minutes if row["review_hint"] == "coded_episode"),
            "minutes_consider_video_review": sum(1 for row in minutes if row["review_hint"] == "consider_video_review"),
            "minutes_quiet": sum(1 for row in minutes if row["review_hint"] == "quiet"),
        },
        "minutes": minutes,
    }

    out_path = OUTPUT / f"{participant}_minute_index.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(f"Written: {out_path}")
    print(f"  {total_minutes} minutes, {out['stats']['minutes_with_events']} with log events")
    print(f"  {out['stats']['minutes_coded_episode']} overlap coded episodes")
    print(f"  {out['stats']['minutes_consider_video_review']} candidates for extra video review")
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--participant", default="ai-01")
    args = parser.parse_args()
    build_minute_index(args.participant)


if __name__ == "__main__":
    main()
