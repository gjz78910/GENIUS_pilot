#!/usr/bin/env python3
"""Track task timing during experiment.

This script helps track time spent on each task, including start/end times,
idle time, and break times. Can be used manually or integrated with screen
recording timestamps.
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path


class TaskTimer:
    """Track task timing."""
    
    def __init__(self, output_file):
        """Initialize timer.
        
        Args:
            output_file: Path to output JSON file
        """
        self.output_file = Path(output_file)
        self.tasks = []
        self.current_task = None
        self.start_time = None
        
        # Create output directory if needed
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
    
    def start_task(self, task_name, task_id=None):
        """Start tracking a task.
        
        Args:
            task_name: Name of the task (e.g., "Task 1: Optimization")
            task_id: Optional task identifier
        """
        if self.current_task:
            print(f"Warning: Task '{self.current_task['name']}' is still running. Ending it first.")
            self.end_task()
        
        self.current_task = {
            "task_id": task_id or f"task_{len(self.tasks) + 1}",
            "name": task_name,
            "start_time": datetime.now().isoformat(),
            "start_timestamp": time.time(),
            "end_time": None,
            "end_timestamp": None,
            "duration_seconds": None,
            "idle_time_seconds": 0,
            "break_time_seconds": 0,
            "notes": [],
        }
        
        self.start_time = time.time()
        print(f"Started: {task_name} at {self.current_task['start_time']}")
    
    def end_task(self):
        """End the current task."""
        if not self.current_task:
            print("Warning: No task is currently running.")
            return
        
        end_time = time.time()
        self.current_task["end_time"] = datetime.now().isoformat()
        self.current_task["end_timestamp"] = end_time
        self.current_task["duration_seconds"] = end_time - self.current_task["start_timestamp"]
        
        print(f"Ended: {self.current_task['name']} - Duration: {self.current_task['duration_seconds']:.1f} seconds")
        
        self.tasks.append(self.current_task)
        self.current_task = None
        self.start_time = None
    
    def add_idle_time(self, seconds):
        """Add idle time to current task.
        
        Args:
            seconds: Number of seconds of idle time
        """
        if not self.current_task:
            print("Warning: No task is currently running.")
            return
        
        self.current_task["idle_time_seconds"] += seconds
        print(f"Added {seconds} seconds of idle time to current task")
    
    def add_break_time(self, seconds):
        """Add break time to current task.
        
        Args:
            seconds: Number of seconds of break time
        """
        if not self.current_task:
            print("Warning: No task is currently running.")
            return
        
        self.current_task["break_time_seconds"] += seconds
        print(f"Added {seconds} seconds of break time to current task")
    
    def add_note(self, note):
        """Add a note to the current task.
        
        Args:
            note: Note text
        """
        if not self.current_task:
            print("Warning: No task is currently running.")
            return
        
        timestamp = datetime.now().isoformat()
        self.current_task["notes"].append({
            "timestamp": timestamp,
            "note": note,
        })
        print(f"Note added: {note}")
    
    def save(self):
        """Save all task data to file."""
        data = {
            "experiment_info": {
                "total_tasks": len(self.tasks),
                "total_duration_seconds": sum(
                    task.get("duration_seconds", 0) for task in self.tasks
                ),
                "total_idle_seconds": sum(
                    task.get("idle_time_seconds", 0) for task in self.tasks
                ),
                "total_break_seconds": sum(
                    task.get("break_time_seconds", 0) for task in self.tasks
                ),
            },
            "tasks": self.tasks,
        }
        
        with open(self.output_file, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"Task timing data saved to: {self.output_file}")
    
    def get_summary(self):
        """Get summary of all tasks."""
        if not self.tasks:
            return "No tasks completed yet."
        
        summary = "\n=== Task Timing Summary ===\n"
        for task in self.tasks:
            duration = task.get("duration_seconds", 0)
            idle = task.get("idle_time_seconds", 0)
            break_time = task.get("break_time_seconds", 0)
            active = duration - idle - break_time
            
            summary += f"\n{task['name']}:\n"
            summary += f"  Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)\n"
            summary += f"  Active time: {active:.1f} seconds ({active/60:.1f} minutes)\n"
            summary += f"  Idle time: {idle:.1f} seconds\n"
            summary += f"  Break time: {break_time:.1f} seconds\n"
        
        total = sum(task.get("duration_seconds", 0) for task in self.tasks)
        summary += f"\nTotal time: {total:.1f} seconds ({total/60:.1f} minutes)\n"
        
        return summary


def interactive_mode(timer):
    """Run interactive mode."""
    print("\n=== Task Timer - Interactive Mode ===")
    print("Commands:")
    print("  start <task_name> - Start a new task")
    print("  end - End current task")
    print("  idle <seconds> - Add idle time")
    print("  break <seconds> - Add break time")
    print("  note <text> - Add a note")
    print("  summary - Show summary")
    print("  save - Save and exit")
    print("  quit - Exit without saving")
    print()
    
    while True:
        try:
            command = input("> ").strip().split()
            if not command:
                continue
            
            cmd = command[0].lower()
            
            if cmd == "start":
                task_name = " ".join(command[1:]) if len(command) > 1 else f"Task {len(timer.tasks) + 1}"
                timer.start_task(task_name)
            
            elif cmd == "end":
                timer.end_task()
            
            elif cmd == "idle":
                seconds = float(command[1]) if len(command) > 1 else 0
                timer.add_idle_time(seconds)
            
            elif cmd == "break":
                seconds = float(command[1]) if len(command) > 1 else 0
                timer.add_break_time(seconds)
            
            elif cmd == "note":
                note = " ".join(command[1:]) if len(command) > 1 else ""
                timer.add_note(note)
            
            elif cmd == "summary":
                print(timer.get_summary())
            
            elif cmd == "save":
                timer.save()
                break
            
            elif cmd == "quit":
                print("Exiting without saving.")
                break
            
            else:
                print(f"Unknown command: {cmd}")
        
        except KeyboardInterrupt:
            print("\nInterrupted. Saving...")
            timer.save()
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Track task timing during experiment"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="DATA_COLLECTION/task_timing.json",
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
        "-i", "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )
    
    args = parser.parse_args()
    
    # Determine output path
    output_path = args.output
    if args.participant_id and args.session_id:
        output_path = f"DATA_COLLECTION/task_timing_{args.participant_id}_{args.session_id}.json"
    elif args.participant_id:
        output_path = f"DATA_COLLECTION/task_timing_{args.participant_id}.json"
    
    timer = TaskTimer(output_path)
    
    if args.interactive:
        interactive_mode(timer)
    else:
        print("Task Timer - Use interactive mode (-i) or import as module")
        print("Example: python SCRIPTS/task_timer.py -i")


if __name__ == "__main__":
    main()
