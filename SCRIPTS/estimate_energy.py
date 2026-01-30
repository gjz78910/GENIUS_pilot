#!/usr/bin/env python3
"""Estimate energy consumption from resource monitoring data.

This script estimates energy consumption based on CPU usage, memory usage,
GPU usage, and system idle vs active time.
"""

import json
import sys
from datetime import datetime
from pathlib import Path


# Typical power consumption values (in watts)
# These are approximations and may need calibration for specific hardware
CPU_TDP_BY_CORE = {
    "intel": 15,  # Watts per core (typical laptop CPU)
    "amd": 12,
    "apple_m1": 10,  # Apple Silicon is more efficient
    "apple_m2": 10,
    "default": 15,
}

MEMORY_POWER_PER_GB = 0.5  # Watts per GB of RAM
GPU_POWER = {
    "integrated": 5,  # Integrated GPU
    "discrete_low": 30,  # Low-end discrete GPU
    "discrete_mid": 60,  # Mid-range discrete GPU
    "discrete_high": 100,  # High-end discrete GPU
    "default": 5,
}

IDLE_POWER = 10  # Base system idle power (watts)
SCREEN_POWER = 5  # Display power (watts)


def detect_cpu_type(cpu_model):
    """Detect CPU type from model name.
    
    Args:
        cpu_model: CPU model string
    
    Returns:
        CPU type string
    """
    cpu_lower = cpu_model.lower()
    if "intel" in cpu_lower or "core" in cpu_lower or "xeon" in cpu_lower:
        return "intel"
    elif "amd" in cpu_lower or "ryzen" in cpu_lower:
        return "amd"
    elif "apple" in cpu_lower or "m1" in cpu_lower or "m2" in cpu_lower:
        return "apple_m1" if "m1" in cpu_lower else "apple_m2"
    return "default"


def estimate_cpu_power(cpu_usage_percent, cpu_cores, cpu_model, duration_hours):
    """Estimate CPU power consumption.
    
    Args:
        cpu_usage_percent: Average CPU usage percentage
        cpu_cores: Number of CPU cores
        cpu_model: CPU model string
        duration_hours: Duration in hours
    
    Returns:
        Energy consumption in watt-hours
    """
    cpu_type = detect_cpu_type(cpu_model)
    power_per_core = CPU_TDP_BY_CORE.get(cpu_type, CPU_TDP_BY_CORE["default"])
    
    # CPU power scales with usage
    # Base power + usage-dependent power
    base_power = power_per_core * cpu_cores * 0.2  # 20% base power
    usage_power = power_per_core * cpu_cores * (cpu_usage_percent / 100.0) * 0.8  # 80% usage-dependent
    
    total_power_watts = base_power + usage_power
    energy_wh = total_power_watts * duration_hours
    
    return energy_wh


def estimate_memory_power(memory_gb, duration_hours):
    """Estimate memory power consumption.
    
    Args:
        memory_gb: Total memory in GB
        duration_hours: Duration in hours
    
    Returns:
        Energy consumption in watt-hours
    """
    power_watts = memory_gb * MEMORY_POWER_PER_GB
    energy_wh = power_watts * duration_hours
    return energy_wh


def estimate_gpu_power(gpu_present, gpu_type, gpu_usage_percent, duration_hours):
    """Estimate GPU power consumption.
    
    Args:
        gpu_present: Whether GPU is present
        gpu_type: GPU type string
        duration_hours: Duration in hours
    
    Returns:
        Energy consumption in watt-hours
    """
    if not gpu_present:
        return 0.0
    
    # Determine GPU power based on type
    gpu_lower = (gpu_type or "").lower()
    if "integrated" in gpu_lower or "apple" in gpu_lower:
        base_power = GPU_POWER["integrated"]
    elif "rtx" in gpu_lower or "gtx" in gpu_lower:
        if "3060" in gpu_lower or "3070" in gpu_lower:
            base_power = GPU_POWER["discrete_mid"]
        elif "3080" in gpu_lower or "3090" in gpu_lower:
            base_power = GPU_POWER["discrete_high"]
        else:
            base_power = GPU_POWER["discrete_low"]
    else:
        base_power = GPU_POWER["default"]
    
    # GPU power scales with usage
    power_watts = base_power * (gpu_usage_percent / 100.0) if gpu_usage_percent else base_power * 0.3
    energy_wh = power_watts * duration_hours
    
    return energy_wh


def estimate_system_power(duration_hours, active_time_hours):
    """Estimate base system power consumption.
    
    Args:
        duration_hours: Total duration in hours
        active_time_hours: Active time (non-idle) in hours
    
    Returns:
        Energy consumption in watt-hours
    """
    # Idle power for idle time
    idle_energy = IDLE_POWER * (duration_hours - active_time_hours)
    
    # Active power (idle + screen) for active time
    active_energy = (IDLE_POWER + SCREEN_POWER) * active_time_hours
    
    return idle_energy + active_energy


def load_resource_data(resource_file):
    """Load resource monitoring data.
    
    Args:
        resource_file: Path to resource monitoring JSONL file
    
    Returns:
        List of resource samples
    """
    samples = []
    with open(resource_file, "r") as f:
        for line in f:
            if line.strip():
                samples.append(json.loads(line))
    return samples


def calculate_average_metrics(samples):
    """Calculate average metrics from samples.
    
    Args:
        samples: List of resource samples
    
    Returns:
        Dictionary with average metrics
    """
    if not samples:
        return None
    
    cpu_values = [s["cpu"]["average"] for s in samples if "cpu" in s and "average" in s["cpu"]]
    memory_values = [s["memory"]["used_gb"] for s in samples if "memory" in s and "used_gb" in s["memory"]]
    
    # Calculate duration
    if len(samples) > 1:
        first_time = datetime.fromisoformat(samples[0]["timestamp"])
        last_time = datetime.fromisoformat(samples[-1]["timestamp"])
        duration_seconds = (last_time - first_time).total_seconds()
        duration_hours = duration_seconds / 3600.0
    else:
        duration_hours = 0.0
    
    # Estimate active time (when CPU > 10%)
    active_samples = [s for s in samples if s.get("cpu", {}).get("average", 0) > 10]
    active_time_hours = (len(active_samples) / len(samples)) * duration_hours if samples else 0
    
    return {
        "avg_cpu_percent": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
        "avg_memory_gb": sum(memory_values) / len(memory_values) if memory_values else 0,
        "duration_hours": duration_hours,
        "active_time_hours": active_time_hours,
    }


def estimate_energy_consumption(resource_file, system_info_file=None, output_file=None):
    """Estimate total energy consumption.
    
    Args:
        resource_file: Path to resource monitoring JSONL file
        system_info_file: Path to system info JSON file (optional)
        output_file: Output JSON file path (optional)
    
    Returns:
        Dictionary with energy estimates
    """
    # Load resource data
    samples = load_resource_data(resource_file)
    metrics = calculate_average_metrics(samples)
    
    if not metrics:
        print("Error: No resource data found", file=sys.stderr)
        return None
    
    # Load system info if available
    system_info = {}
    if system_info_file and Path(system_info_file).exists():
        with open(system_info_file, "r") as f:
            system_info = json.load(f)
    
    # Get system specs
    cpu_cores = system_info.get("cpu", {}).get("cores_logical", 4)
    cpu_model = system_info.get("cpu", {}).get("model", "unknown")
    memory_total_gb = system_info.get("memory", {}).get("total_gb", 8)
    gpu_present = system_info.get("gpu", {}).get("present", False)
    gpu_model = system_info.get("gpu", {}).get("model", "")
    
    # Estimate energy for each component
    cpu_energy = estimate_cpu_power(
        metrics["avg_cpu_percent"],
        cpu_cores,
        cpu_model,
        metrics["duration_hours"]
    )
    
    memory_energy = estimate_memory_power(
        memory_total_gb,
        metrics["duration_hours"]
    )
    
    # GPU usage not directly measured, estimate based on CPU usage
    gpu_usage = metrics["avg_cpu_percent"] * 0.5 if gpu_present else 0
    gpu_energy = estimate_gpu_power(
        gpu_present,
        gpu_model,
        gpu_usage,
        metrics["duration_hours"]
    )
    
    system_energy = estimate_system_power(
        metrics["duration_hours"],
        metrics["active_time_hours"]
    )
    
    # Total energy
    total_energy_wh = cpu_energy + memory_energy + gpu_energy + system_energy
    total_energy_kwh = total_energy_wh / 1000.0
    
    energy_estimate = {
        "estimation_timestamp": datetime.now().isoformat(),
        "resource_file": str(Path(resource_file).absolute()),
        "system_info_file": str(Path(system_info_file).absolute()) if system_info_file else None,
        "duration": {
            "total_hours": round(metrics["duration_hours"], 3),
            "active_hours": round(metrics["active_time_hours"], 3),
            "idle_hours": round(metrics["duration_hours"] - metrics["active_time_hours"], 3),
        },
        "resource_usage": {
            "avg_cpu_percent": round(metrics["avg_cpu_percent"], 2),
            "avg_memory_gb": round(metrics["avg_memory_gb"], 2),
        },
        "energy_breakdown": {
            "cpu_wh": round(cpu_energy, 2),
            "memory_wh": round(memory_energy, 2),
            "gpu_wh": round(gpu_energy, 2),
            "system_wh": round(system_energy, 2),
        },
        "total_energy": {
            "wh": round(total_energy_wh, 2),
            "kwh": round(total_energy_kwh, 4),
        },
        "notes": [
            "Energy estimates are approximations based on typical hardware power consumption",
            "Actual energy consumption may vary based on specific hardware",
            "GPU usage is estimated from CPU usage (may not be accurate)",
            "Calibration with actual power measurements recommended for accuracy",
        ],
    }
    
    # Save to file if specified
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump(energy_estimate, f, indent=2)
        
        print(f"Energy estimate saved to: {output_path}")
    
    return energy_estimate


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Estimate energy consumption from resource monitoring data"
    )
    parser.add_argument(
        "resource_file",
        type=str,
        help="Path to resource monitoring JSONL file"
    )
    parser.add_argument(
        "-s", "--system-info",
        type=str,
        help="Path to system info JSON file"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="DATA_COLLECTION/energy_estimate.json",
        help="Output JSON file path"
    )
    parser.add_argument(
        "--participant-id",
        type=str,
        help="Participant ID to include in filename"
    )
    
    args = parser.parse_args()
    
    # Determine output path
    output_path = args.output
    if args.participant_id:
        output_path = f"DATA_COLLECTION/energy_estimate_{args.participant_id}.json"
    
    # Estimate energy
    estimate = estimate_energy_consumption(
        args.resource_file,
        system_info_file=args.system_info,
        output_file=output_path
    )
    
    if not estimate:
        return 1
    
    # Print summary
    print("\n=== Energy Consumption Estimate ===")
    print(f"Duration: {estimate['duration']['total_hours']:.2f} hours")
    print(f"  Active: {estimate['duration']['active_hours']:.2f} hours")
    print(f"  Idle: {estimate['duration']['idle_hours']:.2f} hours")
    print(f"\nAverage CPU: {estimate['resource_usage']['avg_cpu_percent']:.1f}%")
    print(f"Average Memory: {estimate['resource_usage']['avg_memory_gb']:.2f} GB")
    print(f"\nEnergy Breakdown:")
    print(f"  CPU: {estimate['energy_breakdown']['cpu_wh']:.2f} Wh")
    print(f"  Memory: {estimate['energy_breakdown']['memory_wh']:.2f} Wh")
    print(f"  GPU: {estimate['energy_breakdown']['gpu_wh']:.2f} Wh")
    print(f"  System: {estimate['energy_breakdown']['system_wh']:.2f} Wh")
    print(f"\nTotal Energy: {estimate['total_energy']['kwh']:.4f} kWh ({estimate['total_energy']['wh']:.2f} Wh)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
