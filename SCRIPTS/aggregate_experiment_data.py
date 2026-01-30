#!/usr/bin/env python3
"""Aggregate all experiment data into a single file.

This script combines data from all collection sources into a unified format
for analysis and reporting.
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def load_json_file(file_path):
    """Load JSON file, return None if not found.
    
    Args:
        file_path: Path to JSON file
    
    Returns:
        Dictionary or None
    """
    path = Path(file_path)
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    return None


def load_jsonl_file(file_path):
    """Load JSONL file, return list of samples.
    
    Args:
        file_path: Path to JSONL file
    
    Returns:
        List of dictionaries or None
    """
    path = Path(file_path)
    if path.exists():
        samples = []
        with open(path, "r") as f:
            for line in f:
                if line.strip():
                    samples.append(json.loads(line))
        return samples
    return None


def aggregate_experiment_data(
    participant_id,
    session_id=None,
    data_dir="DATA_COLLECTION",
    output_file=None
):
    """Aggregate all experiment data for a participant.
    
    Args:
        participant_id: Participant ID
        session_id: Session ID (optional)
        data_dir: Directory containing data files
        output_file: Output JSON file path
    
    Returns:
        Dictionary with aggregated data
    """
    data_dir = Path(data_dir)
    
    # Build file paths
    file_patterns = {
        "system_info": f"system_info_{participant_id}.json",
        "task_timing": f"task_timing_{participant_id}.json" if not session_id else f"task_timing_{participant_id}_{session_id}.json",
        "git_activity": f"git_activity_{participant_id}.json",
        "cicd_metrics": f"cicd_metrics_{participant_id}.json",
        "q_developer_metrics": f"q_developer_metrics_{participant_id}.json" if not session_id else f"q_developer_metrics_{participant_id}_{session_id}.json",
        "test_metrics": f"test_metrics_{participant_id}.json" if not session_id else f"test_metrics_{participant_id}_{session_id}.json",
        "code_quality": f"code_quality_{participant_id}.json",
        "energy_estimate": f"energy_estimate_{participant_id}.json",
        "carbon_footprint": f"carbon_footprint_{participant_id}.json",
        "resource_usage": f"resource_usage_{participant_id}.jsonl" if not session_id else f"resource_usage_{participant_id}_{session_id}.jsonl",
    }
    
    # Load all available data
    aggregated = {
        "aggregation_timestamp": datetime.now().isoformat(),
        "participant_id": participant_id,
        "session_id": session_id,
        "data_sources": {},
        "data": {},
    }
    
    for key, filename in file_patterns.items():
        file_path = data_dir / filename
        if file_path.exists():
            if key == "resource_usage":
                data = load_jsonl_file(file_path)
            else:
                data = load_json_file(file_path)
            
            if data is not None:
                aggregated["data"][key] = data
                aggregated["data_sources"][key] = str(file_path)
    
    # Add summary statistics
    aggregated["summary"] = generate_summary(aggregated["data"])
    
    # Save to file if specified
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump(aggregated, f, indent=2)
        
        print(f"Aggregated data saved to: {output_path}")
    
    return aggregated


def generate_summary(data):
    """Generate summary statistics from aggregated data.
    
    Args:
        data: Dictionary with all data sources
    
    Returns:
        Dictionary with summary statistics
    """
    summary = {}
    
    # Task timing summary
    if "task_timing" in data:
        timing = data["task_timing"]
        if "experiment_info" in timing:
            summary["total_duration_seconds"] = timing["experiment_info"].get("total_duration_seconds", 0)
            summary["total_tasks"] = timing["experiment_info"].get("total_tasks", 0)
    
    # Git activity summary
    if "git_activity" in data:
        git = data["git_activity"]
        if "summary" in git:
            summary["total_commits"] = git["summary"].get("total_commits", 0)
            summary["commits_per_hour"] = git["summary"].get("commits_per_hour", 0)
    
    # Code quality summary
    if "code_quality" in data:
        quality = data["code_quality"]
        summary["code_quality_score"] = quality.get("overall_quality_percent")
        summary["code_files"] = quality.get("code_statistics", {}).get("total_files", 0)
    
    # Energy summary
    if "energy_estimate" in data:
        energy = data["energy_estimate"]
        summary["total_energy_kwh"] = energy.get("total_energy", {}).get("kwh")
    
    # Carbon footprint summary
    if "carbon_footprint" in data:
        carbon = data["carbon_footprint"]
        summary["total_emissions_kg_co2"] = carbon.get("total", {}).get("emissions_kg_co2")
    
    # Q Developer usage summary
    if "q_developer_metrics" in data:
        q_dev = data["q_developer_metrics"]
        if "data" in q_dev:
            summary["ai_queries"] = q_dev["data"].get("queries", 0)
            summary["ai_suggestions_accepted"] = q_dev["data"].get("suggestions_accepted", 0)
            summary["ai_suggestions_rejected"] = q_dev["data"].get("suggestions_rejected", 0)
    
    return summary


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Aggregate all experiment data into a single file"
    )
    parser.add_argument(
        "participant_id",
        type=str,
        help="Participant ID"
    )
    parser.add_argument(
        "--session-id",
        type=str,
        help="Session ID (optional)"
    )
    parser.add_argument(
        "-d", "--data-dir",
        type=str,
        default="DATA_COLLECTION",
        help="Data collection directory (default: DATA_COLLECTION)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Output JSON file path (default: DATA_COLLECTION/aggregated_<participant_id>.json)"
    )
    
    args = parser.parse_args()
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        if args.session_id:
            output_path = f"{args.data_dir}/aggregated_{args.participant_id}_{args.session_id}.json"
        else:
            output_path = f"{args.data_dir}/aggregated_{args.participant_id}.json"
    
    # Aggregate data
    aggregated = aggregate_experiment_data(
        args.participant_id,
        session_id=args.session_id,
        data_dir=args.data_dir,
        output_file=output_path
    )
    
    # Print summary
    print(f"\n=== Aggregated Data Summary ===")
    print(f"Participant ID: {aggregated['participant_id']}")
    if aggregated['session_id']:
        print(f"Session ID: {aggregated['session_id']}")
    print(f"\nData sources found: {len(aggregated['data'])}")
    for key in aggregated['data'].keys():
        print(f"  - {key}")
    
    if aggregated['summary']:
        print(f"\nSummary:")
        for key, value in aggregated['summary'].items():
            if value is not None:
                print(f"  {key}: {value}")
    
    print(f"\nFull data saved to: {output_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
