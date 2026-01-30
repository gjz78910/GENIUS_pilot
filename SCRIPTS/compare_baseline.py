#!/usr/bin/env python3
"""Compare experiment runs against baseline.

This script establishes a baseline from manual participant runs and compares
AI-assisted runs against it to calculate efficiency improvements.
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def load_experiment_data(data_file):
    """Load experiment data from JSON file.
    
    Args:
        data_file: Path to experiment data JSON file
    
    Returns:
        Dictionary with experiment data
    """
    with open(data_file, "r") as f:
        return json.load(f)


def calculate_efficiency_metrics(baseline_data, comparison_data):
    """Calculate efficiency metrics comparing to baseline.
    
    Args:
        baseline_data: Baseline experiment data
        comparison_data: Comparison experiment data
    
    Returns:
        Dictionary with efficiency metrics
    """
    metrics = {}
    
    # Time efficiency
    if "task_timing" in baseline_data and "task_timing" in comparison_data:
        baseline_time = baseline_data["task_timing"].get("total_duration_seconds", 0)
        comparison_time = comparison_data["task_timing"].get("total_duration_seconds", 0)
        
        if baseline_time > 0:
            time_reduction = ((baseline_time - comparison_time) / baseline_time) * 100
            time_ratio = comparison_time / baseline_time
            metrics["time"] = {
                "baseline_seconds": baseline_time,
                "comparison_seconds": comparison_time,
                "reduction_percent": round(time_reduction, 2),
                "ratio": round(time_ratio, 3),
                "improvement": time_reduction > 0,
            }
    
    # Effort efficiency (from Git commits)
    if "git_activity" in baseline_data and "git_activity" in comparison_data:
        baseline_commits = baseline_data["git_activity"]["summary"].get("total_commits", 0)
        comparison_commits = comparison_data["git_activity"]["summary"].get("total_commits", 0)
        
        if baseline_commits > 0:
            commit_reduction = ((baseline_commits - comparison_commits) / baseline_commits) * 100
            metrics["effort"] = {
                "baseline_commits": baseline_commits,
                "comparison_commits": comparison_commits,
                "reduction_percent": round(commit_reduction, 2),
                "ratio": round(comparison_commits / baseline_commits, 3),
                "improvement": commit_reduction > 0,
            }
    
    # Code quality comparison
    if "code_quality" in baseline_data and "code_quality" in comparison_data:
        baseline_score = baseline_data["code_quality"].get("overall_quality_percent")
        comparison_score = comparison_data["code_quality"].get("overall_quality_percent")
        
        if baseline_score is not None and comparison_score is not None:
            quality_change = comparison_score - baseline_score
            metrics["quality"] = {
                "baseline_score": baseline_score,
                "comparison_score": comparison_score,
                "change": round(quality_change, 2),
                "improvement": quality_change > 0,
            }
    
    # Resource efficiency (CPU, memory)
    if "resource_usage" in baseline_data and "resource_usage" in comparison_data:
        # Calculate average CPU and memory usage
        baseline_cpu = calculate_average_cpu(baseline_data["resource_usage"])
        comparison_cpu = calculate_average_cpu(comparison_data["resource_usage"])
        
        baseline_memory = calculate_average_memory(baseline_data["resource_usage"])
        comparison_memory = calculate_average_memory(comparison_data["resource_usage"])
        
        if baseline_cpu and comparison_cpu:
            cpu_reduction = ((baseline_cpu - comparison_cpu) / baseline_cpu) * 100
            metrics["resource"] = {
                "cpu": {
                    "baseline_percent": baseline_cpu,
                    "comparison_percent": comparison_cpu,
                    "reduction_percent": round(cpu_reduction, 2),
                    "improvement": cpu_reduction > 0,
                },
            }
        
        if baseline_memory and comparison_memory:
            memory_reduction = ((baseline_memory - comparison_memory) / baseline_memory) * 100
            if "resource" not in metrics:
                metrics["resource"] = {}
            metrics["resource"]["memory"] = {
                "baseline_gb": baseline_memory,
                "comparison_gb": comparison_memory,
                "reduction_percent": round(memory_reduction, 2),
                "improvement": memory_reduction > 0,
            }
    
    return metrics


def calculate_average_cpu(resource_data):
    """Calculate average CPU usage from resource data.
    
    Args:
        resource_data: Resource usage data (file path or list of samples)
    
    Returns:
        Average CPU percentage or None
    """
    if isinstance(resource_data, str):
        # Assume it's a JSONL file path
        samples = []
        try:
            with open(resource_data, "r") as f:
                for line in f:
                    sample = json.loads(line)
                    if "cpu" in sample and "average" in sample["cpu"]:
                        samples.append(sample["cpu"]["average"])
        except Exception:
            return None
    elif isinstance(resource_data, list):
        samples = [
            s["cpu"]["average"] for s in resource_data
            if "cpu" in s and "average" in s["cpu"]
        ]
    else:
        return None
    
    return sum(samples) / len(samples) if samples else None


def calculate_average_memory(resource_data):
    """Calculate average memory usage from resource data.
    
    Args:
        resource_data: Resource usage data (file path or list of samples)
    
    Returns:
        Average memory in GB or None
    """
    if isinstance(resource_data, str):
        # Assume it's a JSONL file path
        samples = []
        try:
            with open(resource_data, "r") as f:
                for line in f:
                    sample = json.loads(line)
                    if "memory" in sample and "used_gb" in sample["memory"]:
                        samples.append(sample["memory"]["used_gb"])
        except Exception:
            return None
    elif isinstance(resource_data, list):
        samples = [
            s["memory"]["used_gb"] for s in resource_data
            if "memory" in s and "used_gb" in s["memory"]
        ]
    else:
        return None
    
    return sum(samples) / len(samples) if samples else None


def compare_baseline(baseline_file, comparison_file, output_file=None):
    """Compare experiment data against baseline.
    
    Args:
        baseline_file: Path to baseline experiment data JSON
        comparison_file: Path to comparison experiment data JSON
        output_file: Output JSON file path
    
    Returns:
        Dictionary with comparison results
    """
    # Load data
    baseline_data = load_experiment_data(baseline_file)
    comparison_data = load_experiment_data(comparison_file)
    
    # Calculate efficiency metrics
    efficiency = calculate_efficiency_metrics(baseline_data, comparison_data)
    
    # Create comparison report
    comparison = {
        "comparison_timestamp": datetime.now().isoformat(),
        "baseline_file": str(Path(baseline_file).absolute()),
        "comparison_file": str(Path(comparison_file).absolute()),
        "baseline_type": baseline_data.get("session_type", "manual"),
        "comparison_type": comparison_data.get("session_type", "ai-assisted"),
        "efficiency_metrics": efficiency,
        "summary": generate_summary(efficiency),
    }
    
    # Save to file if specified
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump(comparison, f, indent=2)
        
        print(f"Comparison report saved to: {output_path}")
    
    return comparison


def generate_summary(efficiency_metrics):
    """Generate human-readable summary.
    
    Args:
        efficiency_metrics: Dictionary with efficiency metrics
    
    Returns:
        String summary
    """
    summary_parts = []
    
    if "time" in efficiency_metrics:
        time_metric = efficiency_metrics["time"]
        if time_metric["improvement"]:
            summary_parts.append(
                f"Time reduced by {time_metric['reduction_percent']:.1f}% "
                f"({time_metric['baseline_seconds']:.1f}s → {time_metric['comparison_seconds']:.1f}s)"
            )
        else:
            summary_parts.append(
                f"Time increased by {abs(time_metric['reduction_percent']):.1f}% "
                f"({time_metric['baseline_seconds']:.1f}s → {time_metric['comparison_seconds']:.1f}s)"
            )
    
    if "effort" in efficiency_metrics:
        effort_metric = efficiency_metrics["effort"]
        if effort_metric["improvement"]:
            summary_parts.append(
                f"Commits reduced by {effort_metric['reduction_percent']:.1f}% "
                f"({effort_metric['baseline_commits']} → {effort_metric['comparison_commits']})"
            )
        else:
            summary_parts.append(
                f"Commits increased by {abs(effort_metric['reduction_percent']):.1f}% "
                f"({effort_metric['baseline_commits']} → {effort_metric['comparison_commits']})"
            )
    
    if "quality" in efficiency_metrics:
        quality_metric = efficiency_metrics["quality"]
        if quality_metric["improvement"]:
            summary_parts.append(
                f"Code quality improved by {quality_metric['change']:.1f}% "
                f"({quality_metric['baseline_score']:.1f}% → {quality_metric['comparison_score']:.1f}%)"
            )
        else:
            summary_parts.append(
                f"Code quality decreased by {abs(quality_metric['change']):.1f}% "
                f"({quality_metric['baseline_score']:.1f}% → {quality_metric['comparison_score']:.1f}%)"
            )
    
    if "resource" in efficiency_metrics:
        resource_metric = efficiency_metrics["resource"]
        if "cpu" in resource_metric:
            cpu_metric = resource_metric["cpu"]
            if cpu_metric["improvement"]:
                summary_parts.append(
                    f"CPU usage reduced by {cpu_metric['reduction_percent']:.1f}%"
                )
            else:
                summary_parts.append(
                    f"CPU usage increased by {abs(cpu_metric['reduction_percent']):.1f}%"
                )
        
        if "memory" in resource_metric:
            memory_metric = resource_metric["memory"]
            if memory_metric["improvement"]:
                summary_parts.append(
                    f"Memory usage reduced by {memory_metric['reduction_percent']:.1f}%"
                )
            else:
                summary_parts.append(
                    f"Memory usage increased by {abs(memory_metric['reduction_percent']):.1f}%"
                )
    
    return "\n".join(summary_parts) if summary_parts else "No metrics available for comparison"


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Compare experiment runs against baseline"
    )
    parser.add_argument(
        "baseline_file",
        type=str,
        help="Path to baseline experiment data JSON file"
    )
    parser.add_argument(
        "comparison_file",
        type=str,
        help="Path to comparison experiment data JSON file"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="DATA_COLLECTION/baseline_comparison.json",
        help="Output JSON file path"
    )
    
    args = parser.parse_args()
    
    # Compare baseline
    comparison = compare_baseline(
        args.baseline_file,
        args.comparison_file,
        output_file=args.output
    )
    
    # Print summary
    print("\n=== Baseline Comparison Summary ===")
    print(comparison["summary"])
    print(f"\nFull report saved to: {args.output}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
