#!/usr/bin/env python3
"""Verify that experiment data is separated per participant/session."""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional


@dataclass(frozen=True)
class FileMeta:
    """Parsed metadata from a data-collection filename."""

    participant_id: str
    session_id: str | None
    kind: str


# Ordered from specific to broad.
FILE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("task_checkpoint", re.compile(r"^Task1_cp[123]_(?P<pid>[A-Za-z0-9-]+)(?:_(?P<sid>.+))?$")),
    ("task_checkpoint", re.compile(r"^Task[23]_(?P<pid>[A-Za-z0-9-]+)(?:_(?P<sid>.+))?$")),
    ("resource_usage", re.compile(r"^resource_usage_(?P<pid>[A-Za-z0-9-]+)(?:_(?P<sid>.+))?$")),
    ("q_developer_metrics", re.compile(r"^q_developer_metrics_(?P<pid>[A-Za-z0-9-]+)(?:_(?P<sid>.+))?$")),
    ("kiro_metrics", re.compile(r"^kiro_metrics_(?P<pid>[A-Za-z0-9-]+)(?:_(?P<sid>.+))?$")),
    ("test_metrics", re.compile(r"^test_metrics_(?P<pid>[A-Za-z0-9-]+)(?:_(?P<sid>.+))?$")),
    ("task_timing", re.compile(r"^task_timing_(?P<pid>[A-Za-z0-9-]+)(?:_(?P<sid>.+))?$")),
    ("aggregated", re.compile(r"^aggregated_(?P<pid>[A-Za-z0-9-]+)(?:_(?P<sid>.+))?$")),
    ("system_info", re.compile(r"^system_info_(?P<pid>[A-Za-z0-9-]+)$")),
    ("survey", re.compile(r"^survey_(?P<pid>[A-Za-z0-9-]+)$")),
    ("git_activity", re.compile(r"^git_activity_(?P<pid>[A-Za-z0-9-]+)$")),
    ("cicd_metrics", re.compile(r"^cicd_metrics_(?P<pid>[A-Za-z0-9-]+)$")),
    ("code_quality", re.compile(r"^code_quality_(?P<pid>[A-Za-z0-9-]+)$")),
    ("energy_estimate", re.compile(r"^energy_estimate_(?P<pid>[A-Za-z0-9-]+)$")),
    ("carbon_footprint", re.compile(r"^carbon_footprint_(?P<pid>[A-Za-z0-9-]+)$")),
]


def parse_metadata(path: Path) -> Optional[FileMeta]:
    """Parse participant/session metadata from filename stem."""
    stem = path.stem
    for kind, pattern in FILE_PATTERNS:
        match = pattern.match(stem)
        if not match:
            continue
        participant_id = match.group("pid")
        session_id = match.groupdict().get("sid")
        return FileMeta(participant_id=participant_id, session_id=session_id, kind=kind)
    return None


def find_data_files(data_dir: str = "DATA_COLLECTION") -> List[Path]:
    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"ERROR: Data directory not found: {data_dir}")
        return []
    files: list[Path] = []
    for pattern in ("*.json", "*.jsonl", "*.md"):
        files.extend(data_path.glob(pattern))
    return sorted(files)


def verify_file_naming(
    files: Iterable[Path],
) -> tuple[Dict[str, List[Path]], Dict[Path, FileMeta], List[str]]:
    participant_files: Dict[str, List[Path]] = defaultdict(list)
    metadata_by_file: Dict[Path, FileMeta] = {}
    issues: List[str] = []

    for file_path in files:
        lower_name = file_path.name.lower()
        if "template" in lower_name or "pre_experiment_survey" in lower_name:
            continue

        metadata = parse_metadata(file_path)
        if metadata is None:
            # Keep auxiliary notes but flag unfamiliar naming.
            if lower_name.startswith("q-dev-chat"):
                continue
            issues.append(f"⚠️  Unrecognized data filename pattern: {file_path.name}")
            continue

        participant_files[metadata.participant_id].append(file_path)
        metadata_by_file[file_path] = metadata

    return participant_files, metadata_by_file, issues


def check_cross_contamination(metadata_by_file: Dict[Path, FileMeta]) -> List[str]:
    """Check explicit participant fields inside JSON files."""
    issues: List[str] = []
    for file_path, metadata in metadata_by_file.items():
        if file_path.suffix != ".json":
            continue
        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                content = json.load(handle)
        except Exception:
            continue

        if isinstance(content, dict):
            explicit_participant = content.get("participant_id")
            if explicit_participant and explicit_participant != metadata.participant_id:
                issues.append(
                    "⚠️  Participant ID mismatch: "
                    f"{file_path.name} filename={metadata.participant_id}, json={explicit_participant}"
                )
    return issues


def check_required_files(participant_id: str, data_dir: str = "DATA_COLLECTION") -> List[str]:
    data_path = Path(data_dir)
    missing = []
    if not (data_path / f"system_info_{participant_id}.json").exists():
        missing.append(f"system_info_{participant_id}.json")
    # Accept survey as .json (from HTML form) or .md (legacy manual fill)
    if not (data_path / f"survey_{participant_id}.json").exists() and \
       not (data_path / f"survey_{participant_id}.md").exists():
        missing.append(f"survey_{participant_id}.json")
    return missing


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Verify data separation between participants"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="DATA_COLLECTION",
        help="Data collection directory (default: DATA_COLLECTION)",
    )
    parser.add_argument(
        "--participant-id",
        type=str,
        help="Check specific participant ID",
    )
    parser.add_argument(
        "--list-participants",
        action="store_true",
        help="List all participants found in data files",
    )
    args = parser.parse_args()

    print("Verifying data separation...")
    print("=" * 80)
    print()

    files = find_data_files(args.data_dir)
    if not files:
        print("No data files found.")
        return 1

    print(f"Found {len(files)} data files")
    print()

    participant_files, metadata_by_file, naming_issues = verify_file_naming(files)

    if args.list_participants:
        print("Participants found in data files:")
        for participant_id in sorted(participant_files.keys()):
            print(f"  - {participant_id}: {len(participant_files[participant_id])} files")
        print()
        return 0

    if naming_issues:
        print("FILE NAMING ISSUES:")
        for issue in naming_issues:
            print(f"  {issue}")
        print()
    else:
        print("✅ File naming is consistent")
        print()

    contamination_issues = check_cross_contamination(metadata_by_file)
    if contamination_issues:
        print("CROSS-CONTAMINATION WARNINGS:")
        for issue in contamination_issues:
            print(f"  {issue}")
        print()
    else:
        print("✅ No cross-contamination detected")
        print()

    if args.participant_id:
        participants_to_check = [args.participant_id]
    else:
        participants_to_check = sorted(participant_files.keys())

    if not participants_to_check:
        print("⚠️  No participants found in data files")
        return 1

    print("REQUIRED FILES CHECK:")
    print("-" * 80)
    all_good = True

    for participant_id in participants_to_check:
        missing = check_required_files(participant_id, args.data_dir)
        file_count = len(participant_files.get(participant_id, []))
        if missing:
            print(f"❌ {participant_id}: Missing {len(missing)} required file(s)")
            for item in missing:
                print(f"     - {item}")
            all_good = False
        else:
            print(f"✅ {participant_id}: All required files present ({file_count} total files)")

    print()
    print("=" * 80)
    print("SUMMARY:")
    print(f"  Total participants: {len(participant_files)}")
    print(f"  Total data files: {len(files)}")
    print(f"  Naming issues: {len(naming_issues)}")
    print(f"  Contamination warnings: {len(contamination_issues)}")

    if all_good and not naming_issues and not contamination_issues:
        print()
        print("✅ All checks passed! Data is properly separated.")
        return 0

    print()
    print("⚠️  Some issues found. Review warnings above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
