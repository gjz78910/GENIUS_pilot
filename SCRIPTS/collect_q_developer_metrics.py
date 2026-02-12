#!/usr/bin/env python3
"""Precise Amazon Q Developer metrics collection focusing on actual user interactions.

This script looks for specific user interaction patterns rather than all log messages.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


def find_latest_vscode_logs():
    """Find the most recent VS Code logs directory."""
    home = Path.home()
    
    if os.name == "nt":  # Windows
        vscode_logs = home / "AppData" / "Roaming" / "Code" / "logs"
    elif sys.platform == "darwin":  # macOS
        vscode_logs = home / "Library" / "Application Support" / "Code" / "logs"
    else:  # Linux
        vscode_logs = home / ".config" / "Code" / "logs"
    
    if not vscode_logs.exists():
        return None
    
    # Find the most recent log directory
    log_dirs = [d for d in vscode_logs.iterdir() if d.is_dir()]
    if not log_dirs:
        return None
    
    # Sort by modification time, get most recent
    latest_dir = max(log_dirs, key=lambda d: d.stat().st_mtime)
    return latest_dir


def find_q_developer_logs(vscode_logs_dir):
    """Find Amazon Q Developer log files."""
    if not vscode_logs_dir:
        return []
    
    q_logs = []
    
    # Look for Amazon Q logs in all windows
    for window_dir in vscode_logs_dir.glob("window*"):
        exthost_dir = window_dir / "exthost"
        if exthost_dir.exists():
            # Look for Amazon Q extension logs
            q_ext_dir = exthost_dir / "amazonwebservices.amazon-q-vscode"
            if q_ext_dir.exists():
                for log_file in q_ext_dir.glob("*.log"):
                    q_logs.append(log_file)
    
    return q_logs


def parse_q_developer_log_precise(log_file):
    """Parse Amazon Q Developer log file for precise user interaction metrics."""
    metrics = {
        "chat_messages_sent": 0,
        "chat_conversations": 0,
        "code_suggestions_shown": 0,
        "code_suggestions_accepted": 0,
        "code_suggestions_rejected": 0,
        "inline_completions": 0,
        "tool_uses": 0,
        "interactions": [],
    }
    
    try:
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            lines = content.split('\n')
            
            conversation_ids = set()
            
            for line in lines:
                if not line.strip():
                    continue
                
                line_lower = line.lower()
                
                # Extract timestamp if available
                timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                timestamp = timestamp_match.group(1) if timestamp_match else None
                
                # Count actual chat messages sent by user
                if "sendchatprompt" in line_lower and "received" in line_lower:
                    metrics["chat_messages_sent"] += 1
                    if timestamp:
                        metrics["interactions"].append({
                            "type": "chat_message_sent",
                            "timestamp": timestamp,
                            "details": "User sent chat message"
                        })
                
                # Count unique conversations
                conv_match = re.search(r'"cwsprChatConversationId":"([^"]+)"', line)
                if conv_match and conv_match.group(1) not in ["", "undefined"]:
                    conversation_ids.add(conv_match.group(1))
                
                # Count code suggestions/completions shown to user
                if "codewhisperer" in line_lower and any(keyword in line_lower for keyword in [
                    "suggestion", "completion", "recommend"
                ]) and "shown" not in line_lower:  # Avoid double counting
                    metrics["code_suggestions_shown"] += 1
                    if timestamp:
                        metrics["interactions"].append({
                            "type": "code_suggestion_shown",
                            "timestamp": timestamp,
                            "details": "Code suggestion displayed"
                        })
                
                # Count inline completions (actual code completions)
                if "inline" in line_lower and "completion" in line_lower and "server" not in line_lower:
                    metrics["inline_completions"] += 1
                    if timestamp:
                        metrics["interactions"].append({
                            "type": "inline_completion",
                            "timestamp": timestamp,
                            "details": "Inline code completion"
                        })
                
                # Count tool uses (when Q Developer uses tools like file operations)
                if "tooluse" in line_lower and "suggested" in line_lower:
                    metrics["tool_uses"] += 1
                    if timestamp:
                        metrics["interactions"].append({
                            "type": "tool_use",
                            "timestamp": timestamp,
                            "details": "Q Developer used a tool"
                        })
                
                # Count button clicks (user accepting suggestions)
                if "buttonclick" in line_lower and "run-" in line_lower:
                    metrics["code_suggestions_accepted"] += 1
                    if timestamp:
                        metrics["interactions"].append({
                            "type": "suggestion_accepted",
                            "timestamp": timestamp,
                            "details": "User accepted suggestion via button click"
                        })
                
                # Count explicit accepts/rejects
                if "accept" in line_lower and "telemetry" in line_lower:
                    metrics["code_suggestions_accepted"] += 1
                    if timestamp:
                        metrics["interactions"].append({
                            "type": "suggestion_accepted",
                            "timestamp": timestamp,
                            "details": "Code suggestion accepted"
                        })
                
                if "reject" in line_lower and "telemetry" in line_lower:
                    metrics["code_suggestions_rejected"] += 1
                    if timestamp:
                        metrics["interactions"].append({
                            "type": "suggestion_rejected",
                            "timestamp": timestamp,
                            "details": "Code suggestion rejected"
                        })
            
            metrics["chat_conversations"] = len(conversation_ids)
    
    except Exception as e:
        print(f"Warning: Could not parse log file {log_file}: {e}", file=sys.stderr)
    
    return metrics


def check_chat_history():
    """Check Amazon Q chat history files for additional context."""
    home = Path.home()
    chat_history_dir = home / ".aws" / "amazonq" / "history"
    
    chat_data = {
        "history_files_found": 0,
        "total_conversations": 0,
        "total_messages": 0
    }
    
    if chat_history_dir.exists():
        for history_file in chat_history_dir.glob("chat-history-*.json"):
            chat_data["history_files_found"] += 1
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    if isinstance(history, dict) and "conversations" in history:
                        conversations = history["conversations"]
                        chat_data["total_conversations"] += len(conversations)
                        for conv in conversations:
                            if "messages" in conv:
                                chat_data["total_messages"] += len(conv["messages"])
            except Exception as e:
                print(f"Warning: Could not read chat history {history_file}: {e}", file=sys.stderr)
    
    return chat_data


def collect_q_developer_metrics():
    """Collect precise Amazon Q Developer metrics."""
    metrics = {
        "collection_timestamp": datetime.now().isoformat(),
        "collection_method": "precise_interaction_analysis",
        "plugin_installed": False,
        "logs_found": False,
        "data": {
            "chat_messages_sent": 0,
            "chat_conversations": 0,
            "code_suggestions_shown": 0,
            "code_suggestions_accepted": 0,
            "code_suggestions_rejected": 0,
            "inline_completions": 0,
            "tool_uses": 0,
            "total_interactions": 0,
            "interactions": [],
        },
        "chat_history": {}
    }
    
    # Find VS Code logs
    vscode_logs = find_latest_vscode_logs()
    if vscode_logs:
        metrics["vscode_logs_path"] = str(vscode_logs)
        
        # Find Q Developer logs
        q_logs = find_q_developer_logs(vscode_logs)
        
        if q_logs:
            metrics["logs_found"] = True
            metrics["plugin_installed"] = True
            
            # Parse each log file
            for log_file in q_logs:
                log_metrics = parse_q_developer_log_precise(log_file)
                
                # Aggregate metrics
                for key in ["chat_messages_sent", "chat_conversations", "code_suggestions_shown",
                           "code_suggestions_accepted", "code_suggestions_rejected", 
                           "inline_completions", "tool_uses"]:
                    metrics["data"][key] += log_metrics[key]
                
                # Combine interactions
                metrics["data"]["interactions"].extend(log_metrics["interactions"])
    
    # Check chat history
    metrics["chat_history"] = check_chat_history()
    
    # Calculate total interactions
    metrics["data"]["total_interactions"] = len(metrics["data"]["interactions"])
    
    return metrics


if __name__ == "__main__":
    metrics = collect_q_developer_metrics()
    print(json.dumps(metrics, indent=2))