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
    pass_rule: str = "all_tests"


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
        pass_rule="task1_cp3_scalability_all_required",
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


def parse_unittest_cases(output: str) -> List[Dict[str, str]]:
    """Extract verbose unittest case statuses from stdout/stderr."""
    cases: List[Dict[str, str]] = []
    pattern = re.compile(r"^(test_[^\s]+) \(([^)]+)\) \.\.\. (ok|FAIL|ERROR|skipped .*)$", re.MULTILINE)
    for match in pattern.finditer(output):
        cases.append(
            {
                "test": match.group(1),
                "qualified_name": match.group(2),
                "status": match.group(3),
            }
        )
    return cases


def apply_pass_rule(
    spec: TestRunSpec,
    return_code: int,
    timed_out: bool,
    combined_output: str,
) -> Dict[str, object]:
    if timed_out:
        return {
            "success": False,
            "completion_status": "FAIL",
            "pass_criteria": {
                "rule": spec.pass_rule,
                "reason": "Timed out before the checkpoint could finish.",
            },
        }

    if spec.pass_rule != "task1_cp3_scalability_all_required":
        success = return_code == 0
        return {
            "success": success,
            "completion_status": "PASS" if success else None,
            "pass_criteria": {"rule": spec.pass_rule},
        }

    cases = parse_unittest_cases(combined_output)
    scalability_cases = [
        case for case in cases if case["qualified_name"].startswith("tests.performance.test_scalability.")
    ]
    non_scalability_cases = [
        case for case in cases if not case["qualified_name"].startswith("tests.performance.test_scalability.")
    ]
    scalability_passed = sum(1 for case in scalability_cases if case["status"] == "ok")
    scalability_total_expected = 5
    non_scalability_failed = [
        case for case in non_scalability_cases if case["status"] not in {"ok"} and not case["status"].startswith("skipped")
    ]
    success = (
        scalability_passed == scalability_total_expected
        and len(scalability_cases) == scalability_total_expected
        and not non_scalability_failed
    )
    completion_status = "PASS" if success else ("PARTIAL" if scalability_passed > 0 else "FAIL")
    return {
        "success": success,
        "completion_status": completion_status,
        "pass_criteria": {
            "rule": spec.pass_rule,
            "scalability_required": scalability_total_expected,
            "scalability_total_expected": scalability_total_expected,
            "scalability_total_seen": len(scalability_cases),
            "scalability_passed": scalability_passed,
            "non_scalability_failed": non_scalability_failed,
        },
    }


def run_spec(spec: TestRunSpec, timeout_seconds: int) -> Dict[str, object]:
    """Run a test spec and return result payload."""
    started_at = datetime.now().isoformat()
    t0 = time.time()
    timed_out = False
    try:
        result = subprocess.run(
            spec.command,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
        return_code = result.returncode
        combined_output = (result.stdout or "") + (result.stderr or "")
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        return_code = 124
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        combined_output = stdout + stderr + f"\nTIMEOUT after {timeout_seconds} seconds\n"
    duration = round(time.time() - t0, 3)

    rule_result = apply_pass_rule(spec, return_code, timed_out, combined_output)
    payload = {
        "run_key": spec.key,
        "filename_prefix": spec.filename_prefix,
        "started_at": started_at,
        "finished_at": datetime.now().isoformat(),
        "duration_seconds": duration,
        "command": spec.command,
        "return_code": return_code,
        "success": rule_result["success"],
        "timed_out": timed_out,
        "timeout_seconds": timeout_seconds,
        "test_statistics": parse_unittest_stats(combined_output),
        "test_cases": parse_unittest_cases(combined_output),
        "pass_criteria": rule_result["pass_criteria"],
        "completion_status": rule_result["completion_status"],
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
    parser.add_argument(
        "--timeout",
        type=int,
        default=180,
        help="Maximum seconds for each checkpoint before recording a timeout (default: 180).",
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
    completion_results: list[dict[str, object]] = []
    for key in run_order:
        spec = RUN_SPECS[key]
        print(f"[RUN] {spec.filename_prefix}: {' '.join(spec.command)}")
        payload = run_spec(spec, args.timeout)
        out_path = build_output_path(
            output_dir, spec.filename_prefix, args.participant_id, args.session_id
        )
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        status = "OK" if payload["success"] else "FAIL"
        print(f"[{status}] Saved {out_path}")
        overall_success = overall_success and bool(payload["success"])

        stats = payload["test_statistics"]
        tests_run = int(stats.get("tests_run", 0))
        failed = int(stats.get("failures", 0)) + int(stats.get("errors", 0))
        if payload.get("completion_status"):
            completion_status = str(payload["completion_status"])
        elif bool(payload["success"]):
            completion_status = "PASS"
        elif tests_run > 0 and failed < tests_run:
            completion_status = "PARTIAL"
        else:
            completion_status = "FAIL"
        completion_results.append({
            "checkpoint": key,
            "status": completion_status,
            "tests_run": tests_run,
            "failures": int(stats.get("failures", 0)),
            "errors": int(stats.get("errors", 0)),
            "return_code": payload["return_code"],
            "timed_out": payload["timed_out"],
            "result_file": str(out_path),
        })

    if args.only != "all":
        for key in RUN_SPECS:
            if key != args.only:
                completion_results.append({
                    "checkpoint": key,
                    "status": "NOT RUN",
                    "tests_run": 0,
                    "failures": 0,
                    "errors": 0,
                    "return_code": None,
                    "timed_out": False,
                    "result_file": None,
                })

    report_suffix = "_".join(part for part in [args.participant_id, args.session_id] if part) or "run"
    report_path = output_dir / f"completion_report_{report_suffix}.json"
    report = {
        "participant_id": args.participant_id,
        "session_id": args.session_id,
        "generated_at": datetime.now().isoformat(),
        "authority": "experiment_checkpoint_runner",
        "warning": "AI statements are not authoritative completion evidence.",
        "checkpoints": completion_results,
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("\nAUTHORITATIVE EXPERIMENT COMPLETION REPORT")
    print("AI statements are not completion evidence; use these checkpoint results.")
    for result in completion_results:
        print(f"  {result['checkpoint']:<10} {result['status']}")
    print(f"Saved {report_path}")

    return 0 if overall_success else 1


if __name__ == "__main__":
    raise SystemExit(main())
