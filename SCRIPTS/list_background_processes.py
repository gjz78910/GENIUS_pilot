#!/usr/bin/env python3
"""List background processes that may affect energy consumption or data collection.

This script helps identify processes that should be closed before starting
the experiment to ensure accurate resource monitoring.
"""

import psutil
import sys
from collections import defaultdict


def get_process_info():
    """Get information about running processes."""
    processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'username']):
        try:
            pinfo = proc.info
            # Get current CPU usage (non-blocking)
            pinfo['cpu_percent'] = proc.cpu_percent(interval=0.1)
            processes.append(pinfo)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    return processes


def categorize_processes(processes):
    """Categorize processes by type."""
    categories = {
        'high_cpu': [],
        'high_memory': [],
        'browsers': [],
        'ides': [],
        'media': [],
        'communication': [],
        'system': [],
        'other': []
    }
    
    browser_keywords = ['chrome', 'firefox', 'safari', 'edge', 'brave', 'opera']
    ide_keywords = ['code', 'pycharm', 'intellij', 'sublime', 'atom', 'vim', 'emacs']
    media_keywords = ['spotify', 'itunes', 'vlc', 'quicktime', 'zoom', 'teams', 'skype']
    comm_keywords = ['slack', 'discord', 'telegram', 'whatsapp', 'messenger']
    
    for proc in processes:
        name_lower = proc['name'].lower()
        cpu = proc.get('cpu_percent', 0)
        mem = proc.get('memory_percent', 0)
        
        # High CPU (> 5%)
        if cpu > 5.0:
            categories['high_cpu'].append(proc)
        
        # High memory (> 5%)
        if mem > 5.0:
            categories['high_memory'].append(proc)
        
        # Browsers
        if any(keyword in name_lower for keyword in browser_keywords):
            categories['browsers'].append(proc)
        
        # IDEs
        elif any(keyword in name_lower for keyword in ide_keywords):
            categories['ides'].append(proc)
        
        # Media players
        elif any(keyword in name_lower for keyword in media_keywords):
            categories['media'].append(proc)
        
        # Communication apps
        elif any(keyword in name_lower for keyword in comm_keywords):
            categories['communication'].append(proc)
        
        # System processes (usually safe to keep)
        elif proc['username'] in ['root', 'system', 'SYSTEM'] or 'system' in name_lower:
            categories['system'].append(proc)
        
        else:
            categories['other'].append(proc)
    
    return categories


def print_category(category_name, processes, limit=10):
    """Print a category of processes."""
    if not processes:
        return
    
    print(f"\n{category_name.upper().replace('_', ' ')}:")
    print("-" * 80)
    
    # Sort by CPU or memory depending on category
    if 'cpu' in category_name:
        processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
    elif 'memory' in category_name:
        processes.sort(key=lambda x: x.get('memory_percent', 0), reverse=True)
    
    for proc in processes[:limit]:
        name = proc['name'][:40]
        pid = proc['pid']
        cpu = proc.get('cpu_percent', 0)
        mem = proc.get('memory_percent', 0)
        user = proc.get('username', 'N/A')
        
        print(f"  {name:40} PID: {pid:6} CPU: {cpu:5.1f}%  MEM: {mem:5.1f}%  User: {user}")
    
    if len(processes) > limit:
        print(f"  ... and {len(processes) - limit} more")


def main():
    """Main function."""
    print("Scanning processes...")
    print("=" * 80)
    
    processes = get_process_info()
    categories = categorize_processes(processes)
    
    # Print summary
    total_processes = len(processes)
    print(f"\nTotal processes: {total_processes}")
    
    # Print categories
    print_category("HIGH CPU USAGE (>5%)", categories['high_cpu'])
    print_category("HIGH MEMORY USAGE (>5%)", categories['high_memory'])
    print_category("BROWSERS (consider closing)", categories['browsers'])
    print_category("IDEs (keep only the assigned IDE)", categories['ides'])
    print_category("MEDIA PLAYERS (consider closing)", categories['media'])
    print_category("COMMUNICATION APPS (consider closing)", categories['communication'])
    
    # Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS:")
    print("-" * 80)
    
    recommendations = []
    
    if categories['browsers']:
        recommendations.append("Close browsers (Chrome, Firefox, Safari, etc.) - they use significant CPU/memory")
    
    if len(categories['ides']) > 1:
        recommendations.append("Close other IDEs - keep only the assigned IDE")
    
    if categories['media']:
        recommendations.append("Close media players (Spotify, iTunes, etc.) - they use CPU/memory")
    
    if categories['communication']:
        recommendations.append("Close communication apps (Slack, Discord, etc.) - they use network and CPU")
    
    if categories['high_cpu']:
        recommendations.append(f"Review {len(categories['high_cpu'])} high-CPU processes above")
    
    if not recommendations:
        recommendations.append("✅ No obvious processes to close. System looks clean.")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    
    print("\n" + "=" * 80)
    print("Note: System processes are usually safe to keep running.")
    print("Focus on closing user applications (browsers, media, communication).")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        sys.exit(1)
