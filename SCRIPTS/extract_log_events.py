"""
Extract all annotatable events from Kiro logs for a given participant.
Produces output/ai-XX_log_events.json — the log-derived backbone of the annotation,
covering ~80% of session events with millisecond precision and zero video needed.

Usage:
    python extract_log_events.py --participant ai-01
    python extract_log_events.py --all
"""

import re
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import OrderedDict
from typing import Optional

BASE_DATA = Path.home() / "Documents/Projects/GENIUS_experiment_data"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

SESSION_START_WALL = {
    "ai-01": "09:00:00",
    "ai-02": "13:00:00",
    "ai-03": "13:00:00",
    "ai-04": "13:00:00",
    "ai-05": "13:00:00",
    "ai-06": "13:00:00",
}

TS_FMT = "%Y-%m-%d %H:%M:%S.%f"
DATE_PREFIX = "2026-06-09 "  # session date; update if needed
TIMESTAMP_RE = re.compile(
    r"20\d{2}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?"
)


def wall_str_to_sec(hms: str) -> float:
    h, m, s = map(int, hms.split(":"))
    return h * 3600 + m * 60 + s


def ts_to_sec(ts: str) -> float:
    dt = datetime.strptime(ts, TS_FMT)
    return dt.hour * 3600 + dt.minute * 60 + dt.second + dt.microsecond / 1e6


def video_sec(ts: str, video_start: float) -> float:
    return round(ts_to_sec(ts) - video_start, 3)


def wall_clock(ts: str) -> str:
    return ts[11:19]


def resolve_session_bounds(participant: str) -> dict:
    """Return the study-defined 2.5-hour analysis window."""
    start = datetime.strptime(DATE_PREFIX + SESSION_START_WALL[participant], "%Y-%m-%d %H:%M:%S")
    end = start + timedelta(hours=2, minutes=30)
    return {
        "session_start_timestamp": start.isoformat(timespec="milliseconds"),
        "session_start_source": "fixed_study_schedule",
        "session_end_timestamp": end.isoformat(timespec="milliseconds"),
        "session_end_source": "fixed_study_window_2h30m",
    }


def parse_collected_timestamp(value: str) -> Optional[datetime]:
    """Parse one complete session-date timestamp without accepting embedded text."""
    if not isinstance(value, str) or not TIMESTAMP_RE.fullmatch(value):
        return None
    try:
        return datetime.fromisoformat(value.replace(",", ".").replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def raw_group(path: Path, log_label: str = "") -> tuple[str, str]:
    """Classify a timestamped source into a visible raw-evidence track."""
    path_text = str(path)
    if "resource_usage" in path.name:
        return "raw_resources", "resource_sample"
    if "surveys" in path.parts:
        return "raw_survey", "survey_timestamp"
    if "task_checkpoints" in path.parts:
        return "raw_checkpoints", "checkpoint_timestamp"
    if "session" in path.parts:
        return "raw_session", "session_timestamp"
    if "[Terminal]" in log_label:
        return "raw_terminal", "kiro_terminal_record"
    if any(marker in log_label for marker in ("[WriteFile]", "[agent-controller]", "[ChatAgent]", "[Tool agent Action]", "[Execution]")):
        return "raw_kiro_activity", "kiro_activity_record"
    if "kiro" in path.parts:
        return "raw_kiro_internal", "kiro_internal_record"
    return "raw_session", "collected_timestamp"


def timestamp_event(participant: str, stamp: datetime, source_file: str,
                    source_locator: str, group: str, category: str,
                    detail: str, start: datetime, end: datetime) -> dict:
    valid = start <= stamp <= end
    return {
        "participant": participant,
        "timestamp": stamp.isoformat(timespec="milliseconds"),
        "wall_time": stamp.strftime("%H:%M:%S"),
        "video_sec": round((stamp - start).total_seconds(), 3),
        "source": "collected_timestamp_inventory",
        "source_file": source_file,
        "source_locator": source_locator,
        "event_category": category,
        "timeline_group": group,
        "detail": detail[:180],
        "validity": "in_window" if valid else "excluded_outside_study_window",
    }


def json_timestamp_events(participant: str, path: Path, root: Path,
                          start: datetime, end: datetime) -> list:
    """Return every complete timestamp scalar in a JSON or JSONL data source."""
    try:
        values = ([json.loads(line) for line in path.read_text(errors="replace").splitlines() if line.strip()]
                  if path.suffix == ".jsonl" else [json.loads(path.read_text(errors="replace"))])
    except (OSError, ValueError, json.JSONDecodeError):
        return []

    events = []
    source_file = str(path.relative_to(root))
    group, category = raw_group(path)

    def visit(value, locator):
        if isinstance(value, dict):
            for key, child in value.items():
                visit(child, locator + [str(key)])
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, locator + [str(index)])
        elif isinstance(value, str):
            stamp = parse_collected_timestamp(value)
            if stamp:
                events.append(timestamp_event(
                    participant, stamp, source_file, ".".join(locator), group,
                    category, value, start, end
                ))

    for line_number, value in enumerate(values, start=1):
        visit(value, ["line_%d" % line_number] if path.suffix == ".jsonl" else [])
    return events


def log_timestamp_events(participant: str, path: Path, root: Path,
                         start: datetime, end: datetime) -> list:
    """Return every line-leading timestamp in a Kiro log, never embedded metadata."""
    events = []
    source_file = str(path.relative_to(root))
    try:
        lines = path.read_text(errors="replace").splitlines()
    except OSError:
        return events
    for line_number, line in enumerate(lines, start=1):
        match = re.match(r"^\s*(%s)" % TIMESTAMP_RE.pattern, line)
        if not match:
            continue
        stamp = parse_collected_timestamp(match.group(1))
        if not stamp:
            continue
        labels = re.findall(r"\[[^]]+\]", line[len(match.group(0)):])
        label = labels[-1] if labels else ""
        group, category = raw_group(path, label)
        event = timestamp_event(
            participant, stamp, source_file, "line_%d" % line_number, group,
            category, line[len(match.group(0)):].strip(), start, end
        )
        event["submission_command_hint"] = (
            "store_participant_work.sh" in line or "git push -u origin" in line
        )
        events.append(event)
    return events


def build_timestamp_inventory(participant: str, bounds: dict) -> tuple[list, list]:
    """Inventory all supported collected timestamp records, excluding videos."""
    root = BASE_DATA / participant
    start = datetime.fromisoformat(bounds["session_start_timestamp"])
    end = datetime.fromisoformat(bounds["session_end_timestamp"])
    discovered = [
        timestamp_event(participant, start, "study_schedule", "start", "raw_session",
                        "session_window_start", "Fixed study start", start, end),
        timestamp_event(participant, end, "study_schedule", "end", "raw_session",
                        "session_window_end", "Fixed study end", start, end),
    ]
    for path in root.rglob("*"):
        if not path.is_file() or "videos" in path.parts or "chat_api" in path.parts:
            continue
        relative = path.relative_to(root)
        supported = (relative.parts[0] in {"session", "surveys", "task_checkpoints"} or
                     relative.parts[0] == "kiro")
        if not supported:
            continue
        if path.suffix in {".json", ".jsonl"}:
            discovered.extend(json_timestamp_events(participant, path, root, start, end))
        elif path.suffix == ".log" and "kiro" in path.parts:
            discovered.extend(log_timestamp_events(participant, path, root, start, end))
    valid = [event for event in discovered if event["validity"] == "in_window"]
    excluded = [event for event in discovered if event["validity"] != "in_window"]
    return valid, excluded


def select_research_timestamps(raw_events: list) -> list:
    """Keep only timing evidence that adds to the behavioural log backbone."""
    selected = []
    seen = set()

    def add(event, category, description, dedupe_timestamp=False):
        key = ((event["timestamp"], category) if dedupe_timestamp else
               (event["timestamp"], event["source_file"], event["source_locator"], category))
        if key in seen:
            return
        seen.add(key)
        selected.append({
            **event,
            "event_category": category,
            "event_description": description,
            "timeline_group": "session_lifecycle",
            "source": "selected_collected_evidence",
            "selection_reason": "adds session-boundary or submission evidence not represented by routine log tracks",
        })

    for event in raw_events:
        source = event["source_file"]
        locator = event["source_locator"]
        if event["event_category"] == "session_window_start":
            add(event, "study_session_start", "Fixed study session start")
        elif source == "surveys/pre_survey.json" and locator == "_metadata.generated_at":
            add(event, "pre_survey_completed", "Pre-experiment survey recorded")
        elif source == "surveys/post_survey.json" and locator == "_metadata.generated_at":
            add(event, "post_survey_completed", "Post-experiment survey recorded")
        elif source == "session/participant_state.json" and locator == "timestamp":
            add(event, "work_storage_recorded", "Participant work storage record created")
        elif source == "kiro/logs/Kiro_Logs.log" and event["event_category"] == "kiro_terminal_record":
            if event.get("submission_command_hint"):
                add(event, "submission_command_recorded", "Submission command recorded in Kiro terminal")
        elif (source == "kiro/logs/Kiro_Logs.log"
              and event["event_category"] == "kiro_internal_record"
              and "Disposed and cleaned up resources" in event.get("detail", "")):
            # Kiro writes many same-timestamp notification cleanup lines on
            # exit.  Retain only the one explicit service-cleanup milestone.
            add(event, "kiro_shutdown_recorded", "Kiro service cleanup recorded",
                dedupe_timestamp=True)

    return sorted(selected, key=lambda event: event["timestamp"])


# ── Kiro_Logs.log parser ──────────────────────────────────────────────────────

def parse_kiro_log(log_path: Path, video_start: float) -> list:
    events = []
    pending_cmd = None

    with open(log_path) as f:
        for line in f:
            line = line.rstrip()

            # ── Agent trigger ─────────────────────────────────────────────────
            m = re.match(
                r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+) \[info\] \[agent-controller\] "
                r"Triggered new agent: (\S+) \(autonomyMode=(\w+)\)",
                line
            )
            if m:
                ts, agent_type, mode = m.group(1), m.group(2), m.group(3)
                events.append({
                    "source": "kiro_log",
                    "event_category": "agent_trigger",
                    "actor": "kiro",
                    "confidence": "high",
                    "timestamp": ts,
                    "wall_time": wall_clock(ts),
                    "video_sec": video_sec(ts, video_start),
                    "agent_type": agent_type,
                    "autonomy_mode": mode,
                })
                continue

            # ── File write ───────────────────────────────────────────────────
            m = re.match(
                r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+) \[info\] \[WriteFile\] "
                r"complete write file: (.+)",
                line
            )
            if m:
                ts, fpath = m.group(1), m.group(2)
                fname = Path(fpath).name
                rel = fpath.replace("/home/participant/GENIUS_pilot/", "")
                events.append({
                    "source": "kiro_log",
                    "event_category": "file_write",
                    "actor": "kiro",
                    "confidence": "high",
                    "timestamp": ts,
                    "wall_time": wall_clock(ts),
                    "video_sec": video_sec(ts, video_start),
                    "file_path": rel,
                    "file_name": fname,
                })
                continue

            # ── Terminal command START ────────────────────────────────────────
            m = re.match(
                r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+) \[info\] \[Terminal\] "
                r"Executing command \{.*?\"command\":\"(.*?)\"",
                line
            )
            if m:
                ts, cmd = m.group(1), m.group(2)
                pending_cmd = {
                    "source": "kiro_log",
                    "event_category": "terminal_command",
                    "actor": "kiro",
                    "confidence": "high",
                    "timestamp": ts,
                    "wall_time": wall_clock(ts),
                    "video_sec": video_sec(ts, video_start),
                    "command": cmd,
                    "exit_code": None,
                    "output_length_bytes": None,
                    "duration_ms": None,
                    "timed_out": False,
                    "output_text": None,
                }
                events.append(pending_cmd)
                continue

            # ── Terminal command DONE ─────────────────────────────────────────
            m = re.match(
                r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+) \[info\] \[Terminal\] "
                r"execute terminal command done \{.*?\"exitCode\":(\d+).*?\"outputLength\":(\d+)",
                line
            )
            if m and pending_cmd:
                ts_done, exit_code, out_len = m.group(1), int(m.group(2)), int(m.group(3))
                pending_cmd["exit_code"] = exit_code
                pending_cmd["output_length_bytes"] = out_len
                pending_cmd["video_sec_end"] = video_sec(ts_done, video_start)
                try:
                    d = (datetime.strptime(ts_done, TS_FMT) -
                         datetime.strptime(pending_cmd["timestamp"], TS_FMT)).total_seconds()
                    pending_cmd["duration_ms"] = int(d * 1000)
                except Exception:
                    pass
                pending_cmd["outcome"] = "pass" if exit_code == 0 else (
                    "interrupted" if exit_code == 130 else "fail"
                )
                pending_cmd = None
                continue

            # ── Execution timeout ─────────────────────────────────────────────
            m = re.match(
                r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+) \[info\] \[Terminal\] "
                r"execution timeout",
                line
            )
            if m and pending_cmd:
                ts_done = m.group(1)
                pending_cmd["timed_out"] = True
                pending_cmd["outcome"] = "timeout"
                try:
                    d = (datetime.strptime(ts_done, TS_FMT) -
                         datetime.strptime(pending_cmd["timestamp"], TS_FMT)).total_seconds()
                    pending_cmd["duration_ms"] = int(d * 1000)
                except Exception:
                    pass
                pending_cmd = None
                continue

    return events


# ── Chat_API.log parser ───────────────────────────────────────────────────────

def extract_terminal_outputs(chat_log: Path) -> list:
    """
    Extract unique terminal output texts from Chat_API.log.
    Outputs appear as tool results embedded in JSON request bodies.
    Deduplicates by tail-of-output key (outputs repeat as context accumulates).
    Returns list in order of first appearance.
    """
    with open(chat_log, errors="replace") as f:
        content = f.read()

    # Pattern: text field containing "Output:\n...\nExit Code: N"
    pattern = r'Output:\\n(.*?)\\n\\nExit Code: (\d+)'
    seen = OrderedDict()
    for m in re.finditer(pattern, content):
        raw_output, exit_code = m.group(1), m.group(2)
        key = raw_output[-300:]  # tail as dedup key
        if key not in seen:
            text = raw_output.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"')
            seen[key] = {"output_text": text.strip(), "exit_code": int(exit_code)}

    return list(seen.values())


def _normalize_chat_content(raw: str) -> str:
    return raw.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"')


def _is_system_chat_segment(text: str) -> bool:
    lowered = text.lower()
    return (
        text.startswith("#")
        or lowered.startswith("you are an intent classifier")
        or lowered.startswith("you are operating in a workspace")
    )


def _user_segments_from_chat_content(raw: str) -> list:
    """Split one Chat_API userInputMessage into participant-authored segments."""
    text = _normalize_chat_content(raw).strip()
    parts = re.split(r"<EnvironmentContext>.*?</EnvironmentContext>", text, flags=re.DOTALL)
    segments = []
    for part in parts:
        part = part.strip()
        if part and not _is_system_chat_segment(part):
            segments.append(part)
    return segments


def conversation_order(chat_log: Path) -> list:
    """Return Kiro conversation IDs in first-seen order from Chat_API.log."""
    if not chat_log.exists():
        return []
    content = chat_log.read_text(errors="replace")
    seen = []
    for cid in re.findall(r'"conversationId":"([^"]+)"', content):
        if cid not in seen:
            seen.append(cid)
    return seen


def extract_participant_messages_from_sessions(participant: str, chat_log: Path) -> list:
    """
    Extract participant chat messages from kiro_session_*.json history.
    Session order follows conversationId first-seen order in Chat_API.log.
    """
    sessions_dir = BASE_DATA / participant / "kiro/sessions"
    if not sessions_dir.exists():
        return []

    by_id = {}
    for path in sessions_dir.glob("kiro_session_*.json"):
        with open(path, errors="replace") as f:
            data = json.load(f)
        sid = data.get("sessionId") or path.stem.replace("kiro_session_", "")
        if sid in by_id:
            continue
        msgs = []
        for entry in data.get("history", []):
            msg = entry.get("message") or {}
            if msg.get("role") != "user":
                continue
            texts = [
                c["text"] for c in msg.get("content", [])
                if c.get("type") == "text" and c.get("text", "").strip()
            ]
            text = "\n".join(texts).strip()
            if text:
                msgs.append(text)
        by_id[sid] = msgs

    order = conversation_order(chat_log)
    messages = []
    seen_ids = set()
    for sid in order:
        if sid in by_id:
            messages.extend(by_id[sid])
            seen_ids.add(sid)
    for sid, msgs in by_id.items():
        if sid not in seen_ids:
            messages.extend(msgs)
    return messages


def extract_participant_messages(chat_log: Path, agent_trigger_times: list = None):
    """
    Extract participant chat messages from Chat_API.log.
    These are in userInputMessage.content fields.
    """
    content = chat_log.read_text(errors="replace")

    messages = []
    pattern = r'"userInputMessage":\{"content":"([^"]{3,})"'
    seen = set()
    for m in re.finditer(pattern, content):
        for text in _user_segments_from_chat_content(m.group(1).strip()):
            if text not in seen and len(text) < 5000:
                seen.add(text)
                messages.append(text)

    return messages


# ── Match terminal outputs to commands ───────────────────────────────────────

def match_outputs_to_commands(events: list, outputs: list) -> None:
    """
    Attach output text to terminal_command events.
    Strategy: match in order — nth unique output → nth terminal command
    (because Chat_API.log captures outputs in execution order).
    Skip commands that timed out with no output (output_length_bytes <= 4).
    """
    cmds = [e for e in events if e["event_category"] == "terminal_command"]
    meaningful_cmds = [c for c in cmds if (c.get("output_length_bytes") or 0) > 10]

    for i, (cmd, out) in enumerate(zip(meaningful_cmds, outputs)):
        cmd["output_text"] = out["output_text"]
        # Parse test results from output
        cmd["test_result"] = parse_test_result(out["output_text"])


def parse_test_result(text: str):
    """Parse unittest output to extract test counts and outcome."""
    if not text:
        return None

    result = {"outcome": None, "ran": None, "failures": None, "errors": None}

    # "Ran N tests in Xs"
    m = re.search(r"Ran (\d+) tests? in", text)
    if m:
        result["ran"] = int(m.group(1))

    # "OK" or "FAILED (failures=N, errors=M)"
    if re.search(r"\nOK\s*$", text):
        result["outcome"] = "pass"
        result["failures"] = 0
        result["errors"] = 0
    elif re.search(r"FAILED", text):
        result["outcome"] = "fail"
        fm = re.search(r"failures=(\d+)", text)
        em = re.search(r"errors=(\d+)", text)
        result["failures"] = int(fm.group(1)) if fm else 0
        result["errors"] = int(em.group(1)) if em else 0
    elif "ImportError" in text or "ModuleNotFoundError" in text:
        result["outcome"] = "import_error"
    elif "TIMEOUT" in text:
        result["outcome"] = "timeout"
    elif result["ran"] is None:
        result["outcome"] = "other"
        # Try to extract key lines
        result["summary"] = text[-200:].strip()

    return result if result["outcome"] else None


# ── Annotate initiator (Kiro vs participant) for terminal commands ─────────────

def annotate_initiators(events: list) -> None:
    """
    Terminal commands preceded by an agent_trigger within 30s are Kiro-initiated.
    Commands with no preceding agent trigger (or >30s gap) are participant-typed.
    """
    agent_times = [e["video_sec"] for e in events if e["event_category"] == "agent_trigger"]
    for e in events:
        if e["event_category"] != "terminal_command":
            continue
        vt = e["video_sec"]
        # Check if any agent trigger fired within the last 120s
        recent = [t for t in agent_times if 0 <= vt - t <= 120]
        e["initiator"] = "kiro_proposed_participant_approved" if recent else "participant_typed"


# ── Summarize session timeline ────────────────────────────────────────────────

def build_summary(events: list) -> dict:
    cmds = [e for e in events if e["event_category"] == "terminal_command"]
    writes = [e for e in events if e["event_category"] == "file_write"]
    triggers = [e for e in events if e["event_category"] == "agent_trigger"]

    files_written = list(dict.fromkeys(e["file_path"] for e in writes))
    failed_cmds = [e for e in cmds if e.get("outcome") not in ("pass", None)]
    long_cmds = [e for e in cmds if (e.get("duration_ms") or 0) > 5000]

    return {
        "total_events": len(events),
        "agent_triggers": len(triggers),
        "terminal_commands": len(cmds),
        "commands_passed": len([c for c in cmds if c.get("outcome") == "pass"]),
        "commands_failed": len(failed_cmds),
        "commands_interrupted": len([c for c in cmds if c.get("outcome") == "interrupted"]),
        "commands_timeout": len([c for c in cmds if c.get("timed_out")]),
        "file_writes": len(writes),
        "unique_files_written": files_written,
        "long_running_commands": [
            {"command": e["command"][:80], "duration_s": e["duration_ms"] / 1000,
             "outcome": e.get("outcome"), "wall_time": e["wall_time"]}
            for e in long_cmds
        ],
        "notable_failures": [
            {"command": e["command"][:80], "outcome": e.get("outcome"),
             "duration_s": (e.get("duration_ms") or 0) / 1000, "wall_time": e["wall_time"]}
            for e in failed_cmds
        ],
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def process_participant(p: str):
    log_path = BASE_DATA / p / "kiro/logs/Kiro_Logs.log"
    chat_log = BASE_DATA / p / "kiro/chat_api/Chat_API.log"
    out_path = OUTPUT_DIR / f"{p}_log_events.json"

    bounds = resolve_session_bounds(p)
    # Keep the historical field name for consumers of the event JSON, but it
    # now denotes the study-session origin, not the recording origin.
    session_start = datetime.fromisoformat(bounds["session_start_timestamp"])
    video_start_wall = session_start.strftime("%H:%M:%S")
    video_start = (session_start.hour * 3600 + session_start.minute * 60 +
                   session_start.second + session_start.microsecond / 1e6)

    print(f"\n{'='*60}")
    print(f"Participant: {p}")
    print(f"  Study window: {bounds['session_start_timestamp']} to {bounds['session_end_timestamp']}")

    raw_timestamp_events, excluded_timestamps = build_timestamp_inventory(p, bounds)
    selected_timestamp_events = select_research_timestamps(raw_timestamp_events)
    print(f"  Timestamp inventory: {len(raw_timestamp_events)} in window, {len(excluded_timestamps)} excluded, {len(selected_timestamp_events)} selected")

    # Phase 1: parse Kiro log
    print("  Parsing Kiro_Logs.log...", end=" ")
    events = parse_kiro_log(log_path, video_start)
    print(f"{len(events)} events")

    # Phase 2: extract terminal outputs from Chat_API
    if chat_log.exists():
        print("  Extracting terminal outputs from Chat_API.log...", end=" ")
        outputs = extract_terminal_outputs(chat_log)
        print(f"{len(outputs)} unique outputs")
        match_outputs_to_commands(events, outputs)

        print("  Extracting participant messages...", end=" ")
        messages = extract_participant_messages_from_sessions(p, chat_log)
        message_source = "kiro_session"
        if not messages:
            messages = extract_participant_messages(chat_log)
            message_source = "chat_api_log"
        print(f"{len(messages)} candidate messages ({message_source})")
    else:
        print("  Chat_API.log not found — skipping output extraction")
        outputs = []
        messages = extract_participant_messages_from_sessions(p, chat_log)
        message_source = "kiro_session"

    # Phase 3: annotate initiators
    annotate_initiators(events)

    # Phase 4: build participant message events, timestamped from agent triggers
    # Each participant message triggers a new chat-agent; match in order
    trigger_times = sorted(
        [e for e in events if e["event_category"] == "agent_trigger"
         and e["agent_type"] == "chat-agent"],
        key=lambda e: e["video_sec"]
    )
    if len(messages) != len(trigger_times):
        print(f"  WARNING: {len(messages)} participant messages vs {len(trigger_times)} chat-agent triggers")

    for i, (msg, trigger) in enumerate(zip(messages, trigger_times)):
        # Message was sent just before the trigger (within a few seconds)
        events.append({
            "source": message_source,
            "event_category": "participant_message",
            "actor": "participant",
            "confidence": "high",
            "timestamp": trigger["timestamp"],
            "wall_time": trigger["wall_time"],
            "video_sec": trigger["video_sec"] - 2,  # ~2s before trigger fires
            "text": msg,
            "char_count": len(msg),
            "word_count": len(msg.split()),
            "message_index": i + 1,
            "followed_by_agent_trigger_at": trigger["wall_time"],
            "id": None,
        })

    window_start = datetime.fromisoformat(bounds["session_start_timestamp"])
    window_end = datetime.fromisoformat(bounds["session_end_timestamp"])
    excluded_log_events = []
    in_window_events = []
    for e in events:
        stamp = datetime.fromisoformat(e["timestamp"])
        if window_start <= stamp <= window_end:
            e["pre_video"] = False
            in_window_events.append(e)
        else:
            excluded_log_events.append({
                **e,
                "exclusion_reason": "outside_fixed_study_window",
            })
    events = in_window_events

    # Sort by video_sec
    events.sort(key=lambda e: e.get("video_sec", 0))

    # Add sequential IDs
    for i, e in enumerate(events):
        e["id"] = i + 1

    # Build output
    summary = build_summary(events)
    output = {
        "participant": p,
        "extracted_at": datetime.now().isoformat(),
        "video_start_wall": video_start_wall,
        "video_start_source": bounds["session_start_source"],
        **bounds,
        "raw_timestamp_events": raw_timestamp_events,
        "selected_timestamp_events": selected_timestamp_events,
        "excluded_timestamps": excluded_timestamps,
        "timestamp_inventory": {
            "discovered": len(raw_timestamp_events) + len(excluded_timestamps),
            "in_window": len(raw_timestamp_events),
            "excluded": len(excluded_timestamps),
        },
        "excluded_log_events": excluded_log_events,
        "summary": summary,
        "candidate_participant_messages": messages,
        "events": events,
    }

    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n  Summary:")
    print(f"    Agent triggers:    {summary['agent_triggers']}")
    print(f"    Terminal commands: {summary['terminal_commands']} "
          f"({summary['commands_passed']} pass, {summary['commands_failed']} fail, "
          f"{summary['commands_interrupted']} interrupted)")
    print(f"    File writes:       {summary['file_writes']} across {len(summary['unique_files_written'])} files")
    if summary["notable_failures"]:
        print(f"  Notable failures:")
        for f_ in summary["notable_failures"]:
            print(f"    [{f_['wall_time']}] {f_['outcome']} {f_['duration_s']:.1f}s  {f_['command'][:60]}")
    print(f"  → {out_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--participant", help="e.g. ai-01")
    parser.add_argument("--all", action="store_true", help="Process all participants")
    args = parser.parse_args()

    participants = list(SESSION_START_WALL.keys()) if args.all else [args.participant]
    for p in participants:
        if not p:
            parser.print_help()
            return
        log_path = BASE_DATA / p / "kiro/logs/Kiro_Logs.log"
        if not log_path.exists():
            print(f"  SKIP {p}: log not found at {log_path}")
            continue
        process_participant(p)


if __name__ == "__main__":
    main()
