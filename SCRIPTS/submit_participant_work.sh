#!/usr/bin/env bash
# Submit participant work and persist the result of every submission step.
# Usage: ./SCRIPTS/submit_participant_work.sh <participant_id> <session_id>

set -u

PARTICIPANT_ID="${1:-}"
SESSION_ID="${2:-SESSION1}"
if [ -z "$PARTICIPANT_ID" ]; then
    echo "Usage: $0 <participant_id> <session_id>" >&2
    exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

if command -v genius-command-audit >/dev/null; then
    genius-command-audit 0 "$PROJECT_ROOT" "$0 $*" || true
fi

AUDIT_DIR="DATA_COLLECTION/terminal_audit"
MANIFEST="$AUDIT_DIR/submission_${PARTICIPANT_ID}_${SESSION_ID}.json"
mkdir -p "$AUDIT_DIR"

started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
checkpoint_timeout_seconds="${GENIUS_CHECKPOINT_TIMEOUT_SECONDS:-180}"

# Capture authoritative checkpoint outcomes before the repository snapshot.
python SCRIPTS/run_experiment_test_checkpoints.py \
    --participant-id "$PARTICIPANT_ID" \
    --session-id "$SESSION_ID" \
    --output-dir DATA_COLLECTION \
    --timeout "$checkpoint_timeout_seconds"
checkpoint_status=$?

# Preserve the experiment-scoped background-monitor and structured terminal
# audit before later storage or network operations can fail.
runtime_dir="${RUNTIME_DIR:-/home/participant/genius-runtime}"
mkdir -p DATA_COLLECTION/runtime
if [ -d "$runtime_dir" ]; then
    cp -a "$runtime_dir"/. DATA_COLLECTION/runtime/ 2>/dev/null || true
fi

# On AWS remote VMs, collect_system_info.py runs automatically at boot into
# the runtime dir as a generic "system_info.json" rather than the
# DATA_COLLECTION/system_info_<ID>.json name verify_data_separation.py and
# the rest of the pipeline expect, so it needs copying into place here.
system_info_dest="DATA_COLLECTION/system_info_${PARTICIPANT_ID}.json"
if [ ! -f "$system_info_dest" ] && [ -f "$runtime_dir/system_info.json" ]; then
    cp "$runtime_dir/system_info.json" "$system_info_dest" 2>/dev/null || true
fi

./SCRIPTS/store_participant_work.sh "$PARTICIPANT_ID" "$SESSION_ID"
store_status=$?

# Store a portable, verified copy of the complete Git object graph. This makes
# exact commits and pre-prompt states reconstructable without depending on the
# participant VM's working .git directory.
git_bundle_status=125
git_bundle_path="DATA_COLLECTION/git_state/${PARTICIPANT_ID}_${SESSION_ID}.bundle"
if [ "$store_status" -eq 0 ] && [ -d .git ]; then
    mkdir -p "$(dirname "$git_bundle_path")"
    git bundle create "$git_bundle_path" --all
    git_bundle_status=$?
    if [ "$git_bundle_status" -eq 0 ]; then
        git bundle verify "$git_bundle_path" >/dev/null 2>&1
        git_bundle_status=$?
        git show-ref > "DATA_COLLECTION/git_state/${PARTICIPANT_ID}_${SESSION_ID}_refs.txt"
    fi
fi

branch="participant-$PARTICIPANT_ID"
push_status=125
if [ "$store_status" -eq 0 ]; then
    git push -u origin "$branch" --tags
    push_status=$?
fi

finished_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
commit="$(git rev-parse HEAD 2>/dev/null || true)"
tag="$(git tag --points-at HEAD | tail -n 1)"
cat > "$MANIFEST" <<EOF
{
  "participant_id": "$PARTICIPANT_ID",
  "session_id": "$SESSION_ID",
  "submission_started_at": "$started_at",
  "submission_finished_at": "$finished_at",
  "checkpoint_exit_code": $checkpoint_status,
  "store_exit_code": $store_status,
  "git_bundle_exit_code": $git_bundle_status,
  "git_bundle": "$git_bundle_path",
  "push_exit_code": $push_status,
  "branch": "$branch",
  "commit": "$commit",
  "tag": "$tag"
}
EOF

if [ "$checkpoint_status" -ne 0 ]; then
    echo "Checkpoint report contains incomplete work; this does not invalidate the submission." >&2
fi
if [ "$store_status" -ne 0 ] || [ "$git_bundle_status" -ne 0 ] || [ "$push_status" -ne 0 ]; then
    echo "Submission evidence was retained locally, but storage, Git-state capture, or push failed; see $MANIFEST" >&2
    exit 1
fi
echo "Submission recorded: $MANIFEST"
