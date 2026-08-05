"""
Legacy API-assisted frame annotation pipeline.

The default workflow is now the local, cost-controlled review queue in
``build_annotation_review_queue.py``.  It uses 5-second AVFoundation survey
frames plus log-derived windows, and never overwrites primary annotations.
This legacy mode remains available only when explicitly requested.

Usage:
    python annotate_video.py --participant ai-01
    python annotate_video.py --participant ai-01 --start 0 --end 600  # first 10 min only

Output:
    SCRIPTS/output/ai-01_annotation.json
"""

import base64
import json
import os
import re
import argparse
import time
import subprocess
import sys
from pathlib import Path
from datetime import datetime

BASE_DATA = Path.home() / "Documents/Projects/GENIUS_experiment_data"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Video start calibration ──────────────────────────────────────────────────
# Determined from first frame: screen shows wall clock which we match to log ts
VIDEO_START_WALL = {
    "ai-01": "09:04:00",
    "ai-02": "13:08:00",
    "ai-03": "13:31:00",
    "ai-04": "13:30:00",
    "ai-05": "13:42:00",
    "ai-06": "13:27:00",
}

def wall_str_to_sec(s):
    h, m, sec = map(int, s.split(":"))
    return h * 3600 + m * 60 + sec

# ── Frame extraction ─────────────────────────────────────────────────────────

def extract_frames(video_path: Path, participant: str,
                   start_sec=0, end_sec=None,
                   dense_interval=3, sparse_interval=15,
                   diff_threshold=0.025):
    """
    Legacy, API-assisted extractor. It uses event-anchored dense sampling and
    is not the default annotation path. Use build_annotation_review_queue.py
    for the research-led workflow: behavioural map first, sparse survey, then
    dense review only for viable episodes.
    Frame-diff filtered to drop near-duplicates.
    """
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError(
            "Legacy API mode requires opencv-python. Use the default local "
            "review-queue workflow instead."
        ) from exc
    log_path = BASE_DATA / participant / "kiro/logs/Kiro_Logs.log"
    video_start = wall_str_to_sec(VIDEO_START_WALL[participant])

    # Parse agent-trigger timestamps from Kiro log
    agent_video_times = set()
    with open(log_path) as f:
        for line in f:
            m = re.match(r'\d{4}-\d{2}-\d{2} (\d{2}):(\d{2}):(\d{2})', line)
            if not m:
                continue
            wall = int(m.group(1))*3600 + int(m.group(2))*60 + int(m.group(3))
            vt = wall - video_start
            if 'Triggered new agent' in line or 'Processing model response stream' in line:
                if vt >= 0:
                    agent_video_times.add(vt)

    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = int(total_frames / fps)
    end_sec = end_sec or duration

    # Build sample set
    sample_times = set()
    for t in agent_video_times:
        for dt in range(-45, 90, dense_interval):
            st = t + dt
            if start_sec <= st <= end_sec:
                sample_times.add(st)
    for t in range(start_sec, end_sec + 1, sparse_interval):
        sample_times.add(t)
    sample_times = sorted(sample_times)

    # Extract with diff filter
    frames = []
    prev_gray = None
    for t in sample_times:
        fn = int(t * fps)
        if fn >= total_frames:
            continue
        cap.set(cv2.CAP_PROP_POS_FRAMES, fn)
        ret, frame = cap.read()
        if not ret:
            continue
        gray = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (320, 192))
        if prev_gray is not None:
            diff = float(abs(gray.astype(int) - prev_gray.astype(int)).mean()) / 255.0
            if diff < diff_threshold:
                continue
        prev_gray = gray
        h, w = frame.shape[:2]
        resized = cv2.resize(frame, (1280, int(h * 1280 / w)))
        _, buf = cv2.imencode('.jpg', resized, [cv2.IMWRITE_JPEG_QUALITY, 82])
        frames.append({
            "video_sec": t,
            "wall_time": sec_to_wall(video_start + t),
            "b64": base64.b64encode(buf).decode()
        })
    cap.release()
    print(f"  Extracted {len(frames)} frames from {duration//60} min video")
    return frames

def sec_to_wall(total_sec):
    h = total_sec // 3600
    m = (total_sec % 3600) // 60
    s = total_sec % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

# ── Kiro log events ──────────────────────────────────────────────────────────

def load_log_events(participant: str) -> list:
    """Extract timestamped events from Kiro_Logs.log for context injection."""
    log_path = BASE_DATA / participant / "kiro/logs/Kiro_Logs.log"
    video_start = wall_str_to_sec(VIDEO_START_WALL[participant])
    events = []
    with open(log_path) as f:
        for line in f:
            m = re.match(r'(\d{4}-\d{2}-\d{2} (\d{2}):(\d{2}):(\d{2}))', line)
            if not m:
                continue
            h,mi,s = int(m.group(2)), int(m.group(3)), int(m.group(4))
            wall = h*3600 + mi*60 + s
            vt = wall - video_start
            rest = line[len(m.group(1)):].strip()
            if 'Triggered new agent' in rest:
                mode = re.search(r'autonomyMode=(\w+)', rest)
                events.append({"video_sec": vt, "type": "agent_triggered",
                               "mode": mode.group(1) if mode else "?"})
            elif '[Terminal] Executing command' in rest:
                cmd = re.search(r'Executing command: (.+)', rest)
                events.append({"video_sec": vt, "type": "terminal_command",
                               "command": cmd.group(1).strip() if cmd else "?"})
    return sorted(events, key=lambda e: e["video_sec"])

# ── Annotation prompt ─────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert HCI researcher annotating screen recordings of developers using an AI coding assistant (Kiro) in VS Code.

This legacy mode is not authorised to produce final timeline annotations. It may
only produce reconnaissance notes for a later research-led review.

For each frame, extract EVERY observable detail:
- Exact text of any participant message visible being typed or just sent
- Exact Kiro response text (summarise if long, but capture key content)
- Every file name visible in tabs, editor, or Kiro actions
- Every command visible in terminal
- Kiro credits number (bottom right of Kiro panel, e.g. "Kiro Pro 6.77")
- Kiro elapsed time if shown (e.g. "1m 49s")
- Wall clock time shown in top-right corner
- Whether "Waiting on your input" is visible and what buttons (Reject/Trust/Run)
- Whether Kiro is "Working..."
- What lines of code are visible (line numbers)
- Terminal output visible (test results, errors, git output)
- Any visual evidence of participant action (cursor position, text selection, mouse location)

Return a JSON object matching this exact schema:"""

FRAME_SCHEMA = {
    "video_sec": "integer — timestamp passed to you",
    "wall_time": "HH:MM:SS from screen top-right",
    "active_file": "filename in bold/selected tab",
    "active_panel": "one of: editor, terminal, kiro_chat, browser, file_explorer, split_view",
    "visible_code_lines": "e.g. '137-206' — line range visible in editor",
    "kiro_state": "one of: working, waiting_approval, showing_response, idle",
    "kiro_credits": "float e.g. 6.77 — from 'Kiro Pro X.XX' bottom right",
    "kiro_elapsed": "string e.g. '1m 49s' or null",
    "kiro_mode": "auto or model_name e.g. 'claude-opus-4.8'",
    "kiro_autopilot": "boolean — is Autopilot toggle on?",
    "kiro_current_tasks": [
        {"task_id": "e.g. 1.2", "description": "...", "status": "In Progress|Completed|Failed"}
    ],
    "kiro_actions_visible": [
        "e.g. 'Read file(s) routing.py test_routing.py'",
        "e.g. 'Accepted edits to test_routing.py'",
        "e.g. 'Task 1.2 Write unit tests... Status: Completed'"
    ],
    "kiro_response_text": "Key text from Kiro's response visible — exact quotes where short enough",
    "waiting_approval": {
        "visible": "boolean",
        "prompt_type": "run_command | accept_edit | trust_action | null",
        "proposed_command": "exact command string or null",
        "proposed_file": "filename or null",
        "buttons_visible": ["Reject", "Trust", "Run"]
    },
    "participant_message_visible": {
        "visible": "boolean",
        "text": "exact text if visible in input box or just sent",
        "state": "typing | just_sent | null"
    },
    "terminal_visible": "boolean",
    "terminal_last_command": "last command line visible e.g. 'python -m unittest ...'",
    "terminal_output_summary": "key output: test counts, pass/fail, errors, git output",
    "terminal_test_result": {
        "ran": "integer or null",
        "failures": "integer or null",
        "errors": "integer or null",
        "outcome": "OK | FAILED | ERROR | null"
    },
    "git_operation_visible": "e.g. 'git commit -m tasks 2 → 3 files, 243 insertions' or null",
    "file_tabs_open": ["list of filenames visible in tab bar"],
    "participant_behaviour_code": "one of: reading_kiro_response, reading_code, reading_terminal, typing_message, idle_watching_kiro, reviewing_diff, navigating_files, running_survey, away",
    "participant_reading_evidence": "what specifically they appear to be reading/doing",
    "cursor_location": "e.g. 'line 156 col 34 in test_routing.py' from status bar or null",
    "event_description": "1-2 sentence plain English description of what is happening at this exact moment"
}

# ── API annotation ────────────────────────────────────────────────────────────

def annotate_frame(client, frame: dict, log_context: str) -> dict:
    """Send one frame to Claude API and get structured annotation back."""
    schema_str = json.dumps(FRAME_SCHEMA, indent=2)
    user_content = [
        {
            "type": "text",
            "text": f"Annotate this frame at video_sec={frame['video_sec']} (wall time ~{frame['wall_time']}).\n\nKiro log context around this time:\n{log_context}\n\nReturn ONLY valid JSON matching this schema:\n{schema_str}"
        },
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": frame["b64"]
            }
        }
    ]
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}]
    )
    text = response.content[0].text.strip()
    # Strip markdown code fences if present
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    try:
        result = json.loads(text)
        result["video_sec"] = frame["video_sec"]
        return result
    except json.JSONDecodeError:
        return {"video_sec": frame["video_sec"], "parse_error": True, "raw": text[:500]}

def get_log_context(log_events: list, video_sec: int, window=120) -> str:
    """Get log events within ±window seconds of this frame for context."""
    nearby = [e for e in log_events if abs(e["video_sec"] - video_sec) <= window]
    if not nearby:
        return "No log events in this window."
    lines = []
    for e in nearby:
        rel = e["video_sec"] - video_sec
        prefix = f"t+{rel:+d}s" if rel != 0 else "NOW"
        if e["type"] == "agent_triggered":
            lines.append(f"  [{prefix}] Kiro agent triggered (mode={e['mode']})")
        elif e["type"] == "terminal_command":
            lines.append(f"  [{prefix}] Terminal: {e['command'][:80]}")
    return "\n".join(lines)

# ── Post-processing: merge frames into events ─────────────────────────────────

def merge_into_events(annotations: list) -> list:
    """
    Merge consecutive frames with same state into discrete events.
    A new event starts when: kiro_state changes, participant_behaviour_code changes,
    active_file changes, or waiting_approval.visible changes.
    """
    if not annotations:
        return []
    events = []
    current = annotations[0].copy()
    current["frames"] = [annotations[0]["video_sec"]]

    for ann in annotations[1:]:
        state_changed = (
            ann.get("kiro_state") != current.get("kiro_state") or
            ann.get("participant_behaviour_code") != current.get("participant_behaviour_code") or
            ann.get("active_file") != current.get("active_file") or
            ann.get("waiting_approval", {}).get("visible") != current.get("waiting_approval", {}).get("visible") or
            ann.get("terminal_test_result", {}).get("outcome") != current.get("terminal_test_result", {}).get("outcome")
        )
        if state_changed:
            current["video_sec_end"] = ann["video_sec"]
            current["duration_sec"] = ann["video_sec"] - current["video_sec"]
            events.append(current)
            current = ann.copy()
            current["frames"] = [ann["video_sec"]]
        else:
            current["frames"].append(ann["video_sec"])
            # Update with latest values (more recent frame is more informative)
            for k in ["kiro_credits", "kiro_elapsed", "terminal_output_summary",
                      "terminal_test_result", "kiro_response_text", "git_operation_visible"]:
                if ann.get(k):
                    current[k] = ann[k]

    current["video_sec_end"] = current["video_sec"] + 15
    current["duration_sec"] = 15
    events.append(current)
    return events

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--participant", required=True, help="e.g. ai-01")
    parser.add_argument(
        "--phase", choices=["review-queue", "legacy-api"], default="review-queue",
        help="review-queue is the sustainable local workflow (default)."
    )
    parser.add_argument("--interval", type=float, default=5.0,
                        help="Survey interval for review-queue mode (seconds).")
    parser.add_argument("--start", type=int, default=0, help="Start second in video")
    parser.add_argument("--end", type=int, default=None, help="End second in video")
    parser.add_argument("--resume", action="store_true", help="Resume from existing partial output")
    args = parser.parse_args()

    if args.phase == "review-queue":
        command = [sys.executable, str(Path(__file__).with_name("build_annotation_review_queue.py")),
                   "--participant", args.participant, "--interval", str(args.interval)]
        if args.start is not None or args.end is not None:
            if args.start is None or args.end is None:
                parser.error("--start and --end must be used together in review-queue mode")
            command += ["--start", str(args.start), "--end", str(args.end)]
        raise SystemExit(subprocess.call(command))

    p = args.participant
    output_path = OUTPUT_DIR / f"{p}_annotation.json"
    frames_cache = OUTPUT_DIR / f"{p}_frames_cache.json"

    # Find video
    video_dir = BASE_DATA / p / "videos"
    videos = list(video_dir.glob("*.mp4"))
    if not videos:
        print(f"No MP4 found in {video_dir}")
        return
    # Pick longest video for participants with multiple files
    video_path = max(videos, key=lambda v: v.stat().st_size)
    print(f"\n{'='*60}")
    print(f"Participant: {p}")
    print(f"Video: {video_path.name}")

    # Load or extract frames
    if args.resume and frames_cache.exists():
        print("  Loading cached frames...")
        with open(frames_cache) as f:
            frames = json.load(f)
    else:
        print("  Extracting frames...")
        frames = extract_frames(video_path, p, args.start, args.end)
        with open(frames_cache, "w") as f:
            # Save without b64 for inspection, full for processing
            json.dump([{k: v for k, v in fr.items() if k != "b64"} for fr in frames], f, indent=2)

    # Load log events for context
    log_events = load_log_events(p)
    print(f"  Loaded {len(log_events)} log events")

    # Load existing annotations if resuming
    done_secs = set()
    annotations = []
    if args.resume and output_path.exists():
        with open(output_path) as f:
            existing = json.load(f)
        annotations = existing.get("raw_frame_annotations", [])
        done_secs = {a["video_sec"] for a in annotations}
        print(f"  Resuming: {len(done_secs)} frames already annotated")

    # Annotate frames
    try:
        import anthropic
    except ImportError as exc:
        raise RuntimeError(
            "Legacy API mode requires the anthropic package. Use --phase review-queue."
        ) from exc
    client = anthropic.Anthropic()
    todo = [fr for fr in frames if fr["video_sec"] not in done_secs]
    print(f"  Annotating {len(todo)} frames...")

    for i, frame in enumerate(todo):
        print(f"  [{i+1}/{len(todo)}] t={frame['video_sec']}s ({frame['wall_time']})...", end=" ", flush=True)
        log_ctx = get_log_context(log_events, frame["video_sec"])
        try:
            ann = annotate_frame(client, frame, log_ctx)
            annotations.append(ann)
            status = ann.get("kiro_state", "?") + " | " + ann.get("participant_behaviour_code", "?")
            print(status)
        except Exception as e:
            print(f"ERROR: {e}")
            annotations.append({"video_sec": frame["video_sec"], "error": str(e)})

        # Save progress every 5 frames
        if (i + 1) % 5 == 0:
            _save(output_path, p, annotations, log_events)
        # Rate limit: 1 req/sec to avoid API throttling
        time.sleep(1.0)

    # Final save with merged events
    _save(output_path, p, annotations, log_events)
    print(f"\n  Done. Output: {output_path}")

def _save(output_path, participant, annotations, log_events):
    sorted_anns = sorted(annotations, key=lambda a: a.get("video_sec", 0))
    events = merge_into_events([a for a in sorted_anns if not a.get("error") and not a.get("parse_error")])
    output = {
        "participant": participant,
        "annotated_at": datetime.now().isoformat(),
        "total_frames_annotated": len(sorted_anns),
        "total_events": len(events),
        "log_events": log_events,
        "events": events,
        "raw_frame_annotations": sorted_anns
    }
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    main()
