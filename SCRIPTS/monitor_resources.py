#!/usr/bin/env python3
"""Monitor system resources during experiment.

This script runs in the background and continuously monitors CPU, memory,
network, and disk I/O usage, logging to a JSON lines file.
"""

import json
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import psutil
except ImportError:
    print("ERROR: psutil not installed. Install with: pip install psutil")
    sys.exit(1)


class ResourceMonitor:
    """Monitor system resources."""
    
    def __init__(self, output_file, interval=60):
        """Initialize monitor.
        
        Args:
            output_file: Path to output JSONL file
            interval: Sampling interval in seconds (default: 60)
        """
        self.output_file = Path(output_file)
        self.interval = interval
        self.running = True
        self.start_time = None
        
        # Create output directory if needed
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Network counters (for calculating per-minute rates)
        self.last_net_io = psutil.net_io_counters()
        self.last_net_time = time.time()
        
        # Disk I/O counters
        self.last_disk_io = psutil.disk_io_counters()
        self.last_disk_time = time.time()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\nReceived signal {signum}, shutting down...")
        self.running = False
    
    def get_cpu_usage(self):
        """Get CPU usage per core and average."""
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        return {
            "per_core": cpu_percent,
            "average": sum(cpu_percent) / len(cpu_percent) if cpu_percent else 0.0,
            "count": len(cpu_percent),
        }
    
    def get_memory_usage(self):
        """Get memory usage."""
        mem = psutil.virtual_memory()
        return {
            "used_gb": round(mem.used / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "total_gb": round(mem.total / (1024**3), 2),
            "percent": mem.percent,
        }
    
    def get_network_usage(self):
        """Get network usage (bytes sent/received per minute)."""
        current_net_io = psutil.net_io_counters()
        current_time = time.time()
        
        # Calculate time delta
        time_delta = current_time - self.last_net_time
        
        # Calculate bytes per minute
        bytes_sent_per_min = 0
        bytes_recv_per_min = 0
        
        if time_delta > 0:
            bytes_sent_delta = current_net_io.bytes_sent - self.last_net_io.bytes_sent
            bytes_recv_delta = current_net_io.bytes_recv - self.last_net_io.bytes_recv
            
            # Convert to per-minute rate
            bytes_sent_per_min = int((bytes_sent_delta / time_delta) * 60)
            bytes_recv_per_min = int((bytes_recv_delta / time_delta) * 60)
        
        # Update counters
        self.last_net_io = current_net_io
        self.last_net_time = current_time
        
        return {
            "bytes_sent_per_min": bytes_sent_per_min,
            "bytes_recv_per_min": bytes_recv_per_min,
            "total_bytes_sent": current_net_io.bytes_sent,
            "total_bytes_recv": current_net_io.bytes_recv,
            "packets_sent": current_net_io.packets_sent,
            "packets_recv": current_net_io.packets_recv,
        }
    
    def get_disk_io(self):
        """Get disk I/O statistics."""
        current_disk_io = psutil.disk_io_counters()
        current_time = time.time()
        
        # Calculate time delta
        time_delta = current_time - self.last_disk_time
        
        # Calculate I/O per minute
        read_ops_per_min = 0
        write_ops_per_min = 0
        read_bytes_per_min = 0
        write_bytes_per_min = 0
        
        if time_delta > 0 and current_disk_io and self.last_disk_io:
            read_ops_delta = current_disk_io.read_count - self.last_disk_io.read_count
            write_ops_delta = current_disk_io.write_count - self.last_disk_io.write_count
            read_bytes_delta = current_disk_io.read_bytes - self.last_disk_io.read_bytes
            write_bytes_delta = current_disk_io.write_bytes - self.last_disk_io.write_bytes
            
            # Convert to per-minute rate
            read_ops_per_min = int((read_ops_delta / time_delta) * 60)
            write_ops_per_min = int((write_ops_delta / time_delta) * 60)
            read_bytes_per_min = int((read_bytes_delta / time_delta) * 60)
            write_bytes_per_min = int((write_bytes_delta / time_delta) * 60)
        
        # Update counters
        self.last_disk_io = current_disk_io
        self.last_disk_time = current_time
        
        return {
            "read_ops_per_min": read_ops_per_min,
            "write_ops_per_min": write_ops_per_min,
            "read_bytes_per_min": read_bytes_per_min,
            "write_bytes_per_min": write_bytes_per_min,
            "total_read_count": current_disk_io.read_count if current_disk_io else 0,
            "total_write_count": current_disk_io.write_count if current_disk_io else 0,
        }
    
    def collect_sample(self):
        """Collect a single sample of all metrics."""
        return {
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": (time.time() - self.start_time) if self.start_time else 0,
            "cpu": self.get_cpu_usage(),
            "memory": self.get_memory_usage(),
            "network": self.get_network_usage(),
            "disk_io": self.get_disk_io(),
        }
    
    def run(self):
        """Run the monitoring loop."""
        self.start_time = time.time()
        
        print(f"Starting resource monitoring...")
        print(f"Output file: {self.output_file}")
        print(f"Sampling interval: {self.interval} seconds")
        print(f"Press Ctrl+C to stop")
        
        with open(self.output_file, "a") as f:
            while self.running:
                sample = self.collect_sample()
                f.write(json.dumps(sample) + "\n")
                f.flush()  # Ensure data is written immediately
                
                # Print summary to console
                print(
                    f"[{sample['timestamp']}] "
                    f"CPU: {sample['cpu']['average']:.1f}% | "
                    f"Memory: {sample['memory']['percent']:.1f}% | "
                    f"Network: {sample['network']['bytes_sent_per_min']/1024:.1f}KB/s sent, "
                    f"{sample['network']['bytes_recv_per_min']/1024:.1f}KB/s recv"
                )
                
                # Sleep until next sample
                time.sleep(self.interval)
        
        print(f"\nMonitoring stopped. Data saved to: {self.output_file}")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Monitor system resources during experiment"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="DATA_COLLECTION/resource_usage.jsonl",
        help="Output JSONL file path"
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
        "-i", "--interval",
        type=int,
        default=60,
        help="Sampling interval in seconds (default: 60)"
    )
    
    args = parser.parse_args()
    
    # Determine output path
    output_path = Path(args.output)
    if args.participant_id and args.session_id:
        output_path = output_path.parent / f"resource_usage_{args.participant_id}_{args.session_id}.jsonl"
    elif args.participant_id:
        output_path = output_path.parent / f"resource_usage_{args.participant_id}.jsonl"
    
    # Create and run monitor
    monitor = ResourceMonitor(output_path, interval=args.interval)
    monitor.run()


if __name__ == "__main__":
    main()
