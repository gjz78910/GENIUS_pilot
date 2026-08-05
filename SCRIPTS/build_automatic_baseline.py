#!/usr/bin/env python3
"""Create log-only annotation manifests after extract_log_events.py has run."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

PARTICIPANTS = [f"ai-{number:02d}" for number in range(1, 7)]
OUTPUT = Path(__file__).parent / "output"
DATA = Path("/Users/k2589922/Documents/Projects/GENIUS_experiment_data")

# ai-01 has no capture timestamp in its file name; its start is established
# from the reviewed first-frame clock.  The remaining recordings embed the
# local machine wall-clock value in their filenames.  Although it ends in Z,
# the ai-02 message anchors show it must not be converted from UTC.
MANUAL_VIDEO_START = {"ai-01": "09:04:00"}
VIDEO_FILENAME_TIMESTAMP = re.compile(r"_(\d{8}T\d{6}Z)\.mp4$")
VALIDATED_VIDEO_ALIGNMENT = {
    "ai-02": (
        "Filename time is local wall clock (despite the Z suffix), validated "
        "by visible Part-1 chat anchors: the 13:29:18 'how to run the tests?' "
        "message at video t≈2717s and the 13:34:35 benchmark-test request at t≈3034s."
    ),
}


def recording_start_from_filename(path: Path) -> Optional[str]:
    match = VIDEO_FILENAME_TIMESTAMP.search(path.name)
    if not match:
        return None
    return datetime.strptime(match.group(1), "%Y%m%dT%H%M%SZ").strftime("%H:%M:%S")


def main():
    for participant in PARTICIPANTS:
        log_path = OUTPUT / f"{participant}_log_events.json"
        if not log_path.exists():
            raise SystemExit(f"Missing {log_path}; run extract_log_events.py --all first.")
        log_data = json.loads(log_path.read_text())
        videos = sorted((DATA / participant / "videos").glob("*.mp4"))
        part_starts = [recording_start_from_filename(path) for path in videos]
        recording_start = next((start for start in part_starts if start),
                               MANUAL_VIDEO_START.get(participant, "unknown"))
        has_filename_timestamps = any(part_starts)
        alignment_validated = participant in VALIDATED_VIDEO_ALIGNMENT
        alignment_source = ("recording filename local wall-clock timestamp (candidate; requires event-anchor validation)"
                            if has_filename_timestamps else "reviewed first-frame clock reference")
        ann_path = OUTPUT / f"{participant}_annotation.json"
        existing_events = []
        if ann_path.exists():
            existing = json.loads(ann_path.read_text())
            existing_events = [
                event for event in existing.get("events", [])
                if event.get("event_category") != "video_state_observation"
                and event.get("review_status") in {None, "final_episode"}
            ]
        payload = {
            "participant": participant,
            "annotation_method": ("research_led_episode_review_v2" if existing_events
                                  else "automatic_log_derived_baseline_v1"),
            "annotated_at": datetime.now().isoformat(timespec="seconds"),
            "video_start_wall": recording_start,
            "video_alignment_status": ("validated" if alignment_validated or participant == "ai-01" else
                                       "clock_aligned" if has_filename_timestamps else
                                       "validated"),
            "video_alignment_evidence": (VALIDATED_VIDEO_ALIGNMENT.get(participant) or
                f"Placed using {alignment_source}; macOS filesystem creation dates are export/copy metadata."),
            "notes": (
                "Log-derived events live in ai-XX_log_events.json. "
                "This file holds reviewed behavioural episodes only."
                if existing_events else
                "This manifest intentionally contains no video behavioural annotations. "
                "The timeline's factual backbone is ai-XX_log_events.json; recording "
                "coverage is placed using the local wall-clock value embedded in the filename. "
                "It requires visible log-anchor validation before it supports event-level seeking or analysis."
            ),
            "video_parts": [
                {"part": index + 1, "file": path.name,
                 "timeline_start_wall": part_starts[index] if part_starts[index] else (
                     recording_start if index == 0 else None),
                 "timing_status": ("validated_local_filename_clock" if alignment_validated and part_starts[index]
                                   else "clock_aligned_local_filename" if part_starts[index]
                                   else "validated_first_frame" if index == 0
                                   else "sequential_after_validated_part")}
                for index, path in enumerate(videos)
            ],
            "events": existing_events,
        }
        ann_path.write_text(json.dumps(payload, indent=2) + "\n")
        print(f"Wrote {participant}: {len(videos)} recording part(s), {len(existing_events)} behavioural video event(s)")


if __name__ == "__main__":
    main()
