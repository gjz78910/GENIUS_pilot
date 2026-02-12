#!/usr/bin/env python3
"""Run experiment checkpoints and store one JSON result file per checkpoint/task.

This is the canonical script for Task 1/2/3 experiment checkpoint result files.
Use this script when you need clearly named checkpoint outputs such as
`Task1_cp1_<ID>_<SESSION>.json` and `Task2_<ID>_<SESSION>.json`.

Output file naming:
- Task1_cp1_<ID>_<SESSION>.json
- Task1_cp2_<ID>_<SESSION>.json
- Task1_cp3_<ID>_<SESSION>.json
- Task2_<ID>_<SESSION>.json
- Task3_<ID>_<SESSION>.json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List


@dataclass(frozen=True)
class TestRunSpec:
    key: str
    filename_prefix: str
    command: List[str]


RUN_SPECS: Dict[str, TestRunSpec] = {
    "task1_cp1": TestRunSpec(
        key="task1_cp1",
        filename_prefix="Task1_cp1",
        command=[
            "python",
            "-m",
            "unittest",
            "tests.test_routing",
            "tests.test_routing_checkpoint_a",
            "tests.test_benchmarks.TestBenchmarksWithOptimal.test_benchmark_small_01",
            "tests.test_benchmarks.TestBenchmarksWithOptimal.test_benchmark_small_02",
            "tests.test_benchmarks.TestBenchmarksWithOptimal.test_benchmark_small_03",
            "tests.test_benchmarks.TestBenchmarksWithOptimal.test_brute_force_routing_optimal",
            "-v",
        ],
    ),
    "task1_cp2": TestRunSpec(
        key="task1_cp2",
        filename_prefix="Task1_cp2",
        command=[
            "python",
            "-m",
            "unittest",
            "tests.test_matching",
            "tests.test_benchmarks.TestBenchmarksWithOptimal.test_benchmark_small_04",
            "tests.test_benchmarks.TestBenchmarksWithOptimal.test_benchmark_small_05",
            "tests.test_routing",
            "-v",
        ],
    ),
    "task1_cp3": TestRunSpec(
        key="task1_cp3",
        filename_prefix="Task1_cp3",
        command=[
            "python",
            "-m",
            "unittest",
            "tests.performance.test_scalability",
            "tests.test_routing",
            "tests.test_matching",
            "tests.test_benchmarks",
            "-v",
        ],
    ),
    "task2": TestRunSpec(
        key="task2",
        filename_prefix="Task2",
        command=["python", "-m", "unittest", "tests.test_report_correctness", "-v"],
    ),
    "task3": TestRunSpec(
        key="task3",
        filename_prefix="Task3",
        command=["python", "-m", "unittest", "tests.test_data_loader", "-v"],
    ),
}


def parse_unittest_stats(output: str) -> Dict[str, int | bool]:
    """Extract simple test stats from unittest output."""
    stats = {
        "tests_run": 0,
        "failures": 0,
        "errors": 0,
        "skipped": 0,
        "success": False,
    }

    ran_match = re.search(r"Ran (\d+) test", output)
    if ran_match:
        stats["tests_run"] = int(ran_match.group(1))

    failures_match = re.search(r"failures=(\d+)", output)
    errors_match = re.search(r"errors=(\d+)", output)
    skipped_match = re.search(r"skipped=(\d+)", output)

    if failures_match:
        stats["failures"] = int(failures_match.group(1))
    if errors_match:
        stats["errors"] = int(errors_match.group(1))
    if skipped_match:
        stats["skipped"] = int(skipped_match.group(1))

    stats["success"] = "OK" in output and "FAILED" not in output
    return stats


def run_spec(spec: TestRunSpec) -> Dict[str, object]:
    """Run a test spec and return result payload."""
    started_at = datetime.now().isoformat()
    t0 = time.time()
    result = subprocess.run(spec.command, capture_output=True, text=True, check=False)
    duration = round(time.time() - t0, 3)
    combined_output = (result.stdout or "") + (result.stderr or "")

    payload = {
        "run_key": spec.key,
        "filename_prefix": spec.filename_prefix,
        "started_at": started_at,
        "finished_at": datetime.now().isoformat(),
        "duration_seconds": duration,
        "command": spec.command,
        "return_code": result.returncode,
        "success": result.returncode == 0,
        "test_statistics": parse_unittest_stats(combined_output),
        "output": combined_output,
    }
    return payload


def build_output_path(
    output_dir: Path, filename_prefix: str, participant_id: str | None, session_id: str | None
) -> Path:
    suffix_parts = [p for p in [participant_id, session_id] if p]
    suffix = "_".join(suffix_parts) if suffix_parts else "run"
    return output_dir / f"{filename_prefix}_{suffix}.json"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run experiment checkpoint tests and save one JSON file per checkpoint/task."
    )
    parser.add_argument(
        "--participant-id",
        type=str,
        help="Participant ID used in output filenames, e.g. P001",
    )
    parser.add_argument(
        "--session-id",
        type=str,
        help="Session ID used in output filenames, e.g. S1",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="DATA_COLLECTION",
        help="Directory for output JSON files (default: DATA_COLLECTION)",
    )
    parser.add_argument(
        "--only",
        type=str,
        choices=["task1_cp1", "task1_cp2", "task1_cp3", "task2", "task3", "all"],
        default="all",
        help="Run only one checkpoint/task, or all (default: all).",
    )

    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    run_order = (
        [args.only]
        if args.only != "all"
        else ["task1_cp1", "task1_cp2", "task1_cp3", "task2", "task3"]
    )

    overall_success = True
    for key in run_order:
        spec = RUN_SPECS[key]
        print(f"[RUN] {spec.filename_prefix}: {' '.join(spec.command)}")
        payload = run_spec(spec)
        out_path = build_output_path(
            output_dir, spec.filename_prefix, args.participant_id, args.session_id
        )
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        status = "OK" if payload["success"] else "FAIL"
        print(f"[{status}] Saved {out_path}")
        overall_success = overall_success and bool(payload["success"])

    return 0 if overall_success else 1


if __name__ == "__main__":
    raise SystemExit(main())
