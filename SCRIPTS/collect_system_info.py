#!/usr/bin/env python3
"""Collect system information for GoCodeGreen data collection.

This script automatically collects system specifications including CPU, memory,
GPU, OS, Python version, and storage information.
"""

import json
import platform
import sys
from datetime import datetime
from pathlib import Path

try:
    import psutil
except ImportError:
    print("ERROR: psutil not installed. Install with: pip install psutil")
    sys.exit(1)


def get_cpu_info():
    """Get CPU information."""
    cpu_info = {
        "model": platform.processor(),
        "cores_physical": psutil.cpu_count(logical=False),
        "cores_logical": psutil.cpu_count(logical=True),
        "frequency_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else None,
    }
    
    # Try to get more detailed CPU info on macOS
    if platform.system() == "Darwin":
        try:
            import subprocess
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                check=True
            )
            cpu_info["model"] = result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
    
    return cpu_info


def get_memory_info():
    """Get memory information."""
    mem = psutil.virtual_memory()
    return {
        "total_gb": round(mem.total / (1024**3), 2),
        "available_gb": round(mem.available / (1024**3), 2),
        "used_gb": round(mem.used / (1024**3), 2),
        "percent_used": mem.percent,
    }


def get_gpu_info():
    """Get GPU information if available."""
    gpu_info = {
        "present": False,
        "model": None,
    }
    
    # Check for GPU on macOS (Metal/Apple Silicon)
    if platform.system() == "Darwin":
        try:
            import subprocess
            # Check for Apple Silicon
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True
            )
            if "Apple" in result.stdout:
                gpu_info["present"] = True
                gpu_info["model"] = "Apple Integrated GPU"
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
    
    # Check for NVIDIA GPU (nvidia-smi)
    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout.strip():
            gpu_info["present"] = True
            gpu_info["model"] = result.stdout.strip().split("\n")[0]
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    return gpu_info


def get_storage_info():
    """Get storage information."""
    disk = psutil.disk_usage("/")
    return {
        "total_gb": round(disk.total / (1024**3), 2),
        "used_gb": round(disk.used / (1024**3), 2),
        "free_gb": round(disk.free / (1024**3), 2),
        "percent_used": disk.percent,
    }


def get_os_info():
    """Get operating system information."""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "architecture": platform.machine(),
        "platform": platform.platform(),
    }


def get_python_info():
    """Get Python information."""
    return {
        "version": platform.python_version(),
        "implementation": platform.python_implementation(),
        "compiler": platform.python_compiler(),
    }


def collect_system_info():
    """Collect all system information."""
    info = {
        "timestamp": datetime.now().isoformat(),
        "cpu": get_cpu_info(),
        "memory": get_memory_info(),
        "gpu": get_gpu_info(),
        "storage": get_storage_info(),
        "os": get_os_info(),
        "python": get_python_info(),
    }
    return info


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Collect system information for GoCodeGreen data collection"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="DATA_COLLECTION/system_info.json",
        help="Output file path (default: DATA_COLLECTION/system_info.json)"
    )
    parser.add_argument(
        "--participant-id",
        type=str,
        help="Participant ID to include in filename"
    )
    
    args = parser.parse_args()
    
    # Collect system information
    info = collect_system_info()
    
    # Determine output path
    output_path = Path(args.output)
    if args.participant_id:
        # Insert participant ID into filename
        output_path = output_path.parent / f"system_info_{args.participant_id}.json"
    
    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to file
    with open(output_path, "w") as f:
        json.dump(info, f, indent=2)
    
    print(f"System information collected and saved to: {output_path}")
    print(f"CPU: {info['cpu']['model']} ({info['cpu']['cores_logical']} cores)")
    print(f"Memory: {info['memory']['total_gb']} GB")
    print(f"GPU: {'Yes' if info['gpu']['present'] else 'No'}")
    if info['gpu']['present']:
        print(f"  Model: {info['gpu']['model']}")
    print(f"Storage: {info['storage']['total_gb']} GB total, {info['storage']['free_gb']} GB free")
    print(f"OS: {info['os']['system']} {info['os']['release']}")
    print(f"Python: {info['python']['version']}")


if __name__ == "__main__":
    main()
