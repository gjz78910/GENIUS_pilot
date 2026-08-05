#!/usr/bin/env python3
"""
generate_timeline.py — GENIUS interactive session timeline.

Usage:
    python SCRIPTS/generate_timeline.py                    # ai-01 (default)
    python SCRIPTS/generate_timeline.py --participant ai-03

Reads:
    SCRIPTS/output/ai-XX_log_events.json   (required)
    SCRIPTS/output/ai-XX_annotation.json   (optional)
    SCRIPTS/lib/vis-timeline.min.js        (required — already downloaded)
    SCRIPTS/lib/vis-timeline.min.css

Outputs:
    SCRIPTS/output/ai-XX_timeline.html  (self-contained, open in Safari or any browser)
"""

import argparse
import json
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

SESSION_DATE    = "2026-06-09"
EXPERIMENT_DATA = Path("/Users/k2589922/Documents/Projects/GENIUS_experiment_data")
ALL_PARTICIPANTS = ["ai-01", "ai-02", "ai-03", "ai-04", "ai-05", "ai-06"]

# Event colours — deliberate dark-lab palette
C = {
    "terminal_pass":        "#3FB950",
    "terminal_fail":        "#F85149",
    "terminal_timeout":     "#D29922",
    "terminal_interrupted": "#E3B341",
    "participant_message":  "#388BFD",
    "reading_behaviour":    "#BC8CFF",
    "approval_decision":    "#FF7B72",
    "manual_navigation":    "#A371F7",
    "behavioural_episode": "#F0883E",
    "task_complete":        "#39D353",
    "code_edit_accepted":   "#2EA043",
    "kiro_action":          "#A5D6FF",
    "kiro_response":        "#79C0FF",
    "agent_trigger":        "#79C0FF",
    "file_write":           "#D2A8FF",
    "command_result":       "#56D364",
    "video_state":          "#A8C7FA",
    "pre_video":            "#484F58",
    "not_attempted":        "#484F58",
}

GROUPS = [
    {"id": "video_coverage", "content": "Video Coverage", "order": 0},
    {"id": "video_annotations", "content": "Video Annotations", "order": 1},
    {"id": "tasks",       "content": "Tasks",        "order": 2},
    {"id": "participant", "content": "Participant",  "order": 3},
    {"id": "kiro",        "content": "Kiro Agent",   "order": 4},
    {"id": "files",       "content": "File Writes",  "order": 5},
    {"id": "terminal",    "content": "Terminal",     "order": 6},
    {"id": "session_lifecycle", "content": "Session Lifecycle", "order": 7},
]

# ── Helpers ────────────────────────────────────────────────────────────────────

def parse_ts(s):
    s = s.strip()
    if len(s) <= 8:
        return datetime.strptime(SESSION_DATE + " " + s, "%Y-%m-%d %H:%M:%S")
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        return datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S")

def wall_dt(w):
    return datetime.strptime(SESSION_DATE + " " + w, "%Y-%m-%d %H:%M:%S")

def sec_dt(sec, sw):
    return wall_dt(sw) + timedelta(seconds=float(sec))

def jsdt(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + "%03d" % (dt.microsecond // 1000)

def media_duration_seconds(path):
    """Read macOS Spotlight media duration without decoding the recording."""
    try:
        value = subprocess.check_output(
            ["mdls", "-name", "kMDItemDurationSeconds", "-raw", str(path)], text=True
        ).strip()
        return float(value) if value not in {"(null)", ""} else 0.0
    except (OSError, subprocess.CalledProcessError, ValueError):
        return 0.0

def tip(e):
    skip = {"output_text"}
    out = []
    for k, v in e.items():
        if k in skip: continue
        sv = str(v)
        if len(sv) > 100: sv = sv[:100] + "…"
        out.append("<b>%s:</b> %s" % (k, sv))
    return "<br>".join(out)

def make(iid, label, s, e, group, color, raw, src, pre=False):
    # vis-timeline points are anchored on a group boundary, which makes a
    # timestamp look as if it belongs to two tracks.  Use a content-less box
    # for instantaneous events: it participates in the normal stack layout
    # and is then rendered as one circular marker inside its own track.
    instantaneous = not e
    item = {
        "id": iid, "content": label, "start": jsdt(s),
        "group": group,
        "type": "range" if e else "box",
        "style": "background:%s;border-color:%s;color:#0d1117;font-size:11px;padding:1px 5px;font-weight:600;" % (color, color),
        "_raw": raw, "_src": src,
    }
    if instantaneous:
        item["content"] = ""
        item["className"] = "instant-event"
    if e: item["end"] = jsdt(e)
    return item

def log_item(ev, iid, vsw):
    cat = ev.get("event_category", "")
    pre = ev.get("pre_video", False)
    s = parse_ts(ev["timestamp"]) if "timestamp" in ev else \
        wall_dt(ev["wall_time"]) if "wall_time" in ev else \
        sec_dt(ev["video_sec"], vsw)
    e = sec_dt(ev["video_sec_end"], vsw) if "video_sec_end" in ev else \
        (s + timedelta(milliseconds=ev["duration_ms"])) if ev.get("duration_ms") else None

    if cat == "terminal_command":
        outcome = ev.get("outcome", "pass")
        color   = C.get("terminal_" + outcome, C["terminal_pass"])
        cmd     = ev.get("command", "")
        short   = (cmd[:42] + "…") if len(cmd) > 42 else cmd
        tr = ev.get("test_result") or {}
        if tr.get("ran"):
            bad = tr.get("failures", 0) + tr.get("errors", 0)
            label = ("▶✓ " if bad == 0 else "▶✗ ") + short + " (%d)" % tr["ran"]
        else:
            label = "▶ " + short
        return make(iid, label, s, e, "terminal", color, ev, "log", pre)

    if cat == "file_write":
        fname = Path(ev.get("file_path", "?")).name
        return make(iid, "✏ " + fname, s, None, "files", C["file_write"], ev, "log", pre)

    if cat == "agent_trigger":
        return make(iid, "⚡ " + ev.get("agent_type", "trigger"), s, None, "kiro", C["agent_trigger"], ev, "log", pre)

    if cat == "participant_message":
        text  = ev.get("text", "")
        short = (text[:30] + "…") if len(text) > 30 else text
        return make(iid, '💬 "' + short + '"', s, None, "participant", C["participant_message"], ev, "log", pre)

    return None


def lifecycle_item(ev, iid):
    """Render a selected session milestone without duplicating routine logs."""
    stamp = datetime.fromisoformat(ev["timestamp"])
    colors = {
        "study_session_start": "#8250DF",
        "pre_survey_completed": "#BF8700",
        "post_survey_completed": "#BF8700",
        "work_storage_recorded": "#1A7F37",
        "submission_command_recorded": "#CF222E",
        "kiro_shutdown_recorded": "#57606A",
    }
    item = make(iid, "", stamp, None, "session_lifecycle",
                colors.get(ev["event_category"], "#57606A"), ev, "selected")
    item["className"] = "instant-event lifecycle-event"
    return item

def resolve_ann_timing(ev, log_by_id, vsw):
    """
    Place a video episode on the timeline.  When log_anchors reference a log
    event, use that event's timestamp so annotations align with log markers.
    Skip anchors that disagree with the episode's declared time by >2 minutes.
    """
    declared_start = None
    if ev.get("wall_time_start"):
        declared_start = wall_dt(ev["wall_time_start"])
    elif ev.get("timeline_sec_start") is not None:
        declared_start = sec_dt(ev["timeline_sec_start"], vsw)

    for anchor in ev.get("log_anchors", []):
        le = log_by_id.get(anchor.get("log_event_id"))
        if not le:
            continue
        if le.get("timestamp"):
            s = parse_ts(le["timestamp"])
        elif le.get("wall_time"):
            s = wall_dt(le["wall_time"])
        else:
            s = sec_dt(le["video_sec"], vsw)
        if declared_start is not None:
            drift = abs((s - declared_start).total_seconds())
            if drift > 120:
                continue
        dur = ev.get("duration_sec") or 0
        e = s + timedelta(seconds=dur) if dur else None
        synced = dict(ev)
        if le.get("video_sec") is not None:
            synced["timeline_sec_start"] = le["video_sec"]
            synced["video_sec_start"] = le["video_sec"]
        synced["synced_from_log_event_id"] = le.get("id")
        synced["synced_wall_time"] = le.get("wall_time")
        if le.get("text"):
            synced["linked_log_text"] = le["text"]
        return s, e, synced

    if ev.get("wall_time_start"):
        s = wall_dt(ev["wall_time_start"])
    else:
        s = sec_dt(ev.get("timeline_sec_start", ev["video_sec_start"]), vsw)
    e_sec = ev.get("timeline_sec_end", ev.get("video_sec_end"))
    if ev.get("wall_time_end"):
        e = wall_dt(ev["wall_time_end"])
    elif e_sec is not None:
        e = sec_dt(e_sec, vsw)
    else:
        dur = ev.get("duration_sec") or 0
        e = s + timedelta(seconds=dur) if dur else None
    synced = dict(ev)
    if ev.get("timeline_sec_start") is not None:
        synced["timeline_sec_start"] = ev["timeline_sec_start"]
    return s, e, synced


def ann_item(ev, iid, vsw, log_by_id=None):
    cat   = ev.get("event_category", "")
    s, e, synced = resolve_ann_timing(ev, log_by_id or {}, vsw)
    desc  = synced.get("event_description", cat)
    short = (desc[:46] + "…") if len(desc) > 46 else desc
    # Short episodes (e.g. 12s) are invisible at session zoom — widen display only.
    display_end = e
    if e is not None:
        min_display = timedelta(seconds=90)
        if (e - s) < min_display:
            display_end = s + min_display
    CMAP = {
        "task_complete":       (C["task_complete"],       "tasks"),
        "kiro_action":         (C["kiro_action"],         "kiro"),
        "kiro_response":       (C["kiro_response"],       "kiro"),
        "participant_message": (C["participant_message"],  "participant"),
        "reading_behaviour":   (C["reading_behaviour"],   "participant"),
        "approval_decision":   (C["approval_decision"],   "participant"),
        "manual_navigation":   (C["manual_navigation"],   "participant"),
        "behavioural_episode": (C["behavioural_episode"], "video_annotations"),
        "code_edit_accepted":  (C["code_edit_accepted"],  "tasks"),
        "command_result":      (C["command_result"],      "terminal"),
        "video_state_observation": (C["video_state"],      "video_annotations"),
    }
    ICONS = {
        "task_complete":"✅","kiro_action":"⚡","kiro_response":"💡",
        "participant_message":"💬","reading_behaviour":"👁",
        "approval_decision":"✔","code_edit_accepted":"📝","command_result":"💻",
        "manual_navigation":"↗",
        "behavioural_episode":"◈",
        "video_state_observation":"🎥",
    }
    color, _semantic_group = CMAP.get(cat, ("#6E7681", "kiro"))
    # Keep video-derived observations together.  Semantic category remains
    # encoded by colour and in the detail panel, but the source is visible at
    # a glance and never confused with log-derived actor tracks.
    item = make(iid, ICONS.get(cat, "•") + " " + short, s, display_end,
                "video_annotations", color, synced, "video")
    item["style"] += "border-left:3px solid rgba(0,0,0,0.4);"
    return item

def terminal_result_status(ev):
    """Return the most reliable terminal status available for a log event."""
    outcome = ev.get("outcome", "")
    # These are process-level facts and take precedence over parsed output.
    if outcome in ("timeout", "interrupted"):
        return outcome
    parsed = (ev.get("test_result") or {}).get("outcome")
    if parsed == "pass":
        return "pass"
    if parsed in ("fail", "import_error"):
        return "fail"
    return outcome if outcome in ("pass", "fail") else "interrupted"

# Canonical experiment checkpoints — aligned with run_experiment_test_checkpoints.py
# and COLLECTED_DATA_SUMMARY.md §6 (Task1_cp1/2/3, Task2, Task3).
CHECKPOINT_SPECS = [
    {
        "key": "task1_cp1",
        "task_id": "Task 1",
        "checkpoint_id": "CP1",
        "topic": "Routing",
        "summary": "Routing + checkpoint A + routing benchmarks",
        "patterns": [
            ("test_routing_checkpoint_a", ()),
            ("TestNearestNeighborTSP", ()),
            ("TestTwoOptImprove", ()),
            ("test_routing_benchmark", ()),
            ("tests.test_routing", ("test_scalability", "tests.test_matching")),
        ],
    },
    {
        "key": "task1_cp2",
        "task_id": "Task 1",
        "checkpoint_id": "CP2",
        "topic": "Matching",
        "summary": "Matching + matching benchmarks",
        "patterns": [
            ("tests.test_matching", ("test_scalability",)),
            ("tests/test_matching", ("test_scalability",)),
            ("tests.test_matching", ()),
            ("tests/test_matching", ()),
            ("src.optimization.matching", ()),
            ("optimization.matching", ()),
        ],
    },
    {
        "key": "task1_cp3",
        "task_id": "Task 1",
        "checkpoint_id": "CP3",
        "topic": "Scalability",
        "summary": "Scalability performance under time limits",
        "patterns": [
            ("tests.performance.test_scalability", ()),
        ],
    },
    {
        "key": "task2",
        "task_id": "Task 2",
        "checkpoint_id": "CP",
        "topic": "Report",
        "summary": "Report generation correctness",
        "patterns": [
            ("test_report_correctness", ()),
        ],
    },
    {
        "key": "task3",
        "task_id": "Task 3",
        "checkpoint_id": "CP",
        "topic": "Data loader",
        "summary": "Data loader validation",
        "patterns": [
            ("test_data_loader", ()),
        ],
    },
]


def checkpoint_label(spec, status_icon):
    """Normalised timeline label: ✓ T1·CP1 Routing  or  ✓ T2 Report"""
    task_num = spec["task_id"].replace("Task ", "T")
    cp_part = ("·" + spec["checkpoint_id"]) if spec["checkpoint_id"] != "CP" else ""
    short = "%s%s %s" % (task_num, cp_part, spec["topic"])
    return "%s %s" % (status_icon, short)


def checkpoint_description(spec, status_label, prior_issues=0):
    """Normalised detail string: Task 1 · CP1 Routing — passed"""
    cp = spec["checkpoint_id"]
    cp_part = (" · " + cp) if cp != "CP" else ""
    desc = "%s%s %s — %s" % (spec["task_id"], cp_part, spec["topic"], status_label)
    if prior_issues:
        desc += " (after %d prior issue%s)" % (prior_issues, "s" if prior_issues != 1 else "")
    return desc


def checkpoint_attempts(events, patterns):
    """Return terminal commands matching the first pattern that hits."""
    for needle, exclusions in patterns:
        attempts = [e for e in events
                    if e.get("event_category") == "terminal_command"
                    and needle in e.get("command", "")
                    and not any(exclusion in e.get("command", "")
                                for exclusion in exclusions)]
        if attempts:
            return attempts, needle
    return [], None


def checkpoint_choose_attempt(attempts, used_log_ids):
    """Pick the best representative attempt, preferring unclaimed log events."""
    statuses = [terminal_result_status(a) for a in attempts]
    issue_indices = [i for i, value in enumerate(statuses)
                     if value in ("fail", "timeout", "interrupted")]
    preferred = len(attempts) - 1
    if issue_indices:
        last_issue = issue_indices[-1]
        for i in range(last_issue + 1, len(attempts)):
            if statuses[i] == "pass":
                preferred = i
                break
    # Prefer an equally good attempt that has not already anchored another checkpoint.
    candidates = [preferred]
    for i in range(len(attempts) - 1, -1, -1):
        if i not in candidates:
            candidates.append(i)
    for i in candidates:
        log_id = attempts[i].get("id")
        if log_id is None or log_id not in used_log_ids:
            return i, statuses[i]
    return preferred, statuses[preferred]


def checkpoint_make(iid, short_label, s, color, raw):
    """Visible labelled box — unlike generic instant events, text stays readable."""
    text_color = "#0d1117" if color not in (C["not_attempted"], C["pre_video"]) else "#f0f3f6"
    item = {
        "id": iid,
        "content": short_label,
        "start": jsdt(s),
        "group": "tasks",
        "type": "box",
        "className": "checkpoint-event",
        "title": raw.get("event_description", raw.get("checkpoint", "Checkpoint")),
        "style": (
            "background:%s;border-color:%s;color:%s;font-size:10px;"
            "padding:1px 6px;font-weight:700;border-radius:4px;"
        ) % (color, color, text_color),
        "_raw": raw,
        "_src": "derived",
    }
    return item


OFFICIAL_CHECKPOINT_FILES = {
    "task1_cp1": "Task1_cp1.json",
    "task1_cp2": "Task1_cp2.json",
    "task1_cp3": "Task1_cp3.json",
    "task2": "Task2.json",
    "task3": "Task3.json",
}


def load_official_checkpoint(participant, key):
    """Post-session canonical result — matches COLLECTED_DATA_SUMMARY.md §6."""
    filename = OFFICIAL_CHECKPOINT_FILES.get(key)
    if not filename:
        return None
    path = EXPERIMENT_DATA / participant / "task_checkpoints" / filename
    if not path.exists():
        return None
    return json.loads(path.read_text())


def official_checkpoint_status(official):
    if not official:
        return "not_attempted", "not attempted"
    stats = official.get("test_statistics") or {}
    success = official.get("success")
    if success is None:
        success = stats.get("success")
    return ("pass", "passed") if success else ("fail", "failed")


def official_command_str(official):
    cmd = official.get("command")
    if isinstance(cmd, list):
        return " ".join(cmd)
    return cmd or ""


def checkpoint_items(events, iid, vsw, session_end, participant):
    """One marker per official experiment checkpoint.

    Pass/fail comes from ``task_checkpoints/*.json`` (post-session canonical
    runs).  In-session terminal logs are used only for timeline placement,
    seek coordinates, and session-time context — never to override the official
    result recorded in COLLECTED_DATA_SUMMARY.md.
    """
    status_icon = {"pass": "✓", "fail": "✗", "not_attempted": "○"}
    result = []
    used_log_ids = set()
    placement_counts = {}

    for index, spec in enumerate(CHECKPOINT_SPECS):
        official = load_official_checkpoint(participant, spec["key"])
        status, status_label = official_checkpoint_status(official)
        attempts, matched_needle = checkpoint_attempts(events, spec["patterns"])
        chosen = None
        if attempts:
            chosen_index, _ignored = checkpoint_choose_attempt(attempts, used_log_ids)
            chosen = attempts[chosen_index]
            log_id = chosen.get("id")
            if log_id is not None:
                used_log_ids.add(log_id)

        if chosen:
            s = (parse_ts(chosen["timestamp"]) if chosen.get("timestamp")
                 else wall_dt(chosen["wall_time"]))
            placement_key = chosen.get("id") if chosen.get("id") is not None else jsdt(s)
            stagger = placement_counts.get(placement_key, 0)
            placement_counts[placement_key] = stagger + 1
            if stagger:
                s = s + timedelta(seconds=stagger * 5)
            placement_note = "Placed at closest in-session terminal run (seek target)."
        else:
            s = session_end - timedelta(minutes=(len(CHECKPOINT_SPECS) - index) * 2)
            placement_note = (
                "No matching in-session terminal run; marker placed near session end. "
                "Official result is from post-session checkpoint run."
            )

        stats = (official or {}).get("test_statistics") or {}
        official_cmd = official_command_str(official) if official else ""
        session_cmd = chosen.get("command", "") if chosen else ""
        cmd = official_cmd or session_cmd
        short_cmd = (cmd[:72] + "…") if len(cmd) > 72 else cmd

        session_status = terminal_result_status(chosen) if chosen else None
        session_mismatch = (
            chosen is not None and session_status is not None
            and ((status == "pass" and session_status in ("fail", "timeout", "interrupted"))
                 or (status == "fail" and session_status == "pass"))
        )

        desc = checkpoint_description(spec, status_label)
        raw = {
            "source": "official_task_checkpoint",
            "event_category": "checkpoint_status",
            "canonical_key": spec["key"],
            "task_id": spec["task_id"],
            "checkpoint_id": spec["checkpoint_id"],
            "topic": spec["topic"],
            "checkpoint": "%s · %s%s" % (
                spec["task_id"],
                spec["checkpoint_id"] + " " if spec["checkpoint_id"] != "CP" else "",
                spec["topic"],
            ),
            "task": "%s · %s" % (spec["task_id"], spec["topic"]),
            "summary": spec["summary"],
            "status": status,
            "status_label": status_label,
            "result_source": "official_post_session" if official else "missing_official_file",
            "event_description": desc,
            "official_result": {
                "success": official.get("success") if official else None,
                "started_at": official.get("started_at") if official else None,
                "finished_at": official.get("finished_at") if official else None,
                "duration_seconds": official.get("duration_seconds") if official else None,
                "tests_run": stats.get("tests_run"),
                "failures": stats.get("failures"),
                "errors": stats.get("errors"),
                "command": official_cmd or None,
            } if official else None,
            "session_log_attempts": len(attempts),
            "session_log_match": matched_needle,
            "session_terminal_status": session_status,
            "session_terminal_mismatch": session_mismatch,
            "status_terminal_log": chosen,
            "wall_time": chosen.get("wall_time") if chosen else None,
            "video_sec": chosen.get("video_sec") if chosen else None,
            "command": cmd or None,
            "command_short": short_cmd or None,
            "display_note": placement_note + (
                " Result matches COLLECTED_DATA_SUMMARY.md (official post-session run)."
                if official else " Official checkpoint file missing."
            ) + (
                " Session-time terminal outcome differed from final official result."
                if session_mismatch else ""
            ),
        }
        label = checkpoint_label(spec, status_icon.get(status, "○"))
        color = C.get("terminal_" + status, C["not_attempted"]) if status != "not_attempted" else C["not_attempted"]
        result.append(checkpoint_make(iid, label, s, color, raw))
        iid += 1
    return result

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--participant", default="ai-01")
    args = ap.parse_args()
    p = args.participant

    base    = Path(__file__).parent
    out_dir = base / "output"
    lib_dir = base / "lib"

    log_path = out_dir / (p + "_log_events.json")
    ann_path = out_dir / (p + "_annotation.json")
    js_path  = lib_dir / "vis-timeline.min.js"
    css_path = lib_dir / "vis-timeline.min.css"

    for path in (log_path, js_path, css_path):
        if not path.exists():
            print("ERROR: %s not found." % path)
            raise SystemExit(1)

    with open(log_path)  as f: log_data = json.load(f)
    with open(js_path)   as f: vis_js   = f.read()
    with open(css_path)  as f: vis_css  = f.read()

    ann_data = json.load(open(ann_path)) if ann_path.exists() else None
    summary  = log_data.get("summary", {})
    # The timeline clock is the fixed study-session origin.  Recording coverage
    # is anchored separately, using the reviewed first-frame clock reference.
    vsw      = log_data.get("video_start_wall", "09:00:00")
    all_evs  = log_data.get("events", [])
    log_by_id = {e["id"]: e for e in all_evs if e.get("id") is not None}

    # Recording files are source-of-truth for coverage duration.  This is
    # intentionally independent of Kiro log activity, which can stop long
    # before the participant's screen recording ends.
    video_dir = EXPERIMENT_DATA / p / "videos"
    candidates = sorted(video_dir.glob("GENIUS_%s_*.mp4" % p)) if video_dir.exists() else []
    video_urls = [os.path.relpath(path, out_dir) for path in candidates]
    video_durations = [media_duration_seconds(path) for path in candidates]
    video_total_sec = sum(video_durations)
    video_found = bool(video_urls)

    session_start_raw = log_data.get("session_start_timestamp")
    session_start_dt = (datetime.fromisoformat(session_start_raw)
                        if session_start_raw else wall_dt(vsw))
    alignment_status = (ann_data or {}).get("video_alignment_status", "pending")
    # The recorder's local wall clock is enough to place coverage and seek by
    # wall time.  A "validated" mapping has additionally passed visible
    # message/command anchor checks.
    alignment_valid = alignment_status in {"validated", "clock_aligned"}
    aligned_video_wall = (ann_data or {}).get("video_start_wall")
    video_start_dt = (wall_dt(aligned_video_wall)
                      if alignment_valid and aligned_video_wall else session_start_dt)
    video_part_starts = []
    next_start = (video_start_dt - session_start_dt).total_seconds()
    annotation_parts = (ann_data or {}).get("video_parts", [])
    for index, duration in enumerate(video_durations):
        part_wall = (annotation_parts[index].get("timeline_start_wall")
                     if index < len(annotation_parts) else None)
        if alignment_valid and part_wall:
            next_start = (wall_dt(part_wall) - session_start_dt).total_seconds()
        video_part_starts.append(next_start)
        next_start += duration
    video_end_dt = session_start_dt + timedelta(
        seconds=max((start + duration for start, duration in zip(video_part_starts, video_durations)),
                    default=(video_start_dt - session_start_dt).total_seconds())
    )
    session_end_raw = log_data.get("session_end_timestamp")
    session_end_dt = (datetime.fromisoformat(session_end_raw)
                      if session_end_raw else session_start_dt)
    dur_min = round((session_end_dt - session_start_dt).total_seconds() / 60, 1)
    vs_iso  = jsdt(session_start_dt)
    video_end_iso = jsdt(video_end_dt)
    end_iso = jsdt(session_end_dt)
    pre_iso = jsdt(wall_dt(vsw) - timedelta(minutes=30))

    # Build items
    items, iid, ann_n = [], 1, 0
    for ev in all_evs:
        it = log_item(ev, iid, vsw)
        if it: items.append(it); iid += 1
    checkpoints = checkpoint_items(all_evs, iid, vsw, session_end_dt, p)
    items.extend(checkpoints)
    iid += len(checkpoints)
    for ev in log_data.get("selected_timestamp_events", []):
        it = lifecycle_item(ev, iid)
        items.append(it)
        iid += 1
    if ann_data:
        for ev in ann_data.get("events", []):
            # Sparse reconnaissance is retained in the source JSON for audit,
            # but it is not a final video annotation and must never appear in
            # the Video Annotations track.
            if ev.get("event_category") == "video_state_observation":
                continue
            it = ann_item(ev, iid, vsw, log_by_id)
            if it: items.append(it); iid += 1; ann_n += 1

    vis_items, raw_map = [], {}
    for it in items:
        raw_map[it["id"]] = {"data": it["_raw"], "src": it["_src"]}
        vis_items.append({k: v for k, v in it.items() if not k.startswith("_")})

    # Participant tab info
    tabs = []
    for pp in ALL_PARTICIPANTS:
        has_data = (out_dir / (pp + "_log_events.json")).exists()
        tabs.append({"id": pp, "active": pp == p, "has_data": has_data})

    # Stats
    stats = {
        "pass":    summary.get("commands_passed", 0),
        "fail":    summary.get("commands_failed", 0) + summary.get("commands_interrupted", 0),
        "timeout": summary.get("commands_timeout", 0),
        "writes":  summary.get("file_writes", 0),
        "msgs":    sum(1 for e in all_evs if e.get("event_category") == "participant_message"),
        "ann":     ann_n,
        "selected": len(log_data.get("selected_timestamp_events", [])),
        "total":   len(vis_items),
    }

    html = build_html(
        vis_js=vis_js, vis_css=vis_css,
        participant=p, dur_min=dur_min, vsw=vsw,
        items_json=json.dumps(vis_items, ensure_ascii=False),
        raw_json=json.dumps(raw_map, ensure_ascii=False),
        groups_json=json.dumps(GROUPS),
        vs_iso=vs_iso, video_end_iso=video_end_iso, end_iso=end_iso, pre_iso=pre_iso,
        video_urls=video_urls, video_durations=video_durations, video_part_starts=video_part_starts,
        video_found=video_found, video_alignment_valid=alignment_valid,
        video_alignment_status=alignment_status,
        tabs=tabs, stats=stats,
    )

    out = out_dir / (p + "_timeline.html")
    out.write_text(html, encoding="utf-8")
    print("Written: %s" % out)
    print("  %d items (%d video-annotated)" % (len(vis_items), ann_n))
    print("  Videos: %s" % (", ".join(str(u) for u in video_urls) or "not found"))
    print("  Open in Safari: open -a Safari '%s'" % out)

# ── HTML ───────────────────────────────────────────────────────────────────────

def build_html(vis_js, vis_css, participant, dur_min, vsw,
               items_json, raw_json, groups_json,
               vs_iso, video_end_iso, end_iso, pre_iso, video_urls, video_durations, video_part_starts, video_found,
               video_alignment_valid, video_alignment_status, tabs, stats):

    # Participant tab HTML
    tab_html = ""
    for t in tabs:
        if t["active"]:
            tab_html += '<button class="tab active" disabled>%s</button>' % t["id"]
        elif t["has_data"]:
            tab_html += '<a class="tab" href="%s_timeline.html">%s</a>' % (t["id"], t["id"])
        else:
            tab_html += '<span class="tab disabled" title="Run extract_log_events.py --participant %s first">%s</span>' % (t["id"], t["id"])

    # Video parts are sequential recording segments, never browser fallbacks.
    if video_found:
        video_src_attr = video_urls[0]
        extra_sources  = ""
        video_count_label = ("%d parts" % len(video_urls)) if len(video_urls) > 1 else ""
    else:
        video_src_attr = ""
        extra_sources  = ""
        video_count_label = ""

    video_urls_js = json.dumps(video_urls)
    video_durations_js = json.dumps(video_durations)

    # Legend entries (no more gray for agent_trigger)
    legend_items = [
        ("#3FB950", "Pass"), ("#F85149", "Fail"), ("#D29922", "Timeout"),
        ("#E3B341", "Interrupted"), ("#388BFD", "Message"), ("#BC8CFF", "Reading"),
        ("#FF7B72", "Approval"), ("#39D353", "Task done"), ("#D2A8FF", "File write"),
        ("#79C0FF", "Agent trigger"),
        ("#1F6FEB", "Recorded video"),
        ("pre", "Pre-recording (dim)"),
    ]
    legend_html = ""
    for item in legend_items:
        if item[0] == "pre":
            legend_html += '<span class="leg"><span class="dot" style="background:#484F58;opacity:.4"></span>%s</span>' % item[1]
        else:
            legend_html += '<span class="leg"><span class="dot" style="background:%s"></span>%s</span>' % item

    return (
"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>GENIUS """ + participant + """ — Session Timeline</title>
<style>
""" + vis_css + """

/* ── Design tokens ── */
:root {
  --bg:        #FFFFFF;
  --surface:   #F6F8FA;
  --surface2:  #FFFFFF;
  --border:    #D0D7DE;
  --border2:   #8C959F;
  --text:      #1F2328;
  --text-2:    #3D444D;
  --text-3:    #57606A;
  --accent:    #388BFD;
  --accent-bg: rgba(56,139,253,0.1);
  --red:       #F85149;
  --green:     #3FB950;
  --amber:     #D29922;
  --mono:      'SF Mono','Monaco','Cascadia Code','Consolas',monospace;
}

/* ── Reset ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body { height: 100%; background: var(--bg); color: var(--text);
             font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
             font-size: 13px; line-height: 1.5; overflow: hidden; }

/* ── Top bar: minimal — just title ── */
#topbar {
  display: flex; align-items: center;
  background: var(--surface); border-bottom: 1px solid var(--border);
  padding: 0 14px; height: 36px; flex-shrink: 0;
}
#title { font-size: 11px; color: var(--text-3); letter-spacing: .1em;
         text-transform: uppercase; font-weight: 700; }

/* ── Info sidebar: legend + stats (left of video) ── */
#info-panel {
  width: 190px; flex-shrink: 0;
  background: var(--surface); border-right: 1px solid var(--border);
  display: flex; flex-direction: column; padding: 12px 10px; gap: 14px; overflow-y: auto;
}
#info-panel h4 { font-size: 9px; font-weight: 700; color: var(--text-3);
                  text-transform: uppercase; letter-spacing: .08em; margin-bottom: 6px; }
.leg { display: flex; align-items: center; gap: 6px; font-size: 11px; color: var(--text-2);
       padding: 2px 0; }
.dot { width: 10px; height: 10px; border-radius: 3px; flex-shrink: 0; }
.stat-row { display: flex; align-items: center; justify-content: space-between;
             padding: 3px 0; border-bottom: 1px solid var(--border); }
.stat-label { font-size: 10px; color: var(--text-3); }
.stat-val { font-size: 11px; font-weight: 700; font-family: var(--mono); }
.stat { font-size: 10px; padding: 1px 7px; border-radius: 10px; font-weight: 700;
        font-family: var(--mono); white-space: nowrap; }

/* ── Main: column layout ── */
#main {
  display: flex; flex-direction: column;
  height: calc(100vh - 44px); overflow: hidden;
}

/* ── Top section: video (center) + right panel ── */
#top-section {
  display: flex; flex-direction: row;
  height: 44vh; min-height: 160px; flex-shrink: 0; overflow: hidden;
}

/* Video area — dark bg, centered */
#video-wrap {
  flex: 1; min-width: 0; background: #000;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: 8px 8px 4px;
}
#video {
  display: block; max-width: 100%; max-height: calc(100% - 30px);
  width: auto; height: auto; border-radius: 3px;
}
#vbar { display: flex; align-items: center; gap: 10px; margin-top: 4px;
        width: 100%; padding: 0 4px; }
#vtime { font-family: var(--mono); font-size: 11px; color: #aaa; min-width: 62px; flex-shrink: 0; }
#vs-now { font-size: 10px; color: var(--text-3); flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
#vno-file { font-size: 10px; color: #D29922; display: none; }

/* Right panel: tabs + detail */
#right-panel {
  width: 300px; flex-shrink: 0;
  border-left: 1px solid var(--border);
  background: var(--surface);
  display: flex; flex-direction: column;
}
#tabs-wrap {
  display: flex; flex-wrap: wrap; gap: 0; padding: 6px 8px; flex-shrink: 0;
  border-bottom: 1px solid var(--border); background: var(--surface2);
}
.tab {
  padding: 3px 10px; font-size: 11px; font-weight: 600; cursor: pointer;
  border: 1px solid var(--border); border-radius: 4px; background: none;
  color: var(--text-2); text-decoration: none; display: inline-block;
  margin: 2px; transition: background .12s, color .12s;
}
.tab:hover { background: var(--surface); color: var(--text); }
.tab.active { background: var(--accent-bg); color: var(--accent); border-color: var(--accent); cursor: default; }
.tab.disabled { color: var(--text-3); cursor: not-allowed; opacity: .5; }

/* Detail panel */
#dp { flex: 1; overflow-y: auto; padding: 10px; }
#dp-title { font-size: 11px; font-weight: 700; color: var(--text); margin-bottom: 8px;
             display: flex; align-items: center; gap: 6px; }
.src-badge { font-size: 10px; padding: 1px 6px; border-radius: 8px;
             background: var(--surface2); color: var(--text-2); font-weight: 600; }
.ph { color: var(--text-3); font-size: 11px; line-height: 1.7; }
.field { padding: 4px 0; border-bottom: 1px solid var(--border); }
.fk { font-size: 9px; font-weight: 700; color: var(--accent); text-transform: uppercase;
       letter-spacing: .05em; margin-bottom: 1px; }
.fv { color: var(--text-2); word-break: break-word; font-size: 11px; }
.out { background: var(--bg); padding: 6px; border-radius: 4px; margin-top: 3px;
       font-family: var(--mono); font-size: 9px; line-height: 1.6;
       white-space: pre-wrap; max-height: 150px; overflow-y: auto;
       color: #7EE787; border: 1px solid var(--border); }
.seek-btn { display: inline-flex; align-items: center; gap: 4px; margin-bottom: 8px;
             padding: 4px 10px; background: var(--accent-bg); color: var(--accent);
             border: 1px solid var(--accent); border-radius: 4px; cursor: pointer;
             font-size: 11px; font-weight: 600; transition: background .15s; }
.seek-btn:hover { background: var(--accent); color: #0d1117; }

/* ── Resize handle ── */
#resize-handle {
  height: 6px; background: var(--border); cursor: ns-resize; flex-shrink: 0;
  transition: background .15s;
}
#resize-handle:hover { background: var(--accent); }

/* ── Timeline section ── */
#tl-section { flex: 1; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }
#tl-hint {
  font-size: 10px; color: var(--text-3); padding: 3px 12px;
  background: var(--surface); border-bottom: 1px solid var(--border); flex-shrink: 0;
  display: flex; align-items: center; gap: 8px;
}
#tl-help { flex: 1; }
.tl-control { background: var(--surface2); color: var(--text-2); border: 1px solid var(--border2);
              border-radius: 3px; cursor: pointer; font: 700 12px var(--mono); line-height: 20px;
              min-width: 24px; padding: 0 6px; }
.tl-control:hover { color: var(--text); border-color: var(--accent); }
.video-band-key { color: #79C0FF; font-weight: 700; }
#tl { flex: 1; min-height: 0; overflow: hidden; }

/* ── vis.js dark overrides ── */
.vis-timeline { height: 100% !important; visibility: visible !important;
                background: var(--bg) !important; border: none !important; }
/* vis-timeline occasionally leaves this transparent loading element in the
   DOM after a constrained-height redraw; otherwise it intercepts every item. */
.vis-loading-screen { display: none !important; pointer-events: none !important; }
.vis-panel.vis-left { background: var(--surface) !important; border-right: 1px solid var(--border) !important; }
.vis-label { color: var(--text-2) !important; font-size: 11px !important; font-weight: 600 !important;
             letter-spacing: .03em; text-transform: uppercase; }
.vis-time-axis .vis-text { color: var(--text-3) !important; font-size: 10px !important; font-family: var(--mono); }
.vis-time-axis .vis-grid.vis-major { border-color: var(--border2) !important; }
.vis-time-axis .vis-grid.vis-minor { border-color: var(--border) !important; }
.vis-panel.vis-background { background: var(--bg) !important; }
.vis-item.vis-selected { filter: brightness(1.3); box-shadow: 0 0 0 2px rgba(255,255,255,.35) !important; }
/* Timestamp-only events use a box rather than vis-timeline's point type.
   This keeps one marker fully inside its category track and lets the library
   stack it clear of interval annotations. */
/* A vis "box" item also creates a dot and connector line for its axis
   position.  They are implementation artifacts here, not separate events. */
.vis-item.vis-dot.instant-event, .vis-item.vis-line.instant-event { display: none !important; }
.vis-item.vis-box.instant-event { width: 20px !important; height: 20px !important; padding: 0 !important;
                                   border: 0 !important; border-radius: 50% !important; }
.vis-item.vis-box.instant-event .vis-item-content { display: none !important; }
.vis-item.vis-box.lifecycle-event { width: 14px !important; height: 14px !important;
                                    opacity: .9; }
/* Checkpoint markers keep their label visible and stay easy to click. */
.vis-item.vis-box.checkpoint-event { width: auto !important; min-width: 52px !important;
                                     height: 22px !important; padding: 0 !important;
                                     border-radius: 4px !important; cursor: pointer !important; }
.vis-item.vis-box.checkpoint-event .vis-item-content {
  display: block !important; padding: 2px 6px !important; line-height: 16px !important;
  white-space: nowrap !important;
}
.vis-item.vis-dot.checkpoint-event, .vis-item.vis-line.checkpoint-event { display: none !important; }
#hover-tip { display: none; position: fixed; z-index: 30; max-width: 340px; padding: 8px 10px;
             background: #1F2328; color: #FFFFFF; border-radius: 5px; box-shadow: 0 3px 14px rgba(0,0,0,.25);
             font-size: 11px; line-height: 1.4; pointer-events: none; overflow-wrap: anywhere; }
#hover-tip b { color: #79C0FF; }
/* ph = video playhead (orange, draggable) */
.vis-custom-time.ph { background: #F0883E !important; width: 2px !important; cursor: ew-resize !important; }
.vis-custom-time.ph .vis-custom-time-marker {
  background: #F0883E !important; color: #0d1117 !important;
  font-size: 10px !important; font-weight: 700 !important;
  border-radius: 3px !important; padding: 1px 5px !important;
  white-space: nowrap !important;
}
.vis-tooltip { background: var(--surface2) !important; color: var(--text) !important;
               border: 1px solid var(--border2) !important; font-size: 11px !important;
               padding: 8px !important; max-width: 300px !important; border-radius: 6px !important; }
.vis-item.video-part { background: rgba(56,139,253,.22) !important; border-color: #1F6FEB !important;
                       color: #0d1117 !important; font-size: 10px !important; }
</style>
</head>
<body>

<div id="topbar">
  <span id="title">GENIUS — """ + participant + """</span>
</div>

<div id="main">

  <div id="top-section">

    <div id="info-panel">
      <div>
        <h4>Legend</h4>
""" + legend_html + """
      </div>
      <div>
        <h4>Session</h4>
        <div class="stat-row"><span class="stat-label">Participant</span><span class="stat-val" style="color:var(--accent)">""" + participant + """</span></div>
        <div class="stat-row"><span class="stat-label">Start</span><span class="stat-val">""" + vsw + """</span></div>
        <div class="stat-row"><span class="stat-label">Session span</span><span class="stat-val">""" + str(dur_min) + """ min</span></div>
        <div class="stat-row"><span class="stat-label">Events</span><span class="stat-val">""" + str(stats["total"]) + """</span></div>
        <div class="stat-row"><span class="stat-label">Lifecycle evidence</span><span class="stat-val">""" + str(stats["selected"]) + """</span></div>
      </div>
      <div>
        <h4>Terminal</h4>
        <div class="stat-row"><span class="stat-label">Pass</span><span class="stat-val" style="color:#3FB950">""" + str(stats["pass"]) + """</span></div>
        <div class="stat-row"><span class="stat-label">Fail / Int</span><span class="stat-val" style="color:#F85149">""" + str(stats["fail"]) + """</span></div>
        <div class="stat-row"><span class="stat-label">Timeout</span><span class="stat-val" style="color:#D29922">""" + str(stats["timeout"]) + """</span></div>
        <div class="stat-row"><span class="stat-label">File writes</span><span class="stat-val" style="color:#D2A8FF">""" + str(stats["writes"]) + """</span></div>
        <div class="stat-row"><span class="stat-label">Messages</span><span class="stat-val" style="color:#388BFD">""" + str(stats["msgs"]) + """</span></div>
        """ + ('<div class="stat-row"><span class="stat-label">Annotated</span><span class="stat-val" style="color:#39D353">%d</span></div>' % stats["ann"] if stats["ann"] else "") + """
      </div>
    </div>

    <div id="video-wrap">
      <video id="video" controls preload="auto" src=\"""" + video_src_attr + """\">""" + extra_sources + """</video>
      <div id="vbar">
        <span id="vtime">00:00:00</span>
        <span id="vs-now">""" + (video_count_label or ("drag orange line or click events to seek" if video_found else "")) + """</span>
        <span id="vno-file">""" + ("" if video_found else "not found — run serve_timeline.py") + """</span>
      </div>
    </div>

    <div id="right-panel">
      <div id="tabs-wrap">""" + tab_html + """</div>
      <div id="dp">
        <div class="ph">Click any event to see details.<br><br>
        Orange line = playhead. Drag it or click events to seek.</div>
      </div>
    </div>
  </div>

  <div id="resize-handle" title="Drag to resize"></div>

  <div id="tl-section">
    <div id="tl-hint">
      <span id="tl-help">Two-finger scroll: horizontal = pan time, vertical = scroll tracks &nbsp;·&nbsp; Pinch = track thickness &nbsp;·&nbsp; Dots = instant events (hover for details) &nbsp;·&nbsp; <span class="video-band-key">Blue band = recorded video</span></span>
      <button class="tl-control" id="zoom-out" title="Zoom out in time">Time −</button>
      <button class="tl-control" id="zoom-reset" title="Show the complete session">Reset</button>
      <button class="tl-control" id="zoom-in" title="Zoom in time">Time +</button>
    </div>
    <div id="tl"></div>
  </div>

</div>
<div id="hover-tip"></div>

<script>
""" + vis_js + """
</script>
<script>
var ITEMS       = """ + items_json + """;
var RAW         = """ + raw_json + """;
var GROUPS      = """ + groups_json + """;
var VS_ISO      = '""" + vs_iso  + """';
var VIDEO_END_ISO = '""" + video_end_iso + """';
var SESSION_END_ISO = '""" + end_iso + """';
var DUR_MIN     = """ + str(dur_min) + """;
var VIDEO_URLS  = """ + video_urls_js + """;
var VIDEO_DURATIONS_KNOWN = """ + video_durations_js + """;
var VIDEO_PART_STARTS = """ + json.dumps(video_part_starts) + """;
var VIDEO_ALIGNMENT_VALID = """ + json.dumps(video_alignment_valid) + """;
var VIDEO_ALIGNMENT_STATUS = """ + json.dumps(video_alignment_status) + """;

var groups = new vis.DataSet(GROUPS);
var items  = new vis.DataSet(ITEMS);

window.addEventListener('load', function () {
  var tlEl    = document.getElementById('tl');
  var tlSec   = document.getElementById('tl-section');
  var hintEl  = document.getElementById('tl-hint');
  var topSec  = document.getElementById('top-section');
  var handle  = document.getElementById('resize-handle');

  var VS_DATE = new Date(VS_ISO);

  // Set timeline height from remaining space after top-section + resize handle
  function setTlHeight() {
    tlEl.style.height = Math.max(80, tlSec.clientHeight - hintEl.offsetHeight) + 'px';
    if (typeof tl !== 'undefined') tl.redraw();
  }
  setTlHeight();

  var WIN_START = VS_DATE;
  var WIN_END   = new Date(SESSION_END_ISO);

  var tl = new vis.Timeline(tlEl, items, groups, {
    groupOrder:      'order',
    stack:           true,
    showMajorLabels: true,
    showMinorLabels: true,
    zoomMin:   5000,
    zoomMax:   4 * 3600 * 1000,
    zoomable: false,
    moveable: true,
    horizontalScroll: true,
    verticalScroll: true,
    start:     WIN_START,
    end:       WIN_END,
    selectable: true,
    orientation: { axis: 'top' },
    // Leave a visible gap between neighbouring annotations.  With stack:true,
    // events that still collide are placed in the next layout lane.
    margin:     { item: { horizontal: 6, vertical: 6 } },
  });
  // Enforce window again after construction (vis.js may override start/end if items fall outside)
  tl.setWindow(WIN_START, WIN_END, { animation: false });

  // Use vis-timeline's own bounded vertical-scroll state.  Its side-panel DOM
  // is not a stable public target across builds, but this is the same state
  // updated by its native wheel/drag implementation.
  function scrollTracksBy(amount) {
    var before = tl._getScrollTop();
    // scrollTop is zero at the top and negative below it.
    var after = tl._setScrollTop(before - amount);
    if (after !== before) tl.redraw();
    return after !== before;
  }
  tlEl.addEventListener('wheel', function(e) {
    // Preserve native horizontal two-finger panning.  Only claim a gesture
    // whose vertical component is dominant.
    if (e.ctrlKey || Math.abs(e.deltaY) <= Math.abs(e.deltaX)) return;
    if (scrollTracksBy(e.deltaY)) {
      e.preventDefault();
      e.stopPropagation();
    }
  }, { passive: false, capture: true });

  var bgDrag = null;
  tlEl.addEventListener('pointerdown', function(e) {
    if (e.button !== 0 || e.target.closest('.vis-item, .vis-custom-time, .vis-time-axis')) return;
    if (!e.target.closest('.vis-panel.vis-center')) return;
    bgDrag = { id: e.pointerId, x: e.clientX, y: e.clientY,
               window: tl.getWindow(), scrollTop: tl._getScrollTop() };
    // This is a background-only drag.  Items keep their native events.
    e.stopPropagation();
  }, true);
  tlEl.addEventListener('pointermove', function(e) {
    if (!bgDrag || e.pointerId !== bgDrag.id) return;
    var dx = e.clientX - bgDrag.x;
    var dy = e.clientY - bgDrag.y;
    var span = bgDrag.window.end.getTime() - bgDrag.window.start.getTime();
    var width = Math.max(1, tlEl.querySelector('.vis-panel.vis-center').clientWidth);
    if (dx) {
      var shift = -dx * span / width;
      tl.setWindow(new Date(bgDrag.window.start.getTime() + shift),
                   new Date(bgDrag.window.end.getTime() + shift), { animation: false });
    }
    var before = tl._getScrollTop();
    var after = tl._setScrollTop(bgDrag.scrollTop + dy);
    if (after !== before) tl.redraw();
    tlEl.style.cursor = 'grabbing';
    e.preventDefault();
    e.stopPropagation();
  }, { passive: false, capture: true });
  function endBackgroundDrag(e) {
    if (!bgDrag || (e && e.pointerId !== bgDrag.id)) return;
    bgDrag = null;
    tlEl.style.cursor = '';
  }
  tlEl.addEventListener('pointerup', endBackgroundDrag, true);
  tlEl.addEventListener('pointercancel', endBackgroundDrag, true);

  function zoomTimeline(factor) {
    var window = tl.getWindow();
    var center = (window.start.getTime() + window.end.getTime()) / 2;
    var span = (window.end.getTime() - window.start.getTime()) * factor;
    tl.setWindow(new Date(center - span / 2), new Date(center + span / 2));
  }
  document.getElementById('zoom-in').addEventListener('click', function() { zoomTimeline(0.65); });
  document.getElementById('zoom-out').addEventListener('click', function() { zoomTimeline(1.55); });
  document.getElementById('zoom-reset').addEventListener('click', function() {
    tl.setWindow(WIN_START, WIN_END, { animation: false });
  });

  var laneGap = 6;
  function adjustTrackSpacing(delta) {
    laneGap = Math.max(2, Math.min(32, laneGap + delta / 4));
    tl.setOptions({ margin: { item: { horizontal: 6, vertical: laneGap } } });
  }
  var pinchScale = 1;
  tlEl.addEventListener('wheel', function(e) {
    if (!e.ctrlKey) return;
    e.preventDefault();
    adjustTrackSpacing(e.deltaY < 0 ? 8 : -8);
  }, { passive: false, capture: true });
  tlEl.addEventListener('gesturestart', function(e) { pinchScale = e.scale; e.preventDefault(); }, { passive: false });
  tlEl.addEventListener('gesturechange', function(e) {
    e.preventDefault();
    adjustTrackSpacing((e.scale - pinchScale) * 48);
    pinchScale = e.scale;
  }, { passive: false });

  // Orange playhead
  tl.addCustomTime(VS_DATE, 'ph');
  tl.setCustomTimeTitle('▶ playhead', 'ph');

  // ── Resize handle: drag to split top-section and timeline ─────────────────
  var resizing = false, resizeStartY = 0, resizeStartH = 0;
  handle.addEventListener('mousedown', function(e) {
    resizing = true; resizeStartY = e.clientY; resizeStartH = topSec.offsetHeight;
    document.body.style.cursor = 'ns-resize'; e.preventDefault();
  });
  document.addEventListener('mousemove', function(e) {
    if (!resizing) return;
    var newH = resizeStartH + (e.clientY - resizeStartY);
    newH = Math.max(120, Math.min(newH, window.innerHeight - 180));
    topSec.style.height = newH + 'px';
    setTlHeight();
  });
  document.addEventListener('mouseup', function() {
    if (!resizing) return;
    resizing = false; document.body.style.cursor = '';
    setTlHeight();
  });

  // ── Video multi-part support ───────────────────────────────────────────────
  var video    = document.getElementById('video');
  var vtime    = document.getElementById('vtime');
  var vsNow    = document.getElementById('vs-now');
  var vNoFile  = document.getElementById('vno-file');
  var videoIdx = 0;
  // Timeline seconds at which each recording part begins.  The first part is
  // aligned to a reviewed on-screen clock; later parts continue from it.
  var VIDEO_OFFSETS = VIDEO_PART_STARTS.slice();
  var VIDEO_DURATIONS = VIDEO_DURATIONS_KNOWN.slice();
  for (var knownIndex = 1; knownIndex < VIDEO_DURATIONS.length; knownIndex++) {
    VIDEO_OFFSETS.push(VIDEO_OFFSETS[knownIndex - 1] + VIDEO_DURATIONS[knownIndex - 1]);
  }

  function renderVideoCoverage() {
    items.remove(items.getIds({filter:function(item) { return String(item.id).indexOf('video-part-') === 0; }}));
    // A recording must not be placed on the study clock until a visible
    // command/message anchor has verified the mapping.  Showing an attractive
    // but wrong band is worse than showing no band at all.
    if (!VIDEO_ALIGNMENT_VALID) return;
    var sessionEndSec = (new Date(SESSION_END_ISO).getTime() - VS_DATE.getTime()) / 1000;
    for (var i = 0; i < VIDEO_DURATIONS.length; i++) {
      var start = VIDEO_OFFSETS[i];
      var end = start + VIDEO_DURATIONS[i];
      // The fixed study window is authoritative.  Footage outside it remains
      // on disk but is not evidence for this session and must not expand the UI.
      if (end <= 0 || start >= sessionEndSec) continue;
      start = Math.max(0, start);
      end = Math.min(sessionEndSec, end);
      items.add({
        id: 'video-part-' + i,
        content: 'Part ' + (i + 1) + (VIDEO_ALIGNMENT_STATUS === 'validated'
          ? ' · validated' : ' · recording clock'),
        start: new Date(VS_DATE.getTime() + start * 1000),
        end: new Date(VS_DATE.getTime() + end * 1000),
        group: 'video_coverage', type: 'range', className: 'video-part',
        title: 'Part ' + (i + 1) + (VIDEO_ALIGNMENT_STATUS === 'validated'
          ? ' — validated against visible log anchors'
          : ' — placed from local recording clock; event-anchor check pending')
      });
    }
  }
  // The metadata-derived durations render every discovered part immediately;
  // loadedmetadata below verifies or fills any duration unavailable to mdls.
  renderVideoCoverage();

  // ── Video setup ───────────────────────────────────────────────────────────
  if (!VIDEO_URLS.length) {
    vNoFile.style.display = 'block';
  }

  // Status feedback (all visible in the UI, no need for browser console)
  video.addEventListener('error', function() {
    var e = video.error;
    var codes = {1:'ABORTED', 2:'NETWORK ERROR', 3:'DECODE ERROR', 4:'FORMAT NOT SUPPORTED'};
    var msg = e ? (codes[e.code] || 'ERROR ' + e.code) : 'UNKNOWN ERROR';
    vNoFile.style.display = 'block';
    vNoFile.textContent = msg + ' — serve via HTTP: run python3 SCRIPTS/serve_timeline.py';
    vsNow.textContent = 'Cannot load video';
  });
  video.addEventListener('loadedmetadata', function() {
    vsNow.textContent = VIDEO_ALIGNMENT_VALID
      ? (VIDEO_ALIGNMENT_STATUS === 'validated' ? 'Ready' : 'Clock-aligned; anchor review pending') +
        ' (' + Math.round(video.duration) + 's) — click events or drag orange line'
      : 'Video alignment pending — timeline seeking is disabled';
    VIDEO_DURATIONS[videoIdx] = video.duration;
    renderVideoCoverage();
    if (VIDEO_URLS.length > 1) buildNextOffset(1);
  });
  video.addEventListener('waiting',  function() { vsNow.textContent = 'Buffering…'; });
  video.addEventListener('playing',  function() { vsNow.textContent = 'Playing'; });
  video.addEventListener('pause',    function() { vsNow.textContent = 'Paused'; });

  // Multi-part: build offset table incrementally after each part's metadata loads
  function buildNextOffset(i) {
    if (i >= VIDEO_URLS.length || VIDEO_OFFSETS.length > i) return;
    var tmp = document.createElement('video');
    tmp.preload = 'metadata';
    tmp.addEventListener('loadedmetadata', function() {
      VIDEO_DURATIONS[i] = tmp.duration;
      VIDEO_OFFSETS.push(VIDEO_OFFSETS[VIDEO_OFFSETS.length - 1] + tmp.duration);
      renderVideoCoverage();
      buildNextOffset(i + 1);
    });
    tmp.src = VIDEO_URLS[i];
  }
  video.addEventListener('ended', function() {
    if (videoIdx + 1 < VIDEO_URLS.length) {
      videoIdx++;
      video.src = VIDEO_URLS[videoIdx];
      video.play().catch(function(){});
    }
  });

  // ── Seek helpers ──────────────────────────────────────────────────────────
  function sessionSecToVideo(sec) {
    for (var i = VIDEO_OFFSETS.length - 1; i >= 0; i--) {
      if (sec >= VIDEO_OFFSETS[i] && sec <= VIDEO_OFFSETS[i] + VIDEO_DURATIONS[i]) {
        return { part: i, t: sec - VIDEO_OFFSETS[i] };
      }
    }
    return null;
  }

  function videoCurrentSessionSec() {
    return (VIDEO_OFFSETS[videoIdx] || 0) + (video.currentTime || 0);
  }

  // Pending seek target — set before awaiting events, cleared in seeked handler
  var seekTarget = null;

  // Step 3: seeked fired → now play (correct point is in buffer)
  video.addEventListener('seeked', function() {
    if (seekTarget === null) return;
    seekTarget = null;
    video.play().catch(function(e) {
      vsNow.textContent = 'Play blocked (' + e.name + ') — click the video player first';
    });
  });

  // Step 2: metadata ready → set currentTime (this triggers seeked)
  video.addEventListener('loadedmetadata', function() {
    if (seekTarget !== null) video.currentTime = seekTarget.t;
  });

  function seekTo(sessionSec) {
    if (!VIDEO_URLS.length) { vNoFile.style.display = 'block'; return; }
    if (sessionSec < 0) { vsNow.textContent = 'Pre-recording (' + Math.round(-sessionSec) + 's before rec start)'; return; }
    var loc = sessionSecToVideo(sessionSec);
    if (loc === null) { vsNow.textContent = 'No video coverage at this timeline time'; return; }

    if (loc.part !== videoIdx) {
      // Switch video part: set src, let loadedmetadata handle the seek
      videoIdx = loc.part;
      seekTarget = loc;
      video.src = VIDEO_URLS[videoIdx];
      // loadedmetadata → sets currentTime → seeked → play()
    } else if (video.readyState >= 1) {
      // Metadata already loaded: set currentTime directly → seeked → play()
      seekTarget = loc;
      video.currentTime = loc.t;
    } else {
      // Not loaded yet: set target, loadedmetadata will handle it
      seekTarget = loc;
    }
  }

  // ── Playhead drag → seek ──────────────────────────────────────────────────
  var draggingPh = false;
  tl.on('timechange',  function(p) { if (p.id === 'ph') draggingPh = true; });
  tl.on('timechanged', function(p) {
    if (p.id !== 'ph') return;
    draggingPh = false;
    var sec = (new Date(p.time).getTime() - VS_DATE.getTime()) / 1000;
    if (sec >= 0) seekTo(sec);
    else vsNow.textContent = 'Pre-recording';
  });

  // ── Video time → playhead sync ────────────────────────────────────────────
  function fmtTime(s) {
    var hh = Math.floor(s/3600), mm = Math.floor((s%3600)/60), ss = Math.floor(s%60);
    return ('0'+hh).slice(-2)+':'+('0'+mm).slice(-2)+':'+('0'+ss).slice(-2);
  }
  video.addEventListener('timeupdate', function() {
    if (!VIDEO_ALIGNMENT_VALID) return;
    if (draggingPh) return;
    var sessionSec = videoCurrentSessionSec();
    vtime.textContent = fmtTime(sessionSec);
    tl.setCustomTime(new Date(VS_DATE.getTime() + sessionSec * 1000), 'ph');
  });

  // ── Detail panel ──────────────────────────────────────────────────────────
  var dp = document.getElementById('dp');

  var FIELD_ORDER = [
    'task_id','checkpoint_id','topic','canonical_key','task','summary',
    'status','status_label','result_source','event_description',
    'declared_by','participant_message','synced_from_log_event_id','synced_wall_time','linked_log_text',
    'official_result','session_log_attempts','session_terminal_status','session_terminal_mismatch',
    'event_category','source','review_status','confidence','time_precision','actor',
    'wall_time','video_sec','video_sec_start','video_sec_end',
    'duration_sec','command','outcome','exit_code','duration_ms','timed_out',
    'test_result','initiator','output_length_bytes',
    'file_path','agent_type','autonomy_mode',
    'text','word_count','event_description',
    'command_short','command','attempt_count','prior_issue_count','matched_needle',
    'duration_ms','display_note',
    'active_file','active_panel','kiro_state','kiro_call_counter',
    'participant_behaviour_code','terminal_output_summary',
    'kiro_tasks_visible','kiro_actions_visible',
    'kiro_state_sequence','approval_interaction_observed','participant_observation',
    'linked_log_events','video_frames_reviewed_sec',
  ];

  function esc(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }
  function fmtVal(v) {
    if (v === null || v === undefined) return '<em style="color:var(--text-3)">—</em>';
    if (typeof v === 'boolean') return v
      ? '<span style="color:var(--green)">true</span>'
      : '<span style="color:var(--red)">false</span>';
    if (Array.isArray(v)) {
      if (!v.length) return '<em style="color:var(--text-3)">[]</em>';
      return '<ul style="margin:2px 0;padding-left:14px;color:var(--text-2)">' +
        v.map(function(x){return '<li>'+esc(typeof x==='object'?JSON.stringify(x):String(x))+'</li>';}).join('')+'</ul>';
    }
    if (typeof v === 'object')
      return Object.entries(v).map(function(kv){
        return '<span style="color:var(--text-3)">'+esc(kv[0])+':</span> '+esc(String(kv[1]));
      }).join(' &nbsp;');
    return esc(String(v));
  }

  function eventVideoSec(d) {
    if (d.synced_from_log_event_id !== undefined && d.timeline_sec_start !== undefined) return d.timeline_sec_start;
    if (d.timeline_sec_start !== undefined) return d.timeline_sec_start;
    if (d.video_sec !== undefined) return d.video_sec;
    if (d.video_sec_start !== undefined) return d.video_sec_start;
    var term = d.status_terminal_log;
    if (term && term.video_sec !== undefined) return term.video_sec;
    return null;
  }

  function showDetail(id) {
    var entry = RAW[id];
    if (!entry) return;
    var d = entry.data, src = entry.src;
    var cat = d.event_category || '—';
    var vsec = eventVideoSec(d);
    var srcLabel = d.source === 'both' ? '🎥 video + 📋 linked log'
                 : src === 'video' ? '🎥 video annotation'
                 : src === 'selected' ? '⏱ selected session evidence'
                 : d.event_category === 'checkpoint_status' ? '📋 official checkpoint'
                 : '📋 log-derived';

    var title = d.event_category === 'checkpoint_status'
      ? (d.task_id && d.topic
          ? d.task_id + (d.checkpoint_id && d.checkpoint_id !== 'CP' ? ' · ' + d.checkpoint_id : '') + ' ' + d.topic
          : (d.checkpoint || 'Checkpoint'))
      : cat;
    var html = '<div id="dp-title">' + esc(title);
    if (d.event_category === 'checkpoint_status' && d.status_label) {
      html += ' <span class="src-badge">' + esc(d.status_label) + '</span>';
    } else {
      html += ' <span class="src-badge">' + srcLabel + '</span>';
    }
    html += '</div>';

    if (d.event_category === 'checkpoint_status') {
      if (d.canonical_key) {
        html += '<div class="field"><div class="fk">Checkpoint key</div><div class="fv">' + esc(d.canonical_key) + '</div></div>';
      }
      if (d.summary) {
        html += '<div class="field"><div class="fk">Tests covered</div><div class="fv">' + esc(d.summary) + '</div></div>';
      }
      if (d.status_label) {
        html += '<div class="field"><div class="fk">Result</div><div class="fv">' + esc(d.status_label) + '</div></div>';
      }
      if (d.official_result) {
        var o = d.official_result;
        var parts = [];
        if (o.tests_run != null) parts.push(o.tests_run + ' tests');
        if (o.failures) parts.push(o.failures + ' failures');
        if (o.errors) parts.push(o.errors + ' errors');
        if (o.duration_seconds != null) parts.push(o.duration_seconds + 's');
        if (parts.length) {
          html += '<div class="field"><div class="fk">Official run</div><div class="fv">' + esc(parts.join(' · ')) + '</div></div>';
        }
        if (o.started_at) {
          html += '<div class="field"><div class="fk">Official run time</div><div class="fv">' + esc(o.started_at) + '</div></div>';
        }
      }
      if (d.session_terminal_mismatch) {
        html += '<div class="field"><div class="fk">Session note</div><div class="fv">In-session terminal outcome differed from the official post-session result.</div></div>';
      }
      if (d.session_log_attempts !== undefined) {
        html += '<div class="field"><div class="fk">In-session log matches</div><div class="fv">' + esc(String(d.session_log_attempts)) + '</div></div>';
      }
      if (d.wall_time) {
        html += '<div class="field"><div class="fk">Wall time</div><div class="fv">' + esc(d.wall_time) + '</div></div>';
      }
    }

    if (vsec !== null) {
      html += '<button class="seek-btn" onclick="seekTo('+vsec+')">▶ Seek to ' +
              (vsec < 0 ? 'pre-recording (' + Math.round(-vsec) + 's before)' : 'this event') + '</button>';
    }
    if (d.output_text) {
      html += '<div class="field"><div class="fk">Terminal output</div><div class="out">' + esc(d.output_text) + '</div></div>';
    }
    if (d.event_description) {
      html += '<div class="field"><div class="fk">Summary</div><div class="fv">' + esc(d.event_description) + '</div></div>';
    }
    var shown = {output_text:1,event_description:1,id:1,timestamp:1,pre_video:1,
                 canonical_key:1,summary:1,status_label:1,official_result:1,
                 session_log_attempts:1,session_terminal_mismatch:1,wall_time:1,
                 task_id:1,checkpoint_id:1,topic:1,task:1,result_source:1,status:1};
    FIELD_ORDER.forEach(function(k){
      if (shown[k] || !(k in d)) return; shown[k]=1;
      html += '<div class="field"><div class="fk">'+esc(k)+'</div><div class="fv">'+fmtVal(d[k])+'</div></div>';
    });
    Object.keys(d).forEach(function(k){
      if (shown[k]) return;
      html += '<div class="field"><div class="fk">'+esc(k)+'</div><div class="fv">'+fmtVal(d[k])+'</div></div>';
    });
    dp.innerHTML = html;
  }

  function activateItem(id) {
    showDetail(id);
    var entry = RAW[id];
    if (!entry) return;
    var vsec = eventVideoSec(entry.data);
    if (vsec === null) return;
    tl.setCustomTime(new Date(VS_DATE.getTime() + vsec * 1000), 'ph');
    if (!VIDEO_ALIGNMENT_VALID) { vsNow.textContent = 'Video alignment needs review'; return; }
    if (vsec >= 0) seekTo(vsec);
  }

  var hoverTip = document.getElementById('hover-tip');
  function showHover(props) {
    var id = props.item;
    if (id === null || id === undefined || !RAW[id]) { hoverTip.style.display = 'none'; return; }
    var d = RAW[id].data;
    var summary, when, heading;
    if (d.event_category === 'checkpoint_status') {
      heading = (d.task_id || '') + (d.checkpoint_id && d.checkpoint_id !== 'CP' ? ' · ' + d.checkpoint_id : '') + ' ' + (d.topic || '');
      heading = heading.trim() || d.checkpoint || 'Checkpoint';
      summary = (d.status_label || d.status || '');
      if (d.official_result && d.official_result.tests_run != null) {
        summary += ' · ' + d.official_result.tests_run + ' tests';
      } else if (d.summary) {
        summary += ' — ' + d.summary;
      }
      if (d.command_short) summary += '<br><span style="opacity:.85">' + esc(d.command_short) + '</span>';
      when = d.wall_time || '';
    } else {
      heading = d.event_category || 'Event';
      summary = d.event_description || d.text || d.command_short || d.command || d.file_path || d.event_category;
      when = d.wall_time || d.video_sec_start || d.video_sec || '';
    }
    hoverTip.innerHTML = '<b>' + esc(heading) + '</b>' +
      (when !== '' ? ' · ' + esc(when) : '') + '<br>' + (d.event_category === 'checkpoint_status' ? summary : esc(summary));
    hoverTip.style.display = 'block';
    var source = props.event || {};
    var pageX = props.pageX || source.pageX || source.clientX || 0;
    var pageY = props.pageY || source.pageY || source.clientY || 0;
    hoverTip.style.left = Math.min(pageX + 14, window.innerWidth - 360) + 'px';
    hoverTip.style.top = Math.min(pageY + 14, window.innerHeight - 90) + 'px';
  }
  // itemover/itemout are vis-timeline's item-specific events.  Generic mouse
  // events do not reliably contain an item id after the timeline redraws.
  tl.on('itemover', showHover);
  tl.on('itemout', function() { hoverTip.style.display = 'none'; });

  tl.on('click', function(props) {
    if (props.item !== null && props.item !== undefined) activateItem(props.item);
  });

  tl.on('select', function(props) {
    if (!props.items.length) return;
    var id = props.items[0];
    activateItem(id);
  });

  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      tl.setSelection([]);
      dp.innerHTML = '<div class="ph">Deselected.</div>';
    }
  });

  window.seekTo = seekTo;
});
</script>
</body>
</html>"""
    )

if __name__ == "__main__":
    main()
