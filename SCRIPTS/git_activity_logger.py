#!/usr/bin/env python3
"""Extract Git activity metrics from repository.

This script analyzes Git commit history to extract metrics such as commit
frequency, commit size, branch activity, and merge events.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_git_command(cmd, repo_path="."):
    """Run a git command and return output.
    
    Args:
        cmd: Git command (list of strings)
        repo_path: Path to git repository
    
    Returns:
        Command output as string
    """
    try:
        result = subprocess.run(
            ["git"] + cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {e}", file=sys.stderr)
        return ""
    except FileNotFoundError:
        print("Error: git not found. Make sure git is installed.", file=sys.stderr)
        return ""


def get_commit_count(repo_path=".", since=None, until=None):
    """Get total commit count.
    
    Args:
        repo_path: Path to git repository
        since: Start date (ISO format or relative like "1 day ago")
        until: End date (ISO format or relative)
    
    Returns:
        Number of commits
    """
    cmd = ["rev-list", "--count", "HEAD"]
    if since:
        cmd.extend(["--since", since])
    if until:
        cmd.extend(["--until", until])
    
    output = run_git_command(cmd, repo_path)
    return int(output) if output.isdigit() else 0


def get_commit_frequency(repo_path=".", since=None, until=None):
    """Calculate commits per hour.
    
    Args:
        repo_path: Path to git repository
        since: Start date
        until: End date
    
    Returns:
        Commits per hour (float)
    """
    count = get_commit_count(repo_path, since, until)
    
    if not since or not until:
        # If no time range specified, use all commits
        # Estimate time range from first to last commit
        first_commit = run_git_command(
            ["log", "--reverse", "--format=%ct", "HEAD"], repo_path
        )
        last_commit = run_git_command(
            ["log", "-1", "--format=%ct", "HEAD"], repo_path
        )
        
        if first_commit and last_commit:
            try:
                first_time = int(first_commit.split("\n")[0])
                last_time = int(last_commit)
                hours = (last_time - first_time) / 3600
                return count / hours if hours > 0 else 0
            except (ValueError, IndexError):
                pass
    
    return 0


def get_commit_stats(repo_path="."):
    """Get commit statistics including size (lines added/removed).
    
    Args:
        repo_path: Path to git repository
    
    Returns:
        List of commit statistics
    """
    cmd = [
        "log",
        "--format=%H|%ct|%an|%s",
        "--numstat",
        "HEAD"
    ]
    
    output = run_git_command(cmd, repo_path)
    commits = []
    
    current_commit = None
    for line in output.split("\n"):
        if "|" in line and not line.startswith("\t"):
            # New commit
            if current_commit:
                commits.append(current_commit)
            
            parts = line.split("|")
            if len(parts) >= 4:
                current_commit = {
                    "hash": parts[0],
                    "timestamp": int(parts[1]),
                    "author": parts[2],
                    "message": parts[3],
                    "files_changed": 0,
                    "lines_added": 0,
                    "lines_removed": 0,
                }
        elif current_commit and line.startswith("\t"):
            # File stats
            parts = line.split("\t")
            if len(parts) >= 3:
                try:
                    added = int(parts[0]) if parts[0] != "-" else 0
                    removed = int(parts[1]) if parts[1] != "-" else 0
                    current_commit["files_changed"] += 1
                    current_commit["lines_added"] += added
                    current_commit["lines_removed"] += removed
                except ValueError:
                    pass
    
    if current_commit:
        commits.append(current_commit)
    
    return commits


def get_branch_activity(repo_path="."):
    """Get branch activity information.
    
    Args:
        repo_path: Path to git repository
    
    Returns:
        Branch activity statistics
    """
    branches = run_git_command(["branch", "-a"], repo_path).split("\n")
    branches = [b.strip() for b in branches if b.strip()]
    
    current_branch = run_git_command(["rev-parse", "--abbrev-ref", "HEAD"], repo_path)
    
    return {
        "total_branches": len(branches),
        "current_branch": current_branch,
        "branches": branches,
    }


def get_merge_events(repo_path="."):
    """Get merge commit events.
    
    Args:
        repo_path: Path to git repository
    
    Returns:
        List of merge events
    """
    cmd = [
        "log",
        "--merges",
        "--format=%H|%ct|%an|%s",
        "HEAD"
    ]
    
    output = run_git_command(cmd, repo_path)
    merges = []
    
    for line in output.split("\n"):
        if "|" in line:
            parts = line.split("|")
            if len(parts) >= 4:
                merges.append({
                    "hash": parts[0],
                    "timestamp": int(parts[1]),
                    "author": parts[2],
                    "message": parts[3],
                })
    
    return merges


def analyze_git_activity(repo_path=".", since=None, until=None):
    """Analyze all Git activity.
    
    Args:
        repo_path: Path to git repository
        since: Start date
        until: End date
    
    Returns:
        Dictionary with all metrics
    """
    commits = get_commit_stats(repo_path)
    
    # Filter by date range if specified
    if since or until:
        filtered_commits = []
        for commit in commits:
            commit_time = datetime.fromtimestamp(commit["timestamp"])
            if since:
                since_time = datetime.fromisoformat(since.replace("Z", "+00:00"))
                if commit_time < since_time:
                    continue
            if until:
                until_time = datetime.fromisoformat(until.replace("Z", "+00:00"))
                if commit_time > until_time:
                    continue
            filtered_commits.append(commit)
        commits = filtered_commits
    
    total_lines_added = sum(c["lines_added"] for c in commits)
    total_lines_removed = sum(c["lines_removed"] for c in commits)
    total_files_changed = sum(c["files_changed"] for c in commits)
    
    return {
        "analysis_timestamp": datetime.now().isoformat(),
        "repository_path": str(Path(repo_path).absolute()),
        "time_range": {
            "since": since,
            "until": until,
        },
        "summary": {
            "total_commits": len(commits),
            "commits_per_hour": get_commit_frequency(repo_path, since, until),
            "total_lines_added": total_lines_added,
            "total_lines_removed": total_lines_removed,
            "total_files_changed": total_files_changed,
            "average_commit_size": {
                "lines_added": total_lines_added / len(commits) if commits else 0,
                "lines_removed": total_lines_removed / len(commits) if commits else 0,
                "files_changed": total_files_changed / len(commits) if commits else 0,
            },
        },
        "branch_activity": get_branch_activity(repo_path),
        "merge_events": get_merge_events(repo_path),
        "commits": commits,
    }


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Extract Git activity metrics from repository"
    )
    parser.add_argument(
        "-r", "--repo",
        type=str,
        default=".",
        help="Path to git repository (default: current directory)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="DATA_COLLECTION/git_activity.json",
        help="Output JSON file path"
    )
    parser.add_argument(
        "--participant-id",
        type=str,
        help="Participant ID to include in filename"
    )
    parser.add_argument(
        "--since",
        type=str,
        help="Start date (ISO format or relative like '1 day ago')"
    )
    parser.add_argument(
        "--until",
        type=str,
        help="End date (ISO format or relative)"
    )
    
    args = parser.parse_args()
    
    # Determine output path
    output_path = Path(args.output)
    if args.participant_id:
        output_path = Path(f"DATA_COLLECTION/git_activity_{args.participant_id}.json")
    
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Analyze Git activity
    print(f"Analyzing Git activity in: {args.repo}")
    activity = analyze_git_activity(args.repo, args.since, args.until)
    
    # Write to file
    with open(output_path, "w") as f:
        json.dump(activity, f, indent=2)
    
    # Print summary
    print(f"\nGit Activity Summary:")
    print(f"  Total commits: {activity['summary']['total_commits']}")
    print(f"  Commits per hour: {activity['summary']['commits_per_hour']:.2f}")
    print(f"  Total lines added: {activity['summary']['total_lines_added']}")
    print(f"  Total lines removed: {activity['summary']['total_lines_removed']}")
    print(f"  Total files changed: {activity['summary']['total_files_changed']}")
    print(f"  Branches: {activity['branch_activity']['total_branches']}")
    print(f"  Merge events: {len(activity['merge_events'])}")
    print(f"\nData saved to: {output_path}")


if __name__ == "__main__":
    main()
