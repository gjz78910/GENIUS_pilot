#!/usr/bin/env python3
"""Validate the fixed-window timestamp inventory for every GENIUS participant."""

import json
from datetime import datetime, timedelta
from pathlib import Path

OUTPUT = Path(__file__).parent / "output"
STARTS = {"ai-01": "09:00:00", **{f"ai-{n:02d}": "13:00:00" for n in range(2, 7)}}
DATE = "2026-06-09"


def main():
    failures = []
    for participant, wall_time in STARTS.items():
        data = json.loads((OUTPUT / f"{participant}_log_events.json").read_text())
        start = datetime.strptime(f"{DATE} {wall_time}", "%Y-%m-%d %H:%M:%S")
        end = start + timedelta(hours=2, minutes=30)
        if data.get("session_start_timestamp") != start.isoformat(timespec="milliseconds"):
            failures.append(f"{participant}: incorrect fixed start")
        if data.get("session_end_timestamp") != end.isoformat(timespec="milliseconds"):
            failures.append(f"{participant}: incorrect fixed end")
        raw = data.get("raw_timestamp_events", [])
        excluded = data.get("excluded_timestamps", [])
        inventory = data.get("timestamp_inventory", {})
        if inventory.get("discovered") != len(raw) + len(excluded):
            failures.append(f"{participant}: inventory count mismatch")
        for event in raw:
            stamp = datetime.fromisoformat(event["timestamp"])
            if not start <= stamp <= end or event.get("validity") != "in_window":
                failures.append(f"{participant}: invalid rendered raw timestamp")
                break
        for event in data.get("events", []):
            stamp = datetime.fromisoformat(event["timestamp"])
            if not start <= stamp <= end:
                failures.append(f"{participant}: invalid rendered derived timestamp")
                break
        for event in data.get("selected_timestamp_events", []):
            stamp = datetime.fromisoformat(event["timestamp"])
            if not start <= stamp <= end:
                failures.append(f"{participant}: invalid selected timestamp")
                break
        if any(event.get("validity") != "excluded_outside_study_window" for event in excluded):
            failures.append(f"{participant}: invalid exclusion status")

    ai01 = json.loads((OUTPUT / "ai-01_log_events.json").read_text())
    ai01_raw = ai01.get("raw_timestamp_events", [])
    if not any(event["source_file"] == "session/participant_state.json" for event in ai01_raw):
        failures.append("ai-01: missing participant-state anchor")
    if not any(event["timeline_group"] == "raw_terminal" and event["wall_time"] == "10:24:40"
               for event in ai01_raw):
        failures.append("ai-01: missing submission-terminal anchor")
    if not any(event["event_category"] == "submission_command_recorded"
               for event in ai01.get("selected_timestamp_events", [])):
        failures.append("ai-01: missing selected submission evidence")

    ai04 = json.loads((OUTPUT / "ai-04_log_events.json").read_text())
    if not any(event["source_file"] == "surveys/post_survey.json" for event in ai04.get("excluded_timestamps", [])):
        failures.append("ai-04: missing excluded late post-survey timestamp")

    if failures:
        raise SystemExit("Timestamp inventory validation failed:\n- " + "\n- ".join(failures))
    print("Timestamp inventory validation passed for ai-01 through ai-06.")


if __name__ == "__main__":
    main()
