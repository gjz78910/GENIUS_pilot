#!/bin/bash
# Restore a participant's stored work
# Usage: ./restore_participant_work.sh <participant_id> [session_id] [--separate-dir]

set -e  # Exit on error

PARTICIPANT_ID="$1"
SESSION_ID="${2:-SESSION1}"
SEPARATE_DIR=false

# Check for --separate-dir flag
if [[ "$*" == *"--separate-dir"* ]]; then
    SEPARATE_DIR=true
fi

if [ -z "$PARTICIPANT_ID" ]; then
    echo "ERROR: Participant ID required"
    echo "Usage: $0 <participant_id> [session_id] [--separate-dir]"
    echo ""
    echo "Options:"
    echo "  --separate-dir    Restore to separate directory instead of main repo"
    echo ""
    echo "To list available participants:"
    echo "  $0 --list"
    exit 1
fi

# List available participants
if [ "$PARTICIPANT_ID" == "--list" ]; then
    echo "Available stored participants:"
    echo ""
    
    # List from Git branches
    if [ -d ".git" ]; then
        echo "Git branches:"
        git branch | grep "participant-" | sed 's/^[* ] /  - /' || echo "  (none)"
        echo ""
        
        echo "Git tags:"
        git tag | grep "participant-" | head -10 | sed 's/^/  - /' || echo "  (none)"
        echo ""
    fi
    
    # List from state files
    if [ -d "DATA_COLLECTION" ]; then
        echo "State files:"
        ls -1 DATA_COLLECTION/participant_state_*.json 2>/dev/null | sed 's/.*participant_state_\(.*\)\.json/  - \1/' || echo "  (none)"
        echo ""
        
        echo "Backup archives:"
        if [ -d "DATA_COLLECTION/participant_backups" ]; then
            ls -1 DATA_COLLECTION/participant_backups/*.tar.gz 2>/dev/null | sed 's/.*participant_\(.*\)\.tar\.gz/  - \1/' | head -10 || echo "  (none)"
        else
            echo "  (none)"
        fi
    fi
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Restoring work for participant: $PARTICIPANT_ID (session: $SESSION_ID)"
echo ""

if [ "$SEPARATE_DIR" = true ]; then
    RESTORE_DIR="participant_${PARTICIPANT_ID}_restored"
    echo "Restoring to separate directory: $RESTORE_DIR"
    mkdir -p "$RESTORE_DIR"
    cd "$RESTORE_DIR"
fi

# Check if Git is initialized
if [ ! -d ".git" ]; then
    echo "⚠️  Not a Git repository. Restoring from backup archive..."
    
    STATE_FILE="../DATA_COLLECTION/participant_state_${PARTICIPANT_ID}_${SESSION_ID}.json"
    if [ -f "$STATE_FILE" ]; then
        BACKUP_FILE=$(grep -o '"backup_file": "[^"]*"' "$STATE_FILE" | cut -d'"' -f4)
        if [ -n "$BACKUP_FILE" ] && [ -f "../$BACKUP_FILE" ]; then
            echo "Extracting from: $BACKUP_FILE"
            tar -xzf "../$BACKUP_FILE"
            echo "✅ Restored from backup archive"
            exit 0
        fi
    fi
    
    # Try to find any backup for this participant
    BACKUP_DIR="../DATA_COLLECTION/participant_backups"
    if [ -d "$BACKUP_DIR" ]; then
        LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/participant_${PARTICIPANT_ID}_*.tar.gz 2>/dev/null | head -1)
        if [ -n "$LATEST_BACKUP" ]; then
            echo "Extracting from latest backup: $LATEST_BACKUP"
            tar -xzf "../$LATEST_BACKUP"
            echo "✅ Restored from backup archive"
            exit 0
        fi
    fi
    
    echo "❌ ERROR: No backup archive found for participant $PARTICIPANT_ID"
    exit 1
fi

# Try to restore from Git branch
BRANCH_NAME="participant-${PARTICIPANT_ID}"
if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
    echo "Found Git branch: $BRANCH_NAME"
    git checkout "$BRANCH_NAME"
    echo "✅ Restored from Git branch"
    exit 0
fi

# Try to restore from Git tag
TAG_PATTERN="participant-${PARTICIPANT_ID}-${SESSION_ID}"
LATEST_TAG=$(git tag | grep "^$TAG_PATTERN" | sort -r | head -1)

if [ -n "$LATEST_TAG" ]; then
    echo "Found Git tag: $LATEST_TAG"
    git checkout "$LATEST_TAG"
    echo "✅ Restored from Git tag"
    exit 0
fi

# Try to restore from state file
STATE_FILE="DATA_COLLECTION/participant_state_${PARTICIPANT_ID}_${SESSION_ID}.json"
if [ -f "$STATE_FILE" ]; then
    COMMIT=$(grep -o '"commit": "[^"]*"' "$STATE_FILE" | cut -d'"' -f4)
    if [ -n "$COMMIT" ] && git rev-parse --verify --quiet "$COMMIT" >/dev/null 2>&1; then
        echo "Found commit in state file: $COMMIT"
        git checkout "$COMMIT"
        echo "✅ Restored from commit"
        exit 0
    fi
fi

# Last resort: try backup archive
BACKUP_DIR="DATA_COLLECTION/participant_backups"
if [ -d "$BACKUP_DIR" ]; then
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/participant_${PARTICIPANT_ID}_*.tar.gz 2>/dev/null | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        echo "⚠️  No Git reference found. Extracting from backup archive..."
        echo "Extracting from: $LATEST_BACKUP"
        tar -xzf "$LATEST_BACKUP"
        echo "✅ Restored from backup archive"
        exit 0
    fi
fi

echo "❌ ERROR: Could not find stored work for participant $PARTICIPANT_ID"
echo ""
echo "Tried:"
echo "  - Git branch: $BRANCH_NAME"
echo "  - Git tags matching: $TAG_PATTERN"
echo "  - State file: $STATE_FILE"
echo "  - Backup archives in: $BACKUP_DIR"
echo ""
echo "To list available participants, run:"
echo "  $0 --list"
exit 1
