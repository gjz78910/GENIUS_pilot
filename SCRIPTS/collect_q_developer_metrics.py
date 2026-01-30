#!/usr/bin/env python3
"""Collect Amazon Q Developer telemetry metrics.

This script attempts to collect metrics from Amazon Q Developer plugin including:
- AI query frequency
- Suggestions accepted/rejected count
- AI interaction timestamps
- Compute cycles (if available)

Note: This requires investigation of Q Developer plugin logs/API.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def find_vscode_logs():
    """Find VS Code extension logs directory.
    
    Returns:
        Path to VS Code logs directory or None
    """
    system = os.name
    home = Path.home()
    
    if system == "nt":  # Windows
        vscode_logs = home / "AppData" / "Roaming" / "Code" / "logs"
    elif system == "darwin":  # macOS
        vscode_logs = home / "Library" / "Application Support" / "Code" / "logs"
    else:  # Linux
        vscode_logs = home / ".config" / "Code" / "logs"
    
    if vscode_logs.exists():
        return vscode_logs
    
    return None


def find_q_developer_logs(vscode_logs=None):
    """Find Q Developer specific log files.
    
    Args:
        vscode_logs: Path to VS Code logs directory
    
    Returns:
        List of potential Q Developer log files
    """
    if not vscode_logs:
        vscode_logs = find_vscode_logs()
    
    if not vscode_logs:
        return []
    
    q_logs = []
    
    # Common extension log locations
    potential_paths = [
        vscode_logs / "exthost" / "*" / "Amazon.q-developer*",
        vscode_logs / "exthost" / "*" / "*q-developer*",
        vscode_logs / "exthost" / "*" / "*q*",
        vscode_logs / "*" / "*q-developer*",
    ]
    
    for pattern in potential_paths:
        try:
            q_logs.extend(Path(vscode_logs).parent.glob(str(pattern.relative_to(vscode_logs))))
        except Exception:
            pass
    
    return q_logs


def parse_log_file(log_file):
    """Parse a log file for Q Developer metrics.
    
    Args:
        log_file: Path to log file
    
    Returns:
        Dictionary with parsed metrics
    """
    metrics = {
        "queries": 0,
        "suggestions_accepted": 0,
        "suggestions_rejected": 0,
        "interactions": [],
    }
    
    try:
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line_lower = line.lower()
                
                # Count queries (heuristic: look for API calls or chat messages)
                if any(keyword in line_lower for keyword in ["query", "request", "chat", "completion"]):
                    metrics["queries"] += 1
                
                # Count accepted suggestions
                if any(keyword in line_lower for keyword in ["accept", "accepted", "applied"]):
                    metrics["suggestions_accepted"] += 1
                
                # Count rejected suggestions
                if any(keyword in line_lower for keyword in ["reject", "rejected", "dismiss", "dismissed"]):
                    metrics["suggestions_rejected"] += 1
                
                # Extract timestamps
                # This is a simplified parser - actual log format may vary
                if "timestamp" in line_lower or "time" in line_lower:
                    metrics["interactions"].append({
                        "line": line.strip()[:200],  # First 200 chars
                        "timestamp": datetime.now().isoformat(),  # Approximate
                    })
    except Exception as e:
        print(f"Warning: Could not parse log file {log_file}: {e}", file=sys.stderr)
    
    return metrics


def check_q_developer_api():
    """Check if Q Developer API is accessible.
    
    Returns:
        Dictionary with API availability info
    """
    # Q Developer may expose metrics through:
    # 1. VS Code extension API
    # 2. Local HTTP endpoint
    # 3. Configuration file
    
    api_info = {
        "available": False,
        "method": None,
        "endpoint": None,
    }
    
    # Check for local API endpoint (common ports)
    try:
        import socket
        test_ports = [8080, 8888, 3000, 5000]
        for port in test_ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)
            result = sock.connect_ex(("localhost", port))
            sock.close()
            if result == 0:
                api_info["available"] = True
                api_info["method"] = "http"
                api_info["endpoint"] = f"http://localhost:{port}"
                break
    except Exception:
        pass
    
    return api_info


def collect_q_developer_metrics():
    """Collect all Q Developer metrics.
    
    Returns:
        Dictionary with all collected metrics
    """
    metrics = {
        "collection_timestamp": datetime.now().isoformat(),
        "collection_method": "log_analysis",
        "plugin_installed": False,
        "logs_found": False,
        "api_available": False,
        "data": {
            "queries": 0,
            "suggestions_accepted": 0,
            "suggestions_rejected": 0,
            "total_interactions": 0,
            "interactions": [],
        },
    }
    
    # Check for VS Code logs
    vscode_logs = find_vscode_logs()
    if vscode_logs:
        metrics["vscode_logs_path"] = str(vscode_logs)
        metrics["plugin_installed"] = True
        
        # Find Q Developer logs
        q_logs = find_q_developer_logs(vscode_logs)
        if q_logs:
            metrics["logs_found"] = True
            metrics["log_files"] = [str(log) for log in q_logs]
            
            # Parse log files
            for log_file in q_logs:
                log_metrics = parse_log_file(log_file)
                metrics["data"]["queries"] += log_metrics["queries"]
                metrics["data"]["suggestions_accepted"] += log_metrics["suggestions_accepted"]
                metrics["data"]["suggestions_rejected"] += log_metrics["suggestions_rejected"]
                metrics["data"]["interactions"].extend(log_metrics["interactions"])
            
            metrics["data"]["total_interactions"] = len(metrics["data"]["interactions"])
    
    # Check for API access
    api_info = check_q_developer_api()
    if api_info["available"]:
        metrics["api_available"] = True
        metrics["api_info"] = api_info
    
    return metrics


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Collect Amazon Q Developer telemetry metrics"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="DATA_COLLECTION/q_developer_metrics.json",
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
        "--vscode-logs",
        type=str,
        help="Path to VS Code logs directory (auto-detected if not specified)"
    )
    
    args = parser.parse_args()
    
    # Determine output path
    output_path = Path(args.output)
    if args.participant_id and args.session_id:
        output_path = Path(
            f"DATA_COLLECTION/q_developer_metrics_{args.participant_id}_{args.session_id}.json"
        )
    elif args.participant_id:
        output_path = Path(f"DATA_COLLECTION/q_developer_metrics_{args.participant_id}.json")
    
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Collect metrics
    print("Collecting Q Developer metrics...")
    print("Note: This is an investigation script. Actual telemetry collection method may vary.")
    print()
    
    metrics = collect_q_developer_metrics()
    
    # Write to file
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)
    
    # Print summary
    print("=== Q Developer Metrics Summary ===")
    print(f"Plugin installed: {metrics['plugin_installed']}")
    print(f"Logs found: {metrics['logs_found']}")
    print(f"API available: {metrics['api_available']}")
    
    if metrics["logs_found"]:
        print(f"\nData from logs:")
        print(f"  Queries: {metrics['data']['queries']}")
        print(f"  Suggestions accepted: {metrics['data']['suggestions_accepted']}")
        print(f"  Suggestions rejected: {metrics['data']['suggestions_rejected']}")
        print(f"  Total interactions: {metrics['data']['total_interactions']}")
    
    if not metrics["plugin_installed"]:
        print("\nWarning: Q Developer plugin not detected.")
        print("  - Make sure VS Code is installed")
        print("  - Make sure Q Developer extension is installed")
        print("  - Check VS Code logs directory manually")
    
    if not metrics["logs_found"] and metrics["plugin_installed"]:
        print("\nWarning: Q Developer logs not found.")
        print("  - Logs may be in a different location")
        print("  - Extension may use different logging mechanism")
        print("  - Consider using screen recording analysis as fallback")
    
    print(f"\nData saved to: {output_path}")
    print("\nNote: This script provides basic log analysis.")
    print("For accurate metrics, check:")
    print("  1. Q Developer extension settings for telemetry options")
    print("  2. VS Code output panel for Q Developer channel")
    print("  3. Amazon Q Developer documentation for API access")


if __name__ == "__main__":
    main()
