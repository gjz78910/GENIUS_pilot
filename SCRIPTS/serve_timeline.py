#!/usr/bin/env python3
"""
serve_timeline.py — serve the timeline via local HTTP and open in Safari.

REQUIRED because Safari blocks file:// access to videos in other directories.
HTTP removes that restriction — all local files are served from one root.

Usage:
    python SCRIPTS/serve_timeline.py              # ai-01 (default), port 8080
    python SCRIPTS/serve_timeline.py ai-03        # specific participant
    python SCRIPTS/serve_timeline.py ai-01 8090   # custom port
"""

import http.server
import os
import subprocess
import sys
import threading
from pathlib import Path
from urllib.parse import urlparse

# Serve from the parent of both GENIUS_pilot_KCL-01 and GENIUS_experiment_data
SERVE_ROOT = Path("/Users/k2589922/Documents/Projects")
PROJECT    = "GENIUS_pilot_KCL-01"
PROJECT_ROOT = SERVE_ROOT / PROJECT

def regenerate_if_stale(participant: str):
    """Regenerate only when timeline inputs changed since the last HTML build."""
    output = PROJECT_ROOT / "SCRIPTS/output" / (participant + "_timeline.html")
    generator = PROJECT_ROOT / "SCRIPTS/generate_timeline.py"
    inputs = [
        generator,
        PROJECT_ROOT / "SCRIPTS/output" / (participant + "_log_events.json"),
        PROJECT_ROOT / "SCRIPTS/output" / (participant + "_annotation.json"),
        PROJECT_ROOT / "SCRIPTS/lib/vis-timeline.min.js",
        PROJECT_ROOT / "SCRIPTS/lib/vis-timeline.min.css",
    ]
    newest_input = max((p.stat().st_mtime for p in inputs if p.exists()), default=0)
    if output.exists() and output.stat().st_mtime >= newest_input:
        return
    result = subprocess.run(
        [sys.executable, str(generator), "--participant", participant],
        cwd=PROJECT_ROOT, capture_output=True, text=True,
    )
    if result.returncode:
        print("Timeline regeneration failed:\n" + result.stderr, file=sys.stderr)
    else:
        print("Regenerated %s timeline from updated annotation/log data." % participant)

def main():
    participant = sys.argv[1] if len(sys.argv) > 1 else "ai-01"
    port        = int(sys.argv[2]) if len(sys.argv) > 2 else 8080

    html_path = "%s/SCRIPTS/output/%s_timeline.html" % (PROJECT, participant)
    url       = "http://localhost:%d/%s" % (port, html_path)

    # Check the HTML exists
    if not (SERVE_ROOT / html_path).exists():
        print("ERROR: %s not found." % (SERVE_ROOT / html_path))
        print("Run first: python SCRIPTS/generate_timeline.py --participant %s" % participant)
        raise SystemExit(1)

    os.chdir(SERVE_ROOT)

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, fmt, *args): pass  # suppress request logs

        def do_GET(self):
            request_path = urlparse(self.path).path
            if request_path == "/" + html_path:
                regenerate_if_stale(participant)
            return super().do_GET()

        def end_headers(self):
            # The self-contained HTML embeds the generated annotation JSON.
            # Do not let Safari keep a stale version after an annotation edit.
            if urlparse(self.path).path == "/" + html_path:
                self.send_header("Cache-Control", "no-store, max-age=0")
            return super().end_headers()

    server = http.server.HTTPServer(("127.0.0.1", port), QuietHandler)
    print("Serving %s on port %d" % (SERVE_ROOT, port))
    print("Opening: %s" % url)
    print("Press Ctrl+C to stop.\n")

    def open_browser():
        import time; time.sleep(0.4)
        subprocess.Popen(["open", "-a", "Safari", url])

    threading.Thread(target=open_browser, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == "__main__":
    main()
