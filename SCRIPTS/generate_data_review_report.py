#!/usr/bin/env python3
"""Generate a single-page HTML review report from one participant's collected data.

The individual DATA_COLLECTION JSON files are correct but not easy for a human
to skim. This script reads whatever files exist for a participant (checkpoints,
token usage, energy/carbon, git/CI/CD/code-quality, system info, screen
recordings) and renders them as one self-contained HTML dashboard, so an
organiser can review a session at a glance instead of opening a dozen JSON
files by hand.

Usage:
    python SCRIPTS/generate_data_review_report.py --participant-id ai-99
    python SCRIPTS/generate_data_review_report.py --participant-id ai-99 --session-id DRYRUN \
        --data-dir DATA_COLLECTION --output DATA_COLLECTION/review_ai-99.html

Missing files are skipped, not treated as errors: an organiser may run this
midway through data collection or on best-effort data.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any, Optional


def find_one(data_dir: Path, participant_id: str, prefix: str, session_id: Optional[str]) -> Optional[Path]:
    """Find a single JSON file for this participant, trying the session-qualified
    name first (e.g. Task1_cp1_ai-99_DRYRUN.json), then the bare name
    (e.g. system_info_ai-99.json). Naming isn't fully consistent across the
    pipeline's scripts, so both forms are checked.
    """
    candidates = []
    if session_id:
        candidates.append(data_dir / f"{prefix}_{participant_id}_{session_id}.json")
    candidates.append(data_dir / f"{prefix}_{participant_id}.json")
    for path in candidates:
        if path.exists():
            return path
    matches = sorted(data_dir.glob(f"{prefix}_{participant_id}*.json"))
    return matches[0] if matches else None


def load_json(path: Optional[Path]) -> Optional[dict]:
    if not path or not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError):
        return None


def find_videos(data_dir: Path) -> list[Path]:
    videos_dir = data_dir / "screen_recordings"
    if not videos_dir.exists():
        return []
    return sorted(videos_dir.glob("*.mp4"))


def find_video_metadata(data_dir: Path, participant_id: str, session_id: Optional[str]) -> tuple[Optional[dict], Optional[list]]:
    """Look for the recorder's own metadata/segments JSON, checking both
    DATA_COLLECTION/ and DATA_COLLECTION/runtime/ (where submit_participant_work.sh
    copies the live runtime dir).
    """
    search_dirs = [data_dir, data_dir / "runtime"]
    metadata = None
    segments = None
    for d in search_dirs:
        if not d.exists():
            continue
        if metadata is None:
            meta_path = find_one(d, participant_id, "screen_recording", session_id)
            metadata = load_json(meta_path)
        seg_path = d / "screen_recording_segments.json"
        if segments is None and seg_path.exists():
            segments = load_json(seg_path)
    return metadata, segments


def fmt(value: Any, default: str = "—") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:,.4f}".rstrip("0").rstrip(".")
    if isinstance(value, list):
        return f"{len(value)} item(s)" if value else "none"
    if isinstance(value, dict):
        return json.dumps(value)
    return str(value)


def status_badge(status: str) -> str:
    css_class = {
        "PASS": "badge-pass",
        "PARTIAL": "badge-partial",
        "FAIL": "badge-fail",
    }.get(status, "badge-unknown")
    return f'<span class="badge {css_class}">{escape(status or "NOT RUN")}</span>'


def render_checkpoints(data_dir: Path, participant_id: str, session_id: Optional[str]) -> str:
    completion = load_json(find_one(data_dir, participant_id, "completion_report", session_id))
    checkpoints = completion.get("checkpoints", []) if completion else []

    if not checkpoints:
        return '<p class="muted">No completion_report file found for this participant.</p>'

    rows = []
    for cp in checkpoints:
        rows.append(
            f"<tr><td>{escape(cp.get('checkpoint', ''))}</td>"
            f"<td>{status_badge(cp.get('status', ''))}</td>"
            f"<td>{fmt(cp.get('tests_run'))}</td>"
            f"<td>{fmt(cp.get('failures'))}</td>"
            f"<td>{fmt(cp.get('errors'))}</td>"
            f"<td>{'yes' if cp.get('timed_out') else 'no'}</td></tr>"
        )

    all_pass = all(cp.get("status") == "PASS" for cp in checkpoints)
    summary_badge = status_badge("PASS" if all_pass else "PARTIAL")

    return f"""
    <p>Overall: {summary_badge} ({sum(1 for c in checkpoints if c.get('status') == 'PASS')}/{len(checkpoints)} checkpoints passed)</p>
    <table>
      <thead><tr><th>Checkpoint</th><th>Status</th><th>Tests run</th><th>Failures</th><th>Errors</th><th>Timed out</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
    """


def render_token_usage(data_dir: Path, participant_id: str, session_id: Optional[str]) -> str:
    local = load_json(find_one(data_dir, participant_id, "claude_code_metrics", session_id))
    cloudtrail = load_json(find_one(data_dir, participant_id, "bedrock_token_usage", session_id))

    local_usage = (local or {}).get("data", {}).get("claude_usage_fields", {}) if local else {}
    ct_summary = (cloudtrail or {}).get("summary", {}) if cloudtrail else {}

    if not local and not cloudtrail:
        return '<p class="muted">No token usage files found.</p>'

    local_rows = "".join(
        f"<tr><td>{escape(k)}</td><td>{fmt(v)}</td></tr>" for k, v in local_usage.items()
    ) or "<tr><td colspan='2' class='muted'>No usage fields recorded</td></tr>"

    ct_rows = "".join(
        f"<tr><td>{escape(k)}</td><td>{fmt(v)}</td></tr>"
        for k, v in ct_summary.items()
        if k not in ("by_model", "by_inference_region")
    ) or "<tr><td colspan='2' class='muted'>No CloudTrail token events found</td></tr>"

    return f"""
    <div class="callout">
      <strong>Use the local transcript numbers as the real usage.</strong> AWS CloudTrail
      does not record token counts for streaming calls, which is how Claude Code makes
      almost all of its real requests — it only reliably confirms a call happened and
      which model served it, not how big it was.
    </div>
    <div class="two-col">
      <div>
        <h4>Local transcript (Claude Code's own record — trust this)</h4>
        <table><tbody>{local_rows}</tbody></table>
      </div>
      <div>
        <h4>AWS CloudTrail (incomplete — reference only)</h4>
        <table><tbody>{ct_rows}</tbody></table>
      </div>
    </div>
    """


def render_video(data_dir: Path, out_dir: Path, participant_id: str, session_id: Optional[str]) -> str:
    videos = find_videos(data_dir)
    metadata, segments = find_video_metadata(data_dir, participant_id, session_id)

    if not videos:
        return '<p class="muted">No screen recording found under screen_recordings/.</p>'

    info_bits = []
    if metadata:
        if metadata.get("screen_size"):
            info_bits.append(f"Resolution: {escape(metadata['screen_size'])}")
        if metadata.get("started_at") and metadata.get("stopped_at"):
            try:
                start = datetime.fromisoformat(metadata["started_at"].replace("Z", "+00:00"))
                stop = datetime.fromisoformat(metadata["stopped_at"].replace("Z", "+00:00"))
                info_bits.append(f"Duration: {(stop - start).total_seconds():.0f}s")
            except ValueError:
                pass
    if segments is not None:
        info_bits.append(f"Segments: {len(segments)}" + (" (recording restarted mid-session)" if len(segments) > 1 else " (no interruptions)"))

    info_line = " · ".join(info_bits) if info_bits else ""

    players = []
    for video in videos:
        try:
            rel = os.path.relpath(video, out_dir)
        except ValueError:
            rel = str(video)
        size_mb = video.stat().st_size / (1024 * 1024)
        players.append(
            f'<div class="video-block"><p><code>{escape(video.name)}</code> ({size_mb:.1f} MB)</p>'
            f'<video controls preload="metadata" src="{escape(rel)}"></video></div>'
        )

    return f"<p>{info_line}</p>" if not players else f"<p>{info_line}</p>" + "".join(players)


def render_kv_table(data: Optional[dict], keys: list[tuple[str, str]]) -> str:
    if not data:
        return '<p class="muted">No data file found.</p>'
    rows = []
    for label, key in keys:
        value = data
        for part in key.split("."):
            if isinstance(value, dict):
                value = value.get(part)
            else:
                value = None
                break
        rows.append(f"<tr><td>{escape(label)}</td><td>{fmt(value)}</td></tr>")
    return f"<table><tbody>{''.join(rows)}</tbody></table>"


def build_report(data_dir: Path, participant_id: str, session_id: Optional[str], out_path: Path) -> str:
    aggregated = load_json(find_one(data_dir, participant_id, "aggregated", session_id))
    energy = load_json(find_one(data_dir, participant_id, "energy_estimate", session_id))
    carbon = load_json(find_one(data_dir, participant_id, "carbon_footprint", session_id))
    git_activity = load_json(find_one(data_dir, participant_id, "git_activity", session_id))
    cicd = load_json(find_one(data_dir, participant_id, "cicd_metrics", session_id))
    quality = load_json(find_one(data_dir, participant_id, "code_quality", session_id))
    system_info = load_json(find_one(data_dir, participant_id, "system_info", session_id))

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    label = f"{participant_id}" + (f" / {session_id}" if session_id else "")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Data Review — {escape(label)}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         max-width: 960px; margin: 0 auto; padding: 32px 24px 80px; color: #1a1a1a; background: #fafafa; }}
  h1 {{ font-size: 22px; margin-bottom: 4px; }}
  h2 {{ font-size: 16px; margin: 36px 0 10px; padding-bottom: 6px; border-bottom: 2px solid #e5e5e5; }}
  h4 {{ font-size: 13px; margin: 0 0 8px; color: #555; }}
  .meta {{ color: #666; font-size: 13px; margin-bottom: 24px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; background: #fff; }}
  th, td {{ text-align: left; padding: 7px 10px; border-bottom: 1px solid #eee; }}
  th {{ background: #f2f2f2; font-weight: 600; }}
  .muted {{ color: #888; font-size: 13px; font-style: italic; }}
  .badge {{ display: inline-block; padding: 2px 10px; border-radius: 99px; font-size: 12px; font-weight: 700; }}
  .badge-pass {{ background: #dcfce7; color: #15803d; }}
  .badge-partial {{ background: #fef9c3; color: #a16207; }}
  .badge-fail {{ background: #fee2e2; color: #b91c1c; }}
  .badge-unknown {{ background: #e5e7eb; color: #4b5563; }}
  .callout {{ background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 6px; padding: 10px 14px; font-size: 13px; margin-bottom: 14px; }}
  .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
  .video-block {{ margin-top: 12px; }}
  video {{ width: 100%; max-width: 640px; border-radius: 6px; background: #000; margin-top: 6px; }}
  code {{ background: #f2f2f2; padding: 1px 5px; border-radius: 4px; font-size: 12px; }}
  section {{ background: #fff; border: 1px solid #eee; border-radius: 8px; padding: 4px 20px 20px; margin-bottom: 16px; }}
</style>
</head>
<body>
  <h1>Data Review — {escape(label)}</h1>
  <div class="meta">Generated {generated_at} from <code>{escape(str(data_dir))}</code></div>

  <section>
    <h2>Checkpoints</h2>
    {render_checkpoints(data_dir, participant_id, session_id)}
  </section>

  <section>
    <h2>Screen Recording</h2>
    {render_video(data_dir, out_path.parent, participant_id, session_id)}
  </section>

  <section>
    <h2>Token Usage</h2>
    {render_token_usage(data_dir, participant_id, session_id)}
  </section>

  <section>
    <h2>Energy &amp; Carbon</h2>
    <div class="two-col">
      <div>
        <h4>Energy</h4>
        {render_kv_table(energy, [
            ("Duration (hours)", "duration.total_hours"),
            ("Active (hours)", "duration.active_hours"),
            ("Avg CPU %", "resource_usage.avg_cpu_percent"),
            ("Avg memory (GB)", "resource_usage.avg_memory_gb"),
            ("Total energy (kWh)", "total_energy.kwh"),
        ])}
      </div>
      <div>
        <h4>Carbon</h4>
        {render_kv_table(carbon, [
            ("Location", "location"),
            ("Grid factor (kg CO2/kWh)", "grid_emission_factor"),
            ("Energy emissions (kg CO2)", "energy.emissions_kg_co2"),
            ("Total emissions (kg CO2)", "total.emissions_kg_co2"),
        ])}
      </div>
    </div>
  </section>

  <section>
    <h2>Git / CI-CD / Code Quality</h2>
    <div class="two-col">
      <div>
        <h4>Git activity</h4>
        {render_kv_table(git_activity, [
            ("Total commits", "summary.total_commits"),
            ("Total files changed", "summary.total_files_changed"),
            ("Lines added / removed", "summary.total_lines_added"),
            ("Branches", "branch_activity.total_branches"),
            ("Merge events", "merge_events"),
        ])}
        <h4 style="margin-top:16px;">CI/CD</h4>
        {render_kv_table(cicd, [
            ("CI configuration found", "ci_configuration"),
            ("Running in a CI environment", "ci_environment.is_ci"),
            ("CI-related commits", "git_activity.ci_related_commits"),
        ])}
      </div>
      <div>
        <h4>Code quality</h4>
        {render_kv_table(quality, [
            ("Overall quality score", "overall_quality_score"),
            ("Avg cyclomatic complexity", "radon.cyclomatic_complexity.average"),
            ("Max cyclomatic complexity", "radon.cyclomatic_complexity.max"),
            ("Avg maintainability index", "radon.maintainability_index.average"),
            ("Pydocstyle issues", "pydocstyle.total_issues"),
        ])}
      </div>
    </div>
  </section>

  <section>
    <h2>System Info</h2>
    {render_kv_table(system_info, [
        ("CPU model", "cpu.model"),
        ("CPU cores (logical)", "cpu.cores_logical"),
        ("Memory total (GB)", "memory.total_gb"),
        ("GPU present", "gpu.present"),
        ("OS", "os.system"),
        ("OS release", "os.release"),
        ("Python", "python.version"),
    ])}
  </section>

  <section>
    <h2>Aggregated Summary</h2>
    {render_kv_table((aggregated or {}).get("summary"), [
        (k.replace("_", " ").title(), k)
        for k in (aggregated or {}).get("summary", {}).keys()
    ]) if aggregated else '<p class="muted">No aggregated_&lt;ID&gt;.json file found.</p>'}
  </section>

</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an HTML review report for one participant's collected data.")
    parser.add_argument("--participant-id", required=True)
    parser.add_argument("--session-id", default=None)
    parser.add_argument("--data-dir", default="DATA_COLLECTION")
    parser.add_argument("--output", default=None, help="Output HTML path (default: <data-dir>/review_<ID>[_<SESSION>].html)")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        print(f"Data directory not found: {data_dir}", file=sys.stderr)
        return 1

    suffix = f"_{args.session_id}" if args.session_id else ""
    output = Path(args.output) if args.output else data_dir / f"review_{args.participant_id}{suffix}.html"

    html = build_report(data_dir, args.participant_id, args.session_id, output)
    output.write_text(html, encoding="utf-8")
    print(f"Report written to: {output}")
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(main())
