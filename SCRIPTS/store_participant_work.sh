#!/bin/bash
# Store participant work before resetting environment
# Usage: ./store_participant_work.sh <participant_id> [session_id]

set -e  # Exit on error

PARTICIPANT_ID="$1"
SESSION_ID="${2:-SESSION1}"

if [ -z "$PARTICIPANT_ID" ]; then
    echo "ERROR: Participant ID required"
    echo "Usage: $0 <participant_id> [session_id]"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Check if Git is initialized
if [ ! -d ".git" ]; then
    echo "WARNING: Not a Git repository. Creating archive backup instead..."
    BACKUP_DIR="DATA_COLLECTION/participant_backups"
    mkdir -p "$BACKUP_DIR"
    BACKUP_FILE="$BACKUP_DIR/participant_${PARTICIPANT_ID}_${SESSION_ID}_$(date +%Y%m%d_%H%M%S).tar.gz"
    tar -czf "$BACKUP_FILE" --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='DATA_COLLECTION' .
    echo "✅ Backup created: $BACKUP_FILE"
    
    # Create checksum
    sha256sum "$BACKUP_FILE" > "${BACKUP_FILE}.sha256"
    echo "✅ Checksum saved: ${BACKUP_FILE}.sha256"
    exit 0
fi

echo "Storing work for participant: $PARTICIPANT_ID (session: $SESSION_ID)"
echo ""

# Check for uncommitted changes
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "⚠️  WARNING: You have uncommitted changes!"
    echo "   Committing them to participant branch..."
    
    # Create or checkout participant branch
    BRANCH_NAME="participant-${PARTICIPANT_ID}"
    if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
        git checkout "$BRANCH_NAME"
    else
        git checkout -b "$BRANCH_NAME"
    fi
    
    # Commit all changes
    git add -A
    git commit -m "Participant ${PARTICIPANT_ID} work - ${SESSION_ID} - $(date +%Y-%m-%d\ %H:%M:%S)" || true
fi

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Create participant branch if not already on it
if [ "$CURRENT_BRANCH" != "participant-${PARTICIPANT_ID}" ]; then
    BRANCH_NAME="participant-${PARTICIPANT_ID}"
    if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
        echo "⚠️  Branch $BRANCH_NAME already exists. Switching to it..."
        git checkout "$BRANCH_NAME"
    else
        echo "Creating participant branch: $BRANCH_NAME"
        git checkout -b "$BRANCH_NAME"
    fi
fi

# Create tag for this session
TAG_NAME="participant-${PARTICIPANT_ID}-${SESSION_ID}-$(date +%Y%m%d-%H%M%S)"
echo "Creating tag: $TAG_NAME"
git tag -a "$TAG_NAME" -m "Participant ${PARTICIPANT_ID} session ${SESSION_ID} - $(date +%Y-%m-%d\ %H:%M:%S)"

# Export Git log for this participant
LOG_FILE="DATA_COLLECTION/git_log_${PARTICIPANT_ID}_${SESSION_ID}.txt"
echo "Exporting Git log to: $LOG_FILE"
git log --oneline --graph --all --decorate > "$LOG_FILE" 2>/dev/null || true

# Create archive backup as additional safety
BACKUP_DIR="DATA_COLLECTION/participant_backups"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/participant_${PARTICIPANT_ID}_${SESSION_ID}_$(date +%Y%m%d_%H%M%S).tar.gz"
echo "Creating archive backup: $BACKUP_FILE"
tar -czf "$BACKUP_FILE" --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='DATA_COLLECTION' . 2>/dev/null || true

# Create checksum
if [ -f "$BACKUP_FILE" ]; then
    sha256sum "$BACKUP_FILE" > "${BACKUP_FILE}.sha256" 2>/dev/null || md5sum "$BACKUP_FILE" > "${BACKUP_FILE}.md5" 2>/dev/null || true
fi

# Save current state info
STATE_FILE="DATA_COLLECTION/participant_state_${PARTICIPANT_ID}_${SESSION_ID}.json"
cat > "$STATE_FILE" <<EOF
{
  "participant_id": "${PARTICIPANT_ID}",
  "session_id": "${SESSION_ID}",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "branch": "$(git rev-parse --abbrev-ref HEAD)",
  "commit": "$(git rev-parse HEAD)",
  "tag": "${TAG_NAME}",
  "backup_file": "${BACKUP_FILE}",
  "has_uncommitted": $(git diff --quiet && echo "false" || echo "true")
}
EOF

echo ""
echo "✅ Participant work stored successfully!"
echo ""
echo "Summary:"
echo "  Branch: $(git rev-parse --abbrev-ref HEAD)"
echo "  Tag: $TAG_NAME"
echo "  Commit: $(git rev-parse --short HEAD)"
echo "  Backup: $BACKUP_FILE"
echo "  State file: $STATE_FILE"
echo ""
echo "To restore this work later, use:"
echo "  ./SCRIPTS/restore_participant_work.sh $PARTICIPANT_ID $SESSION_ID"
echo ""
