#!/usr/bin/env python3
"""Generate success criteria report comparing manual vs AI-assisted runs.

This script generates a comprehensive report comparing efficiency, quality,
scalability, sustainability, and governance metrics.
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def load_comparison_data(comparison_file):
    """Load baseline comparison data.
    
    Args:
        comparison_file: Path to baseline comparison JSON file
    
    Returns:
        Dictionary with comparison data
    """
    with open(comparison_file, "r") as f:
        return json.load(f)


def load_aggregated_data(data_file):
    """Load aggregated experiment data.
    
    Args:
        data_file: Path to aggregated data JSON file
    
    Returns:
        Dictionary with aggregated data
    """
    with open(data_file, "r") as f:
        return json.load(f)


def calculate_efficiency_metrics(baseline_data, ai_data):
    """Calculate efficiency metrics.
    
    Args:
        baseline_data: Baseline (manual) aggregated data
        ai_data: AI-assisted aggregated data
    
    Returns:
        Dictionary with efficiency metrics
    """
    efficiency = {}
    
    # Time efficiency
    baseline_time = baseline_data.get("summary", {}).get("total_duration_seconds", 0)
    ai_time = ai_data.get("summary", {}).get("total_duration_seconds", 0)
    
    if baseline_time > 0:
        time_reduction = ((baseline_time - ai_time) / baseline_time) * 100
        efficiency["time"] = {
            "baseline_seconds": baseline_time,
            "ai_seconds": ai_time,
            "reduction_percent": round(time_reduction, 2),
            "improvement": time_reduction > 0,
        }
    
    # Effort efficiency (commits)
    baseline_commits = baseline_data.get("summary", {}).get("total_commits", 0)
    ai_commits = ai_data.get("summary", {}).get("total_commits", 0)
    
    if baseline_commits > 0:
        commit_reduction = ((baseline_commits - ai_commits) / baseline_commits) * 100
        efficiency["effort"] = {
            "baseline_commits": baseline_commits,
            "ai_commits": ai_commits,
            "reduction_percent": round(commit_reduction, 2),
            "improvement": commit_reduction > 0,
        }
    
    # Cost efficiency (estimated from time and resources)
    baseline_energy = baseline_data.get("summary", {}).get("total_energy_kwh", 0)
    ai_energy = ai_data.get("summary", {}).get("total_energy_kwh", 0)
    
    if baseline_energy > 0:
        energy_reduction = ((baseline_energy - ai_energy) / baseline_energy) * 100
        efficiency["cost"] = {
            "baseline_energy_kwh": baseline_energy,
            "ai_energy_kwh": ai_energy,
            "reduction_percent": round(energy_reduction, 2),
            "improvement": energy_reduction > 0,
        }
    
    return efficiency


def calculate_quality_metrics(baseline_data, ai_data):
    """Calculate quality metrics.
    
    Args:
        baseline_data: Baseline aggregated data
        ai_data: AI-assisted aggregated data
    
    Returns:
        Dictionary with quality metrics
    """
    quality = {}
    
    # Code quality score
    baseline_score = baseline_data.get("summary", {}).get("code_quality_score")
    ai_score = ai_data.get("summary", {}).get("code_quality_score")
    
    if baseline_score is not None and ai_score is not None:
        score_change = ai_score - baseline_score
        quality["code_quality"] = {
            "baseline_score": baseline_score,
            "ai_score": ai_score,
            "change": round(score_change, 2),
            "improvement": score_change > 0,
        }
    
    # Defect rates (from test results)
    baseline_data_sources = baseline_data.get("data", {})
    ai_data_sources = ai_data.get("data", {})
    
    if "test_metrics" in baseline_data_sources and "test_metrics" in ai_data_sources:
        baseline_tests = baseline_data_sources["test_metrics"]
        ai_tests = ai_data_sources["test_metrics"]
        
        baseline_failures = baseline_tests.get("test_statistics", {}).get("failures", 0)
        baseline_total = baseline_tests.get("test_statistics", {}).get("tests_run", 0)
        baseline_defect_rate = (baseline_failures / baseline_total * 100) if baseline_total > 0 else 0
        
        ai_failures = ai_tests.get("test_statistics", {}).get("failures", 0)
        ai_total = ai_tests.get("test_statistics", {}).get("tests_run", 0)
        ai_defect_rate = (ai_failures / ai_total * 100) if ai_total > 0 else 0
        
        quality["defect_rate"] = {
            "baseline_percent": round(baseline_defect_rate, 2),
            "ai_percent": round(ai_defect_rate, 2),
            "change": round(ai_defect_rate - baseline_defect_rate, 2),
            "improvement": ai_defect_rate < baseline_defect_rate,
        }
    
    return quality


def calculate_scalability_metrics(baseline_data, ai_data):
    """Calculate scalability metrics.
    
    Args:
        baseline_data: Baseline aggregated data
        ai_data: AI-assisted aggregated data
    
    Returns:
        Dictionary with scalability metrics
    """
    scalability = {}
    
    # Performance across test sizes (from test metrics)
    baseline_data_sources = baseline_data.get("data", {})
    ai_data_sources = ai_data.get("data", {})
    
    if "test_metrics" in baseline_data_sources and "test_metrics" in ai_data_sources:
        baseline_tests = baseline_data_sources["test_metrics"]
        ai_tests = ai_data_sources["test_metrics"]
        
        baseline_duration = baseline_tests.get("execution", {}).get("duration_seconds", 0)
        ai_duration = ai_tests.get("execution", {}).get("duration_seconds", 0)
        
        if baseline_duration > 0:
            speedup = baseline_duration / ai_duration
            scalability["performance"] = {
                "baseline_duration_seconds": baseline_duration,
                "ai_duration_seconds": ai_duration,
                "speedup": round(speedup, 2),
                "improvement": speedup > 1,
            }
    
    # Repeatability (consistency across participants)
    # This would require multiple participants' data
    scalability["repeatability"] = {
        "note": "Requires data from multiple participants to assess",
    }
    
    return scalability


def calculate_sustainability_metrics(baseline_data, ai_data):
    """Calculate sustainability metrics.
    
    Args:
        baseline_data: Baseline aggregated data
        ai_data: AI-assisted aggregated data
    
    Returns:
        Dictionary with sustainability metrics
    """
    sustainability = {}
    
    # Energy use
    baseline_energy = baseline_data.get("summary", {}).get("total_energy_kwh", 0)
    ai_energy = ai_data.get("summary", {}).get("total_energy_kwh", 0)
    
    if baseline_energy > 0:
        energy_reduction = ((baseline_energy - ai_energy) / baseline_energy) * 100
        sustainability["energy"] = {
            "baseline_kwh": baseline_energy,
            "ai_kwh": ai_energy,
            "reduction_percent": round(energy_reduction, 2),
            "improvement": energy_reduction > 0,
        }
    
    # Compute cycles
    baseline_data_sources = baseline_data.get("data", {})
    ai_data_sources = ai_data.get("data", {})
    
    if "carbon_footprint" in baseline_data_sources and "carbon_footprint" in ai_data_sources:
        baseline_cycles = baseline_data_sources["carbon_footprint"].get("compute", {}).get("estimated_cycles", 0)
        ai_cycles = ai_data_sources["carbon_footprint"].get("compute", {}).get("estimated_cycles", 0)
        
        if baseline_cycles > 0:
            cycles_reduction = ((baseline_cycles - ai_cycles) / baseline_cycles) * 100
            sustainability["compute_cycles"] = {
                "baseline_cycles": baseline_cycles,
                "ai_cycles": ai_cycles,
                "reduction_percent": round(cycles_reduction, 2),
                "improvement": cycles_reduction > 0,
            }
    
    # Emissions
    baseline_emissions = baseline_data.get("summary", {}).get("total_emissions_kg_co2", 0)
    ai_emissions = ai_data.get("summary", {}).get("total_emissions_kg_co2", 0)
    
    if baseline_emissions > 0:
        emissions_reduction = ((baseline_emissions - ai_emissions) / baseline_emissions) * 100
        sustainability["emissions"] = {
            "baseline_kg_co2": baseline_emissions,
            "ai_kg_co2": ai_emissions,
            "reduction_percent": round(emissions_reduction, 2),
            "improvement": emissions_reduction > 0,
        }
    
    return sustainability


def calculate_governance_metrics(baseline_data, ai_data):
    """Calculate governance metrics.
    
    Args:
        baseline_data: Baseline aggregated data
        ai_data: AI-assisted aggregated data
    
    Returns:
        Dictionary with governance metrics
    """
    governance = {
        "security": {
            "note": "Assessed via governance checklist",
        },
        "ethical_ai": {
            "note": "Assessed via governance checklist",
        },
        "data_privacy": {
            "note": "Assessed via governance checklist",
        },
    }
    
    # Check if governance checklist data is available
    # This would need to be integrated from governance_checklist.md
    
    return governance


def generate_success_criteria_report(
    baseline_file,
    ai_file,
    output_file=None
):
    """Generate comprehensive success criteria report.
    
    Args:
        baseline_file: Path to baseline (manual) aggregated data JSON
        ai_file: Path to AI-assisted aggregated data JSON
        output_file: Output JSON file path
    
    Returns:
        Dictionary with success criteria report
    """
    # Load data
    baseline_data = load_aggregated_data(baseline_file)
    ai_data = load_aggregated_data(ai_file)
    
    # Calculate all metrics
    report = {
        "report_timestamp": datetime.now().isoformat(),
        "baseline_file": str(Path(baseline_file).absolute()),
        "ai_file": str(Path(ai_file).absolute()),
        "success_criteria": {
            "efficiency": calculate_efficiency_metrics(baseline_data, ai_data),
            "quality": calculate_quality_metrics(baseline_data, ai_data),
            "scalability": calculate_scalability_metrics(baseline_data, ai_data),
            "sustainability": calculate_sustainability_metrics(baseline_data, ai_data),
            "governance": calculate_governance_metrics(baseline_data, ai_data),
        },
        "summary": generate_summary_text(baseline_data, ai_data),
    }
    
    # Save to file if specified
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"Success criteria report saved to: {output_path}")
    
    return report


def generate_summary_text(baseline_data, ai_data):
    """Generate human-readable summary.
    
    Args:
        baseline_data: Baseline aggregated data
        ai_data: AI-assisted aggregated data
    
    Returns:
        String summary
    """
    summary_parts = []
    
    # Efficiency
    baseline_time = baseline_data.get("summary", {}).get("total_duration_seconds", 0)
    ai_time = ai_data.get("summary", {}).get("total_duration_seconds", 0)
    if baseline_time > 0:
        time_reduction = ((baseline_time - ai_time) / baseline_time) * 100
        summary_parts.append(f"Time: {time_reduction:+.1f}% change ({baseline_time/60:.1f}min → {ai_time/60:.1f}min)")
    
    # Quality
    baseline_score = baseline_data.get("summary", {}).get("code_quality_score")
    ai_score = ai_data.get("summary", {}).get("code_quality_score")
    if baseline_score is not None and ai_score is not None:
        score_change = ai_score - baseline_score
        summary_parts.append(f"Code Quality: {score_change:+.1f}% change ({baseline_score:.1f}% → {ai_score:.1f}%)")
    
    # Sustainability
    baseline_energy = baseline_data.get("summary", {}).get("total_energy_kwh", 0)
    ai_energy = ai_data.get("summary", {}).get("total_energy_kwh", 0)
    if baseline_energy > 0:
        energy_reduction = ((baseline_energy - ai_energy) / baseline_energy) * 100
        summary_parts.append(f"Energy: {energy_reduction:+.1f}% change ({baseline_energy:.4f}kWh → {ai_energy:.4f}kWh)")
    
    return "\n".join(summary_parts) if summary_parts else "No metrics available"


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate success criteria report comparing manual vs AI-assisted runs"
    )
    parser.add_argument(
        "baseline_file",
        type=str,
        help="Path to baseline (manual) aggregated data JSON file"
    )
    parser.add_argument(
        "ai_file",
        type=str,
        help="Path to AI-assisted aggregated data JSON file"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="DATA_COLLECTION/success_criteria_report.json",
        help="Output JSON file path"
    )
    
    args = parser.parse_args()
    
    # Generate report
    report = generate_success_criteria_report(
        args.baseline_file,
        args.ai_file,
        output_file=args.output
    )
    
    # Print summary
    print("\n=== Success Criteria Report ===")
    print(report["summary"])
    print(f"\nFull report saved to: {args.output}")
    
    # Print detailed metrics
    print("\n=== Detailed Metrics ===")
    for criterion, metrics in report["success_criteria"].items():
        print(f"\n{criterion.upper()}:")
        for metric, value in metrics.items():
            if isinstance(value, dict) and "improvement" in value:
                status = "✓" if value["improvement"] else "✗"
                print(f"  {status} {metric}: {value}")
            else:
                print(f"  {metric}: {value}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
