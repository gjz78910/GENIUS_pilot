#!/usr/bin/env python3
"""Collect best-effort Claude Code metrics for GENIUS AI-condition sessions.

The collector summarizes local Claude Code and VS Code extension artifacts. It
does not treat local transcript text as provider token telemetry; exact token
and cost values should come from Bedrock/Anthropic billing where available.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def vscode_root() -> Path:
    home = Path.home()
    if os.name == "nt":
        return home / "AppData" / "Roaming" / "Code"
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / "Code"
    return home / ".config" / "Code"


def parse_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(value, dict):
                    records.append(value)
    except OSError:
        return []
    return records


def role_from_record(record: dict[str, Any]) -> str | None:
    for key in ("type", "role"):
        value = record.get(key)
        if isinstance(value, str) and value in {"user", "assistant", "system"}:
            return value

    message = record.get("message")
    if isinstance(message, dict):
        role = message.get("role")
        if isinstance(role, str):
            return role
    return None


def usage_from_record(record: dict[str, Any]) -> dict[str, int]:
    usage: dict[str, int] = {}
    candidates = []
    if isinstance(record.get("usage"), dict):
        candidates.append(record["usage"])
    message = record.get("message")
    if isinstance(message, dict) and isinstance(message.get("usage"), dict):
        candidates.append(message["usage"])

    for candidate in candidates:
        for key, value in candidate.items():
            if isinstance(value, int):
                usage[key] = usage.get(key, 0) + value
    return usage


def count_tool_uses(record: dict[str, Any]) -> int:
    text = json.dumps(record, separators=(",", ":"), ensure_ascii=False).lower()
    return text.count('"type":"tool_use"') + text.count('"tool_use"')


def collect_transcript_metrics() -> dict[str, Any]:
    projects_dir = Path.home() / ".claude" / "projects"
    metrics: dict[str, Any] = {
        "projects_dir": str(projects_dir),
        "projects_dir_exists": projects_dir.exists(),
        "transcript_files": 0,
        "records": 0,
        "conversations": 0,
        "user_turns": 0,
        "assistant_turns": 0,
        "system_turns": 0,
        "tool_uses": 0,
        "usage_fields": {},
        "files": [],
    }
    if not projects_dir.exists():
        return metrics

    for path in sorted(projects_dir.rglob("*.jsonl")):
        records = parse_jsonl(path)
        if not records:
            continue

        file_counts = {
            "path": str(path),
            "records": len(records),
            "user_turns": 0,
            "assistant_turns": 0,
            "system_turns": 0,
            "tool_uses": 0,
            "usage_fields": {},
        }
        metrics["transcript_files"] += 1
        metrics["records"] += len(records)
        metrics["conversations"] += 1

        for record in records:
            role = role_from_record(record)
            if role == "user":
                metrics["user_turns"] += 1
                file_counts["user_turns"] += 1
            elif role == "assistant":
                metrics["assistant_turns"] += 1
                file_counts["assistant_turns"] += 1
            elif role == "system":
                metrics["system_turns"] += 1
                file_counts["system_turns"] += 1

            tool_uses = count_tool_uses(record)
            metrics["tool_uses"] += tool_uses
            file_counts["tool_uses"] += tool_uses

            for key, value in usage_from_record(record).items():
                metrics["usage_fields"][key] = metrics["usage_fields"].get(key, 0) + value
                file_counts["usage_fields"][key] = file_counts["usage_fields"].get(key, 0) + value

        metrics["files"].append(file_counts)
    return metrics


def collect_vscode_extension_metrics() -> dict[str, Any]:
    logs_root = vscode_root() / "logs"
    storage_root = vscode_root() / "User" / "globalStorage" / "anthropic.claude-code"
    metrics: dict[str, Any] = {
        "logs_root": str(logs_root),
        "storage_root": str(storage_root),
        "extension_installed": storage_root.exists(),
        "log_files": 0,
        "claude_log_files": 0,
        "error_lines": 0,
        "warning_lines": 0,
        "permission_mentions": 0,
    }
    if not logs_root.exists():
        return metrics

    for path in logs_root.rglob("*"):
        if not path.is_file():
            continue
        name = str(path).lower()
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "claude" not in name and "anthropic" not in name and "claude" not in content.lower():
            continue

        metrics["log_files"] += 1
        if "anthropic.claude-code" in name or "claude-code" in name:
            metrics["claude_log_files"] += 1
        for line in content.splitlines():
            lower = line.lower()
            if re.search(r"\b(error|exception|traceback)\b", lower):
                metrics["error_lines"] += 1
            if re.search(r"\b(warn|warning)\b", lower):
                metrics["warning_lines"] += 1
            if "permission" in lower:
                metrics["permission_mentions"] += 1
    return metrics


def build_output_path(output: str | None, participant_id: str | None, session_id: str | None) -> Path | None:
    if output:
        return Path(output)
    if participant_id and session_id:
        return Path(f"DATA_COLLECTION/claude_code_metrics_{participant_id}_{session_id}.json")
    if participant_id:
        return Path(f"DATA_COLLECTION/claude_code_metrics_{participant_id}.json")
    return None


def collect_claude_code_metrics() -> dict[str, Any]:
    transcript = collect_transcript_metrics()
    vscode = collect_vscode_extension_metrics()
    data = {
        "total_detected_events": transcript["records"] + vscode["log_files"],
        "claude_conversations": transcript["conversations"],
        "claude_user_turns": transcript["user_turns"],
        "claude_assistant_turns": transcript["assistant_turns"],
        "claude_system_turns": transcript["system_turns"],
        "claude_tool_uses": transcript["tool_uses"],
        "claude_usage_fields": transcript["usage_fields"],
        "vscode_claude_log_files": vscode["claude_log_files"],
        "vscode_error_lines": vscode["error_lines"],
        "vscode_warning_lines": vscode["warning_lines"],
    }
    return {
        "collection_timestamp": utc_now(),
        "collection_method": "claude_code_local_transcript_and_vscode_log_scan",
        "notes": (
            "Token-like usage fields are reported only when present in local Claude Code "
            "records. Treat provider billing, Bedrock invocation logs, or Anthropic "
            "usage exports as authoritative for cost and token accounting."
        ),
        "data": data,
        "transcripts": transcript,
        "vscode_extension": vscode,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect Claude Code metrics")
    parser.add_argument("-o", "--output", type=str, help="Output JSON file path")
    parser.add_argument("--participant-id", type=str, help="Participant ID")
    parser.add_argument("--session-id", type=str, help="Session ID")
    args = parser.parse_args()

    metrics = collect_claude_code_metrics()
    output_path = build_output_path(args.output, args.participant_id, args.session_id)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
        print(f"Claude Code metrics saved to: {output_path}")
        print(f"Claude Code user turns: {metrics['data']['claude_user_turns']}")
        return 0

    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
