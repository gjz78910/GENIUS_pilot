#!/usr/bin/env python3
"""Collect exact Bedrock token counts from CloudTrail for one GENIUS VM."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def get_self_instance_id() -> str:
    request = urllib.request.Request(
        "http://169.254.169.254/latest/api/token",
        method="PUT",
        headers={"X-aws-ec2-metadata-token-ttl-seconds": "60"},
    )
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            token = response.read().decode("utf-8")
        meta = urllib.request.Request(
            "http://169.254.169.254/latest/meta-data/instance-id",
            headers={"X-aws-ec2-metadata-token": token},
        )
        with urllib.request.urlopen(meta, timeout=2) as response:
            return response.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError("Could not read EC2 instance id from metadata service") from exc


def run_aws(args: list[str]) -> dict[str, Any]:
    completed = subprocess.run(args, check=True, text=True, capture_output=True)
    return json.loads(completed.stdout)


def lookup_events(
    event_name: str,
    region: str,
    profile: str | None,
    start_time: str | None,
    end_time: str | None,
) -> list[dict[str, Any]]:
    base = [
        "aws",
        "cloudtrail",
        "lookup-events",
        "--region",
        region,
        "--lookup-attributes",
        f"AttributeKey=EventName,AttributeValue={event_name}",
        "--max-results",
        "50",
        "--output",
        "json",
    ]
    if profile:
        base[1:1] = ["--profile", profile]
    if start_time:
        base.extend(["--start-time", start_time])
    if end_time:
        base.extend(["--end-time", end_time])

    events: list[dict[str, Any]] = []
    next_token: str | None = None
    while True:
        command = list(base)
        if next_token:
            command.extend(["--next-token", next_token])
        page = run_aws(command)
        events.extend(page.get("Events", []))
        next_token = page.get("NextToken")
        if not next_token:
            return events


def event_belongs_to_instance(event: dict[str, Any], instance_id: str) -> bool:
    identity = event.get("userIdentity", {})
    principal = str(identity.get("principalId", ""))
    issued_to = str(identity.get("inScopeOf", {}).get("credentialsIssuedTo", ""))
    return principal.endswith(f":{instance_id}") or instance_id in issued_to


def extract_records(events: list[dict[str, Any]], instance_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    token_events: list[dict[str, Any]] = []
    failed_events: list[dict[str, Any]] = []
    for wrapper in events:
        try:
            event = json.loads(wrapper.get("CloudTrailEvent", "{}"))
        except json.JSONDecodeError:
            continue
        if not event_belongs_to_instance(event, instance_id):
            continue

        additional = event.get("additionalEventData") or {}
        input_tokens = additional.get("inputTokens")
        output_tokens = additional.get("outputTokens")
        record = {
            "event_time": event.get("eventTime"),
            "event_name": event.get("eventName"),
            "request_id": event.get("requestID"),
            "model_id": (event.get("requestParameters") or {}).get("modelId"),
            "inference_region": additional.get("inferenceRegion"),
            "input_tokens": input_tokens if isinstance(input_tokens, int) else 0,
            "output_tokens": output_tokens if isinstance(output_tokens, int) else 0,
        }
        if "errorCode" in event:
            record["error_code"] = event.get("errorCode")
            record["error_message"] = event.get("errorMessage")
            failed_events.append(record)
        elif isinstance(input_tokens, int) or isinstance(output_tokens, int):
            token_events.append(record)
    return token_events, failed_events


def summarize(token_events: list[dict[str, Any]]) -> dict[str, Any]:
    by_model: dict[str, dict[str, int]] = defaultdict(lambda: {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "events": 0})
    by_region: dict[str, dict[str, int]] = defaultdict(lambda: {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "events": 0})

    total_input = 0
    total_output = 0
    for event in token_events:
        input_tokens = int(event["input_tokens"])
        output_tokens = int(event["output_tokens"])
        total_input += input_tokens
        total_output += output_tokens
        for bucket, key in ((by_model, event.get("model_id") or "unknown"), (by_region, event.get("inference_region") or "unknown")):
            bucket[key]["input_tokens"] += input_tokens
            bucket[key]["output_tokens"] += output_tokens
            bucket[key]["total_tokens"] += input_tokens + output_tokens
            bucket[key]["events"] += 1

    return {
        "input_tokens": total_input,
        "output_tokens": total_output,
        "total_tokens": total_input + total_output,
        "token_event_count": len(token_events),
        "by_model": dict(by_model),
        "by_inference_region": dict(by_region),
    }


def output_path(output: str | None, participant_id: str | None, session_id: str | None) -> Path | None:
    if output:
        return Path(output)
    if participant_id and session_id:
        return Path(f"DATA_COLLECTION/bedrock_token_usage_{participant_id}_{session_id}.json")
    if participant_id:
        return Path(f"DATA_COLLECTION/bedrock_token_usage_{participant_id}.json")
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect Bedrock token usage from CloudTrail")
    parser.add_argument("--participant-id")
    parser.add_argument("--session-id")
    parser.add_argument("--instance-id", default="self", help="EC2 instance id, or 'self' on a VM")
    parser.add_argument("--region", default=os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "eu-west-2")
    parser.add_argument("--profile", help="AWS profile for organiser-side collection")
    parser.add_argument("--start-time", help="CloudTrail lookup start time, e.g. 2026-09-02T23:00:00Z")
    parser.add_argument("--end-time", help="CloudTrail lookup end time")
    parser.add_argument("-o", "--output")
    args = parser.parse_args()

    instance_id = get_self_instance_id() if args.instance_id == "self" else args.instance_id
    wrappers: list[dict[str, Any]] = []
    for event_name in ("InvokeModel", "InvokeModelWithResponseStream"):
        wrappers.extend(lookup_events(event_name, args.region, args.profile, args.start_time, args.end_time))

    token_events, failed_events = extract_records(wrappers, instance_id)
    result = {
        "collection_timestamp": utc_now(),
        "collection_method": "cloudtrail_bedrock_invoke_model_additional_event_data",
        "participant_id": args.participant_id,
        "session_id": args.session_id,
        "instance_id": instance_id,
        "region": args.region,
        "start_time": args.start_time,
        "end_time": args.end_time,
        "summary": summarize(token_events),
        "token_events": token_events,
        "failed_events": failed_events,
    }

    path = output_path(args.output, args.participant_id, args.session_id)
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"Bedrock token usage saved to: {path}")
        print(f"Input tokens: {result['summary']['input_tokens']}")
        print(f"Output tokens: {result['summary']['output_tokens']}")
        print(f"Total tokens: {result['summary']['total_tokens']}")
    else:
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
