#!/usr/bin/env python3
"""Verify that data is stored separately for each participant.

This script checks:
- All data files have participant IDs in their names
- No cross-contamination between participants
- File naming is consistent
- Required data files exist
"""

import json
import sys
from pathlib import Path
from collections import defaultdict


def find_data_files(data_dir="DATA_COLLECTION"):
    """Find all data collection files."""
    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"ERROR: Data directory not found: {data_dir}")
        return []
    
    # Find all JSON, JSONL, and MD files
    files = []
    for pattern in ["*.json", "*.jsonl", "*.md"]:
        files.extend(data_path.glob(pattern))
    
    return sorted(files)


def extract_participant_id(filename):
    """Extract participant ID from filename.
    
    Expected patterns:
    - system_info_<ID>.json
    - resource_usage_<ID>_<SESSION>.jsonl
    - survey_<ID>.md
    """
    name = filename.stem  # filename without extension
    
    # Pattern: <prefix>_<ID> or <prefix>_<ID>_<SESSION>
    parts = name.split('_')
    
    # Look for participant ID patterns
    # Usually the last part before session ID, or just the last part
    if len(parts) >= 2:
        # Check if last part looks like a session ID (SESSION1, SESSION2, etc.)
        if parts[-1].startswith('SESSION') or parts[-1].isdigit():
            # Second to last is likely the participant ID
            if len(parts) >= 3:
                return parts[-2]
        else:
            # Last part is the participant ID
            return parts[-1]
    
    return None


def verify_file_naming(files):
    """Verify file naming is consistent."""
    issues = []
    participant_files = defaultdict(list)
    
    for file in files:
        # Skip template files
        if 'template' in file.name.lower() or 'pre_experiment_survey' in file.name:
            continue
        
        # Skip backup directories
        if 'participant_backups' in str(file):
            continue
        
        participant_id = extract_participant_id(file)
        
        if participant_id:
            participant_files[participant_id].append(file)
        else:
            issues.append(f"⚠️  Could not extract participant ID from: {file.name}")
    
    return participant_files, issues


def check_cross_contamination(participant_files):
    """Check for cross-contamination between participants."""
    issues = []
    
    # Check if any files reference multiple participants
    for file in sum(participant_files.values(), []):
        try:
            if file.suffix == '.json':
                with open(file, 'r') as f:
                    data = json.load(f)
                    # Check if data contains participant IDs
                    data_str = json.dumps(data)
                    for pid in participant_files.keys():
                        if pid in data_str and pid != extract_participant_id(file):
                            issues.append(f"⚠️  Possible cross-contamination: {file.name} may contain data for participant {pid}")
        except (json.JSONDecodeError, IOError):
            # Skip files that can't be read
            pass
    
    return issues


def check_required_files(participant_id, data_dir="DATA_COLLECTION"):
    """Check if required data files exist for a participant."""
    data_path = Path(data_dir)
    required_patterns = [
        f"system_info_{participant_id}.json",
        f"survey_{participant_id}.md",
    ]
    
    missing = []
    for pattern in required_patterns:
        if not (data_path / pattern).exists():
            missing.append(pattern)
    
    return missing


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Verify data separation between participants"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="DATA_COLLECTION",
        help="Data collection directory (default: DATA_COLLECTION)"
    )
    parser.add_argument(
        "--participant-id",
        type=str,
        help="Check specific participant ID"
    )
    parser.add_argument(
        "--list-participants",
        action="store_true",
        help="List all participants found in data files"
    )
    
    args = parser.parse_args()
    
    print("Verifying data separation...")
    print("=" * 80)
    print()
    
    # Find all data files
    files = find_data_files(args.data_dir)
    if not files:
        print("No data files found.")
        return
    
    print(f"Found {len(files)} data files")
    print()
    
    # Verify file naming
    participant_files, naming_issues = verify_file_naming(files)
    
    if args.list_participants:
        print("Participants found in data files:")
        for pid in sorted(participant_files.keys()):
            file_count = len(participant_files[pid])
            print(f"  - {pid}: {file_count} files")
        print()
        return
    
    # Report naming issues
    if naming_issues:
        print("FILE NAMING ISSUES:")
        for issue in naming_issues:
            print(f"  {issue}")
        print()
    else:
        print("✅ File naming is consistent")
        print()
    
    # Check cross-contamination
    contamination_issues = check_cross_contamination(participant_files)
    
    if contamination_issues:
        print("CROSS-CONTAMINATION WARNINGS:")
        for issue in contamination_issues:
            print(f"  {issue}")
        print()
    else:
        print("✅ No cross-contamination detected")
        print()
    
    # Check specific participant or all
    if args.participant_id:
        participants_to_check = [args.participant_id]
    else:
        participants_to_check = sorted(participant_files.keys())
    
    if not participants_to_check:
        print("⚠️  No participants found in data files")
        return
    
    # Check required files for each participant
    print("REQUIRED FILES CHECK:")
    print("-" * 80)
    all_good = True
    
    for pid in participants_to_check:
        missing = check_required_files(pid, args.data_dir)
        file_count = len(participant_files.get(pid, []))
        
        if missing:
            print(f"❌ {pid}: Missing {len(missing)} required file(s)")
            for m in missing:
                print(f"     - {m}")
            all_good = False
        else:
            print(f"✅ {pid}: All required files present ({file_count} total files)")
    
    print()
    
    # Summary
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
    else:
        print()
        print("⚠️  Some issues found. Review warnings above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
