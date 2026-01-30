#!/usr/bin/env python3
"""Collect test execution metrics.

This script runs tests and collects metrics including execution time, pass/fail
counts, code coverage, and resource usage during test execution.
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import psutil
except ImportError:
    print("Warning: psutil not installed. Memory metrics will not be available.")
    psutil = None


def get_memory_usage():
    """Get current memory usage.
    
    Returns:
        Dictionary with memory metrics
    """
    if not psutil:
        return None
    
    process = psutil.Process()
    mem_info = process.memory_info()
    mem_percent = process.memory_percent()
    
    return {
        "rss_mb": round(mem_info.rss / (1024**2), 2),
        "vms_mb": round(mem_info.vms / (1024**2), 2),
        "percent": round(mem_percent, 2),
    }


def get_cpu_usage(duration=1.0):
    """Get average CPU usage over a period.
    
    Args:
        duration: Duration to measure CPU usage
    
    Returns:
        Average CPU usage percentage
    """
    if not psutil:
        return None
    
    process = psutil.Process()
    try:
        cpu_percent = process.cpu_percent(interval=duration)
        return round(cpu_percent, 2)
    except Exception:
        return None


def run_tests(test_path="tests", pattern="test_*.py", verbose=True, exclude_performance=True):
    """Run tests and capture output.
    
    Args:
        test_path: Path to test directory
        pattern: Test file pattern
        verbose: Whether to use verbose output
        exclude_performance: Exclude performance tests (default: True)
    
    Returns:
        Tuple of (success, output, duration)
    """
    # Exclude performance tests by default (they take too long)
    if exclude_performance:
        # Run specific test modules instead of discover to exclude performance/
        test_modules = [
            "tests.test_benchmarks",
            "tests.test_data_loader",
            "tests.test_engineer",
            "tests.test_job",
            "tests.test_matching",
            "tests.test_models",
            "tests.test_report_correctness",
            "tests.test_routing",
            "tests.test_scheduler",
            "tests.test_scheduler_integration",
        ]
        cmd = ["python", "-m", "unittest"] + test_modules
    else:
        cmd = ["python", "-m", "unittest", "discover", "-s", test_path, "-p", pattern]
    
    if verbose:
        cmd.append("-v")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        duration = time.time() - start_time
        return result.returncode == 0, result.stdout + result.stderr, duration
    except Exception as e:
        duration = time.time() - start_time
        return False, str(e), duration


def parse_test_output(output):
    """Parse unittest output to extract test counts.
    
    Args:
        output: Test output string
    
    Returns:
        Dictionary with test statistics
    """
    stats = {
        "tests_run": 0,
        "failures": 0,
        "errors": 0,
        "skipped": 0,
        "success": False,
    }
    
    # Look for unittest summary line
    import re
    
    # Pattern: "Ran X tests in Y.YYs"
    ran_match = re.search(r"Ran (\d+) test", output)
    if ran_match:
        stats["tests_run"] = int(ran_match.group(1))
    
    # Pattern: "OK" or "FAILED"
    if "OK" in output and "FAILED" not in output:
        stats["success"] = True
    
    # Pattern: "FAILED (failures=X)"
    failures_match = re.search(r"FAILED.*?failures=(\d+)", output)
    if failures_match:
        stats["failures"] = int(failures_match.group(1))
        stats["success"] = False
    
    # Pattern: "errors=(\d+)"
    errors_match = re.search(r"errors=(\d+)", output)
    if errors_match:
        stats["errors"] = int(errors_match.group(1))
    
    # Pattern: "skipped=(\d+)"
    skipped_match = re.search(r"skipped=(\d+)", output)
    if skipped_match:
        stats["skipped"] = int(skipped_match.group(1))
    
    return stats


def collect_test_metrics(test_path="tests", pattern="test_*.py", output_file=None, exclude_performance=True):
    """Collect all test metrics.
    
    Args:
        test_path: Path to test directory
        pattern: Test file pattern
        output_file: Output JSON file path
        exclude_performance: Exclude performance tests (default: True)
    
    Returns:
        Dictionary with all test metrics
    """
    # Get initial memory usage
    initial_memory = get_memory_usage()
    initial_cpu = get_cpu_usage(0.1)
    
    # Run tests
    if exclude_performance:
        print(f"Running tests (excluding performance tests)...")
    else:
        print(f"Running tests from {test_path} with pattern {pattern}...")
    success, output, duration = run_tests(test_path, pattern, exclude_performance=exclude_performance)
    
    # Get peak memory usage
    peak_memory = get_memory_usage()
    peak_cpu = get_cpu_usage(0.1)
    
    # Parse test output
    test_stats = parse_test_output(output)
    
    # Collect coverage if available
    coverage = None
    try:
        result = subprocess.run(
            ["coverage", "report", "--format=json"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            import json as json_lib
            coverage = json_lib.loads(result.stdout)
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        pass
    
    metrics = {
        "collection_timestamp": datetime.now().isoformat(),
        "test_path": str(Path(test_path).absolute()),
        "test_pattern": pattern,
        "execution": {
            "success": success,
            "duration_seconds": round(duration, 2),
        },
        "test_statistics": test_stats,
        "resource_usage": {
            "initial_memory_mb": initial_memory["rss_mb"] if initial_memory else None,
            "peak_memory_mb": peak_memory["rss_mb"] if peak_memory else None,
            "memory_delta_mb": (
                round(peak_memory["rss_mb"] - initial_memory["rss_mb"], 2)
                if (peak_memory and initial_memory)
                else None
            ),
            "initial_cpu_percent": initial_cpu,
            "peak_cpu_percent": peak_cpu,
        },
        "coverage": coverage,
    }
    
    # Save to file if specified
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump(metrics, f, indent=2)
        
        print(f"\nTest metrics saved to: {output_path}")
    
    return metrics


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Collect test execution metrics"
    )
    parser.add_argument(
        "-t", "--test-path",
        type=str,
        default="tests",
        help="Path to test directory (default: tests)"
    )
    parser.add_argument(
        "-p", "--pattern",
        type=str,
        default="test_*.py",
        help="Test file pattern (default: test_*.py)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="DATA_COLLECTION/test_metrics.json",
        help="Output JSON file path"
    )
    parser.add_argument(
        "--participant-id",
        type=str,
        help="Participant ID to include in filename"
    )
    parser.add_argument(
        "--session-id",
        type=str,
        help="Session ID to include in filename"
    )
    parser.add_argument(
        "--include-performance",
        action="store_true",
        help="Include performance tests (warning: can take hours)"
    )
    
    args = parser.parse_args()
    
    # Determine output path
    output_path = args.output
    if args.participant_id and args.session_id:
        output_path = f"DATA_COLLECTION/test_metrics_{args.participant_id}_{args.session_id}.json"
    elif args.participant_id:
        output_path = f"DATA_COLLECTION/test_metrics_{args.participant_id}.json"
    
    # Collect metrics
    metrics = collect_test_metrics(
        test_path=args.test_path,
        pattern=args.pattern,
        output_file=output_path,
        exclude_performance=not args.include_performance
    )
    
    # Print summary
    print(f"\n=== Test Metrics Summary ===")
    print(f"Success: {metrics['execution']['success']}")
    print(f"Duration: {metrics['execution']['duration_seconds']:.2f} seconds")
    print(f"Tests run: {metrics['test_statistics']['tests_run']}")
    print(f"Failures: {metrics['test_statistics']['failures']}")
    print(f"Errors: {metrics['test_statistics']['errors']}")
    
    if metrics['resource_usage']['peak_memory_mb']:
        print(f"Peak memory: {metrics['resource_usage']['peak_memory_mb']} MB")
    if metrics['resource_usage']['peak_cpu_percent']:
        print(f"Peak CPU: {metrics['resource_usage']['peak_cpu_percent']}%")
    
    if metrics['coverage']:
        total = metrics['coverage'].get('totals', {})
        if 'percent_covered' in total:
            print(f"Coverage: {total['percent_covered']:.1f}%")


if __name__ == "__main__":
    main()
