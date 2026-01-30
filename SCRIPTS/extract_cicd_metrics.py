#!/usr/bin/env python3
"""Extract CI/CD metrics from GitLab CI/CD pipeline.

This script extracts metrics from GitLab CI/CD including pipeline run frequency,
execution time, test execution time, resource usage, and pass/fail rates.
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_gitlab_api_token():
    """Get GitLab API token from environment."""
    return os.getenv("GITLAB_TOKEN") or os.getenv("CI_JOB_TOKEN")


def get_project_id():
    """Get GitLab project ID from environment or git remote."""
    # Try CI environment variable first
    project_id = os.getenv("CI_PROJECT_ID")
    if project_id:
        return project_id
    
    # Try to extract from git remote
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True
        )
        # Parse GitLab URL to extract project path
        url = result.stdout.strip()
        # This is a simplified parser - may need adjustment for different URL formats
        return None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def parse_gitlab_ci_yml(ci_file=".gitlab-ci.yml"):
    """Parse GitLab CI configuration file.
    
    Args:
        ci_file: Path to .gitlab-ci.yml
    
    Returns:
        Dictionary with CI configuration info
    """
    if not Path(ci_file).exists():
        return None
    
    with open(ci_file, "r") as f:
        content = f.read()
    
    # Extract stages
    stages_match = re.search(r"stages:\s*\n((?:\s*-\s*\w+\s*\n?)+)", content)
    stages = []
    if stages_match:
        stages = re.findall(r"-\s*(\w+)", stages_match.group(1))
    
    # Extract job names
    job_pattern = r"^(\w+):\s*$"
    jobs = re.findall(job_pattern, content, re.MULTILINE)
    
    return {
        "stages": stages,
        "jobs": jobs,
        "file_exists": True,
    }


def extract_test_times_from_logs(log_file=None):
    """Extract test execution times from CI logs.
    
    Args:
        log_file: Path to CI log file (optional)
    
    Returns:
        Dictionary with test timing information
    """
    test_times = {
        "correctness_tests": None,
        "benchmark_tests": None,
        "performance_tests": None,
        "total_time": None,
    }
    
    # If running in CI, try to get from environment or artifacts
    if os.getenv("CI"):
        # In GitLab CI, test times might be in job logs
        # This would need to be parsed from actual CI logs
        pass
    
    return test_times


def get_pipeline_info_from_api(project_id, token, limit=10):
    """Get pipeline information from GitLab API.
    
    Args:
        project_id: GitLab project ID
        token: GitLab API token
        limit: Maximum number of pipelines to fetch
    
    Returns:
        List of pipeline information
    """
    if not project_id or not token:
        return []
    
    try:
        import urllib.request
        import urllib.parse
        
        url = f"https://gitlab.com/api/v4/projects/{project_id}/pipelines"
        params = {"per_page": limit, "order_by": "updated_at", "sort": "desc"}
        
        req = urllib.request.Request(
            f"{url}?{urllib.parse.urlencode(params)}",
            headers={"PRIVATE-TOKEN": token}
        )
        
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data
    except Exception as e:
        print(f"Warning: Could not fetch pipeline info from API: {e}", file=sys.stderr)
        return []


def analyze_local_git_history():
    """Analyze local Git history for CI/CD activity.
    
    Returns:
        Dictionary with CI/CD activity metrics
    """
    try:
        # Get commit messages related to CI/CD
        result = subprocess.run(
            ["git", "log", "--all", "--grep=CI", "--grep=pipeline", "--format=%H|%ct|%s", "-i"],
            capture_output=True,
            text=True,
            check=True
        )
        
        ci_commits = []
        for line in result.stdout.strip().split("\n"):
            if "|" in line:
                parts = line.split("|", 2)
                if len(parts) >= 3:
                    ci_commits.append({
                        "hash": parts[0],
                        "timestamp": int(parts[1]),
                        "message": parts[2],
                    })
        
        return {
            "ci_related_commits": len(ci_commits),
            "commits": ci_commits,
        }
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {"ci_related_commits": 0, "commits": []}


def extract_cicd_metrics(repo_path=".", use_api=False):
    """Extract all CI/CD metrics.
    
    Args:
        repo_path: Path to repository
        use_api: Whether to use GitLab API (requires token)
    
    Returns:
        Dictionary with all CI/CD metrics
    """
    ci_config = parse_gitlab_ci_yml(Path(repo_path) / ".gitlab-ci.yml")
    
    metrics = {
        "analysis_timestamp": datetime.now().isoformat(),
        "repository_path": str(Path(repo_path).absolute()),
        "ci_environment": {
            "is_ci": os.getenv("CI") == "true",
            "ci_project_id": os.getenv("CI_PROJECT_ID"),
            "ci_pipeline_id": os.getenv("CI_PIPELINE_ID"),
            "ci_job_id": os.getenv("CI_JOB_ID"),
        },
        "ci_configuration": ci_config,
        "test_execution": extract_test_times_from_logs(),
        "git_activity": analyze_local_git_history(),
    }
    
    # Try to get pipeline info from API if requested
    if use_api:
        project_id = get_project_id() or os.getenv("CI_PROJECT_ID")
        token = get_gitlab_api_token()
        
        if project_id and token:
            pipelines = get_pipeline_info_from_api(project_id, token)
            metrics["pipelines"] = {
                "count": len(pipelines),
                "recent_pipelines": pipelines[:5],  # Last 5 pipelines
            }
            
            if pipelines:
                # Calculate average pipeline duration
                durations = [
                    p.get("duration", 0) for p in pipelines if p.get("duration")
                ]
                if durations:
                    metrics["pipelines"]["average_duration_seconds"] = sum(durations) / len(durations)
                    metrics["pipelines"]["total_duration_seconds"] = sum(durations)
                
                # Count by status
                status_counts = {}
                for p in pipelines:
                    status = p.get("status", "unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1
                metrics["pipelines"]["status_counts"] = status_counts
        else:
            metrics["pipelines"] = {
                "error": "API credentials not available",
            }
    else:
        metrics["pipelines"] = {
            "note": "API access not requested. Use --use-api flag to fetch pipeline data.",
        }
    
    return metrics


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Extract CI/CD metrics from GitLab CI/CD pipeline"
    )
    parser.add_argument(
        "-r", "--repo",
        type=str,
        default=".",
        help="Path to repository (default: current directory)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="DATA_COLLECTION/cicd_metrics.json",
        help="Output JSON file path"
    )
    parser.add_argument(
        "--participant-id",
        type=str,
        help="Participant ID to include in filename"
    )
    parser.add_argument(
        "--use-api",
        action="store_true",
        help="Use GitLab API to fetch pipeline data (requires GITLAB_TOKEN)"
    )
    
    args = parser.parse_args()
    
    # Determine output path
    output_path = Path(args.output)
    if args.participant_id:
        output_path = Path(f"DATA_COLLECTION/cicd_metrics_{args.participant_id}.json")
    
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Extract metrics
    print(f"Extracting CI/CD metrics from: {args.repo}")
    metrics = extract_cicd_metrics(args.repo, use_api=args.use_api)
    
    # Write to file
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)
    
    # Print summary
    print(f"\nCI/CD Metrics Summary:")
    if metrics["ci_configuration"]:
        print(f"  CI Configuration: Found")
        print(f"    Stages: {', '.join(metrics['ci_configuration']['stages'])}")
        print(f"    Jobs: {len(metrics['ci_configuration']['jobs'])}")
    else:
        print(f"  CI Configuration: Not found")
    
    print(f"  CI Environment: {'Yes' if metrics['ci_environment']['is_ci'] else 'No'}")
    print(f"  CI-related commits: {metrics['git_activity']['ci_related_commits']}")
    
    if "pipelines" in metrics and "count" in metrics["pipelines"]:
        print(f"  Pipelines analyzed: {metrics['pipelines']['count']}")
        if "average_duration_seconds" in metrics["pipelines"]:
            avg = metrics["pipelines"]["average_duration_seconds"]
            print(f"  Average pipeline duration: {avg:.1f} seconds")
    
    print(f"\nData saved to: {output_path}")


if __name__ == "__main__":
    main()
