#!/usr/bin/env python3
"""Collect best-effort Kiro IDE activity metrics.

The collector intentionally avoids storing raw prompt or response text. It reads
Kiro local session state and logs, then keeps only counts, IDs, model names,
credit metering, context usage, and character-count token estimates.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


EVENT_PATTERNS = {
    "chat_messages": re.compile(r"\b(chat|prompt|user message|conversation)\b", re.I),
    "agent_actions": re.compile(r"\b(agent|autopilot|supervised|tool call|tool_use|apply patch)\b", re.I),
    "file_changes": re.compile(r"\b(write|edit|created file|modified file|delete file|diff)\b", re.I),
    "errors": re.compile(r"\b(error|exception|failed|rate limit)\b", re.I),
}

LOG_SUFFIXES = {".log", ".json", ".jsonl", ".txt"}
CHAT_API_LOG_NAME = "Q Chat API.log"


def redact_snippet(text: str, limit: int = 240) -> str:
    """Return a short diagnostic snippet without long strings or bearer tokens."""
    redacted = re.sub(r'"([^"\\]|\\.){20,}"', '"<redacted_string>"', text)
    redacted = re.sub(r"Bearer\s+[A-Za-z0-9._~+/-]+=*", "Bearer <redacted_token>", redacted)
    redacted = re.sub(
        r"(access[_-]?token[\"']?\s*[:=]\s*[\"']?)[A-Za-z0-9._~+/-]+=*",
        r"\1<redacted_token>",
        redacted,
        flags=re.I,
    )
    return redacted.strip()[:limit]


def candidate_log_roots() -> list[Path]:
    home = Path.home()
    if os.name == "nt":
        return [
            home / "AppData" / "Roaming" / "Kiro" / "logs",
            home / ".kiro" / "logs",
        ]
    if sys.platform == "darwin":
        return [
            home / "Library" / "Application Support" / "Kiro" / "logs",
            home / ".kiro" / "logs",
        ]
    return [
        home / ".config" / "Kiro" / "logs",
        home / ".config" / "kiro" / "logs",
        home / ".kiro" / "logs",
    ]


def candidate_session_roots() -> list[Path]:
    """Return Kiro IDE workspace-session roots for the current platform."""
    home = Path.home()
    if os.name == "nt":
        return [
            home / "AppData" / "Roaming" / "Kiro" / "User" / "globalStorage" / "kiro.kiroagent" / "workspace-sessions",
            home / ".kiro" / "sessions",
        ]
    if sys.platform == "darwin":
        return [
            home / "Library" / "Application Support" / "Kiro" / "User" / "globalStorage" / "kiro.kiroagent" / "workspace-sessions",
            home / "Library" / "Application Support" / "kiro" / "User" / "globalStorage" / "kiro.kiroagent" / "workspace-sessions",
            home / ".kiro" / "sessions",
        ]
    return [
        home / ".config" / "Kiro" / "User" / "globalStorage" / "kiro.kiroagent" / "workspace-sessions",
        home / ".config" / "kiro" / "User" / "globalStorage" / "kiro.kiroagent" / "workspace-sessions",
        home / ".kiro" / "sessions",
    ]


def iter_log_files(roots: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in LOG_SUFFIXES:
                files.append(path)
    return sorted(files, key=lambda item: item.stat().st_mtime, reverse=True)


def iter_session_files(roots: Iterable[Path]) -> list[Path]:
    """Return Kiro session JSON files."""
    files: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.json"):
            if path.is_file():
                files.append(path)
    return sorted(files, key=lambda item: item.stat().st_mtime, reverse=True)


def parse_logs(log_files: list[Path]) -> dict[str, object]:
    counters = {key: 0 for key in EVENT_PATTERNS}
    interactions = []

    for log_file in log_files:
        try:
            with log_file.open("r", encoding="utf-8", errors="ignore") as handle:
                for line_number, line in enumerate(handle, start=1):
                    if not line.strip():
                        continue
                    for key, pattern in EVENT_PATTERNS.items():
                        if pattern.search(line):
                            counters[key] += 1
                            if len(interactions) < 250:
                                interactions.append(
                                    {
                                        "type": key,
                                        "file": str(log_file),
                                        "line": line_number,
                                        "snippet": redact_snippet(line),
                                    }
                                )
        except OSError as exc:
            interactions.append(
                {
                    "type": "read_error",
                    "file": str(log_file),
                    "error": str(exc),
                }
            )

    counters["total_detected_events"] = sum(counters.values())
    return {
        "counters": counters,
        "interactions": interactions,
    }


def as_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def count_message_like_items(history: Any) -> int:
    if not isinstance(history, list):
        return 0
    count = 0
    for item in history:
        if not isinstance(item, dict):
            continue
        if "message" in item or "promptLogs" in item or "executionId" in item:
            count += 1
    return count


def parse_session_files(session_files: list[Path]) -> dict[str, object]:
    """Parse Kiro workspace session files without storing message text."""
    sessions: list[dict[str, object]] = []
    selected_models: Counter[str] = Counter()
    session_types: Counter[str] = Counter()
    autonomy_modes: Counter[str] = Counter()

    for path in session_files:
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            payload = json.loads(content)
        except (OSError, json.JSONDecodeError) as exc:
            sessions.append({"file": str(path), "read_error": str(exc)})
            continue

        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict) and item.get("sessionId"):
                    sessions.append(
                        {
                            "file": str(path),
                            "session_id": item.get("sessionId"),
                            "title_present": bool(item.get("title")),
                            "workspace_directory": item.get("workspaceDirectory"),
                        }
                    )
            continue

        if not isinstance(payload, dict):
            continue

        selected_model = payload.get("selectedModel")
        session_type = payload.get("sessionType")
        autonomy_mode = payload.get("autonomyMode")
        if selected_model:
            selected_models[str(selected_model)] += 1
        if session_type:
            session_types[str(session_type)] += 1
        if autonomy_mode:
            autonomy_modes[str(autonomy_mode)] += 1

        history = payload.get("history", [])
        sessions.append(
            {
                "file": str(path),
                "session_id": payload.get("sessionId"),
                "title_present": bool(payload.get("title")),
                "workspace_path": payload.get("workspacePath") or payload.get("workspaceDirectory"),
                "selected_model": selected_model,
                "default_model_title": payload.get("defaultModelTitle"),
                "session_type": session_type,
                "autonomy_mode": autonomy_mode,
                "usage_summary_enabled": payload.get("isUsageSummaryEnabled"),
                "context_usage_percent": payload.get("contextUsagePercentage"),
                "context_usage_by_session": payload.get("contextUsagePercentageBySession"),
                "initial_context_estimate": payload.get("initialContextEstimate"),
                "history_items": len(history) if isinstance(history, list) else 0,
                "message_like_history_items": count_message_like_items(history),
            }
        )

    return {
        "session_files_found": len(session_files),
        "sessions": sessions[:100],
        "selected_models": dict(selected_models),
        "session_types": dict(session_types),
        "autonomy_modes": dict(autonomy_modes),
    }


def iter_json_lines(path: Path) -> Iterable[dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                line = line.strip()
                if not line.startswith("{"):
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict):
                    yield payload
    except OSError:
        return


def model_from_message(message: Any) -> str | None:
    if isinstance(message, dict):
        model = message.get("modelId") or message.get("modelName")
        if model:
            return str(model)
    return None


def parse_chat_api_logs(log_files: list[Path]) -> dict[str, object]:
    """Parse Kiro Q Chat API logs for privacy-safe interaction metrics."""
    # Match both "Q Chat API.log" and rotated versions "Q Chat API.1.log", "Q Chat API.2.log", …
    chat_api_logs = [
        path for path in log_files
        if re.match(r".*Q Chat API(\.\d+)?\.log$", path.name)
    ]
    request_queue: list[dict[str, object]] = []
    turns: list[dict[str, object]] = []

    conversation_ids: set[str] = set()
    request_ids: set[str] = set()
    request_models: Counter[str] = Counter()
    response_models: Counter[str] = Counter()
    chat_trigger_types: Counter[str] = Counter()
    http_statuses: Counter[str] = Counter()
    total_stream_events = 0
    total_tool_use_events = 0
    total_credits = 0.0

    for path in sorted(chat_api_logs):
        for payload in iter_json_lines(path):
            request = payload.get("request")
            if isinstance(request, dict):
                conversation_state = request.get("conversationState", {})
                if not isinstance(conversation_state, dict):
                    continue

                conversation_id = conversation_state.get("conversationId")
                if conversation_id:
                    conversation_ids.add(str(conversation_id))

                trigger = conversation_state.get("chatTriggerType")
                if trigger:
                    chat_trigger_types[str(trigger)] += 1

                current_message = (
                    conversation_state.get("currentMessage", {}).get("userInputMessage", {})
                    if isinstance(conversation_state.get("currentMessage"), dict)
                    else {}
                )
                prompt_text = current_message.get("content", "") if isinstance(current_message, dict) else ""
                request_model = model_from_message(current_message)
                if request_model:
                    request_models[request_model] += 1

                history = conversation_state.get("history", [])
                if isinstance(history, list):
                    for item in history:
                        if not isinstance(item, dict):
                            continue
                        history_model = model_from_message(item.get("userInputMessage"))
                        if history_model:
                            request_models[history_model] += 1

                request_queue.append(
                    {
                        "source_log": str(path),
                        "conversation_id": conversation_id,
                        "request_model": request_model,
                        "input_chars": len(prompt_text) if isinstance(prompt_text, str) else 0,
                        "history_items": len(history) if isinstance(history, list) else 0,
                        "chat_trigger_type": trigger,
                    }
                )
                continue

            response = payload.get("response")
            if not isinstance(response, dict):
                continue

            queued_request = request_queue.pop(0) if request_queue else {}
            metadata = response.get("metadata", {})
            request_id = metadata.get("requestId") if isinstance(metadata, dict) else None
            if request_id:
                request_ids.add(str(request_id))
            status = metadata.get("httpStatusCode") if isinstance(metadata, dict) else None
            if status:
                http_statuses[str(status)] += 1

            full_response = response.get("fullResponse", "")
            output_chars = len(full_response) if isinstance(full_response, str) else 0

            events = response.get("events", [])
            turn_models: set[str] = set()
            turn_credits = 0.0
            context_usage_events: list[dict[str, object]] = []
            tool_use_events = 0
            stream_events = len(events) if isinstance(events, list) else 0
            total_stream_events += stream_events

            if isinstance(events, list):
                for event in events:
                    if not isinstance(event, dict):
                        continue
                    if "toolUseEvent" in event:
                        tool_use_events += 1
                    metering = event.get("meteringEvent")
                    if isinstance(metering, dict) and str(metering.get("unit", "")).lower() == "credit":
                        usage = as_float(metering.get("usage"))
                        if usage is not None:
                            turn_credits += usage
                    context_usage = event.get("contextUsageEvent")
                    if isinstance(context_usage, dict):
                        context_usage_events.append(context_usage)
                    for value in event.values():
                        model = model_from_message(value)
                        if model:
                            turn_models.add(model)
                            response_models[model] += 1

            total_tool_use_events += tool_use_events
            total_credits += turn_credits

            input_chars = int(queued_request.get("input_chars", 0) or 0)
            turns.append(
                {
                    "source_log": queued_request.get("source_log"),
                    "conversation_id": queued_request.get("conversation_id"),
                    "request_id": request_id,
                    "http_status": status,
                    "request_model": queued_request.get("request_model"),
                    "response_models": sorted(turn_models),
                    "chat_trigger_type": queued_request.get("chat_trigger_type"),
                    "history_items": queued_request.get("history_items", 0),
                    "input_chars": input_chars,
                    "output_chars": output_chars,
                    "estimated_input_tokens_chars_div_4": round(input_chars / 4),
                    "estimated_output_tokens_chars_div_4": round(output_chars / 4),
                    "credits_used": turn_credits,
                    "stream_events": stream_events,
                    "tool_use_events": tool_use_events,
                    "context_usage_events": context_usage_events,
                }
            )

    return {
        "chat_api_logs_found": len(chat_api_logs),
        "chat_api_log_files": [str(path) for path in chat_api_logs[:100]],
        "conversation_count": len(conversation_ids),
        "conversations": sorted(conversation_ids),
        "request_count": len(turns),
        "response_count": len(turns),
        "request_ids": sorted(request_ids),
        "request_id_count": len(request_ids),
        "request_models": dict(request_models),
        "response_models": dict(response_models),
        "chat_trigger_types": dict(chat_trigger_types),
        "http_statuses": dict(http_statuses),
        "stream_events": total_stream_events,
        "tool_use_events": total_tool_use_events,
        "credits_used": total_credits,
        "estimated_input_tokens": sum(turn["estimated_input_tokens_chars_div_4"] for turn in turns),
        "estimated_output_tokens": sum(turn["estimated_output_tokens_chars_div_4"] for turn in turns),
        "turns": turns[:250],
    }


def collect_kiro_metrics() -> dict[str, object]:
    roots = candidate_log_roots()
    session_roots = candidate_session_roots()
    log_files = iter_log_files(roots)
    session_files = iter_session_files(session_roots)
    parsed = parse_logs(log_files)
    sessions = parse_session_files(session_files)
    chat_api = parse_chat_api_logs(log_files)

    data = {
        **parsed["counters"],
        "log_files_found": len(log_files),
        "session_files_found": sessions["session_files_found"],
        "chat_api_logs_found": chat_api["chat_api_logs_found"],
        "kiro_conversations": chat_api["conversation_count"],
        "kiro_requests": chat_api["request_count"],
        "kiro_responses": chat_api["response_count"],
        "kiro_request_ids": chat_api["request_id_count"],
        "kiro_credits_used": chat_api["credits_used"],
        "kiro_estimated_input_tokens": chat_api["estimated_input_tokens"],
        "kiro_estimated_output_tokens": chat_api["estimated_output_tokens"],
        "kiro_tool_use_events": chat_api["tool_use_events"],
        "kiro_stream_events": chat_api["stream_events"],
    }

    return {
        "collection_timestamp": datetime.now().isoformat(),
        "collection_method": "kiro_local_log_and_session_scan",
        "privacy_note": "Raw prompt and response text is not stored. Token counts are estimated from character counts unless Kiro exposes exact values in logs.",
        "log_roots_checked": [str(root) for root in roots],
        "session_roots_checked": [str(root) for root in session_roots],
        "logs_found": bool(log_files),
        "log_files": [str(path) for path in log_files[:100]],
        "data": data,
        "sessions": sessions,
        "chat_api": chat_api,
        "interactions": parsed["interactions"],
    }


def build_output_path(
    explicit_output: str | None, participant_id: str | None, session_id: str | None
) -> Path | None:
    if explicit_output:
        return Path(explicit_output)
    if participant_id and session_id:
        return Path(f"DATA_COLLECTION/kiro_metrics_{participant_id}_{session_id}.json")
    if participant_id:
        return Path(f"DATA_COLLECTION/kiro_metrics_{participant_id}.json")
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect best-effort Kiro activity metrics")
    parser.add_argument("-o", "--output", type=str, help="Output JSON file path")
    parser.add_argument("--participant-id", type=str, help="Participant ID")
    parser.add_argument("--session-id", type=str, help="Session ID")
    args = parser.parse_args()

    metrics = collect_kiro_metrics()
    output_path = build_output_path(args.output, args.participant_id, args.session_id)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(metrics, handle, indent=2)
        print(f"Kiro metrics saved to: {output_path}")
        print(f"Detected events: {metrics['data']['total_detected_events']}")
        return 0

    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
