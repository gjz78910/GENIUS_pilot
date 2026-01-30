#!/bin/bash
# Reset environment to initial codebase state
# Usage: ./reset_environment.sh [participant_id] [session_id]
# 
# IMPORTANT: Run store_participant_work.sh FIRST to save participant work!

set -e  # Exit on error

PARTICIPANT_ID="$1"
SESSION_ID="${2:-SESSION1}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "🔄 Resetting environment to initial state..."
echo ""

# Safety check: Warn if participant work might not be stored
if [ -n "$PARTICIPANT_ID" ]; then
    STATE_FILE="DATA_COLLECTION/participant_state_${PARTICIPANT_ID}_${SESSION_ID}.json"
    if [ ! -f "$STATE_FILE" ]; then
        echo "⚠️  WARNING: No state file found for participant $PARTICIPANT_ID"
        echo "   Make sure you ran: ./SCRIPTS/store_participant_work.sh $PARTICIPANT_ID $SESSION_ID"
        read -p "   Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Aborted. Please store participant work first."
            exit 1
        fi
    fi
fi

# Check if Git is initialized
if [ ! -d ".git" ]; then
    echo "⚠️  WARNING: Not a Git repository. Cannot reset via Git."
    echo "   Please manually restore from backup or initial codebase."
    exit 1
fi

# Check current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $CURRENT_BRANCH"

# Find initial/main branch
if git show-ref --verify --quiet "refs/heads/main"; then
    INITIAL_BRANCH="main"
elif git show-ref --verify --quiet "refs/heads/master"; then
    INITIAL_BRANCH="master"
else
    # Use the first branch or current if only one exists
    INITIAL_BRANCH=$(git branch | head -1 | sed 's/^[* ] //')
    echo "⚠️  Using branch '$INITIAL_BRANCH' as initial branch"
fi

# Switch to initial branch
if [ "$CURRENT_BRANCH" != "$INITIAL_BRANCH" ]; then
    echo "Switching to initial branch: $INITIAL_BRANCH"
    git checkout "$INITIAL_BRANCH" 2>/dev/null || {
        echo "⚠️  Could not checkout $INITIAL_BRANCH. Creating it from current state..."
        git checkout -b "$INITIAL_BRANCH"
    }
fi

# Reset to initial commit (or HEAD if no specific initial commit)
# Try to find a tag or commit marked as initial
INITIAL_COMMIT=""
if git rev-parse --verify --quiet "refs/tags/initial" >/dev/null 2>&1; then
    INITIAL_COMMIT="initial"
    echo "Found 'initial' tag, resetting to it..."
elif git rev-parse --verify --quiet "refs/tags/v1.0" >/dev/null 2>&1; then
    INITIAL_COMMIT="v1.0"
    echo "Found 'v1.0' tag, resetting to it..."
else
    # Use the first commit or HEAD
    INITIAL_COMMIT=$(git rev-list --max-parents=0 HEAD 2>/dev/null | head -1 || echo "HEAD")
    echo "Resetting to: $INITIAL_COMMIT"
fi

# Hard reset to initial state
echo "Performing hard reset..."
git reset --hard "$INITIAL_COMMIT" 2>/dev/null || {
    echo "⚠️  Could not reset to $INITIAL_COMMIT. Using HEAD instead."
    git reset --hard HEAD
}

# Clean working directory
echo "Cleaning working directory..."
git clean -fd

# Remove Python cache
echo "Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true

# Remove generated reports (but keep DATA_COLLECTION)
echo "Cleaning generated reports..."
rm -rf reports/*.csv 2>/dev/null || true

# Remove .coverage and test artifacts
rm -f .coverage coverage.xml htmlcov -rf 2>/dev/null || true

# Verify demo works
echo ""
echo "Verifying reset was successful..."
echo ""

if python -m src.demo > /dev/null 2>&1; then
    echo "✅ Demo runs successfully"
else
    echo "⚠️  WARNING: Demo failed to run. Check for issues."
    python -m src.demo || true
fi

# Run basic tests
echo "Running basic tests..."
if python -m unittest tests.test_models -v > /dev/null 2>&1; then
    echo "✅ Basic tests pass"
else
    echo "⚠️  WARNING: Some tests failed. Check output above."
    python -m unittest tests.test_models -v || true
fi

echo ""
echo "✅ Environment reset complete!"
echo ""
echo "Summary:"
echo "  Reset to branch: $(git rev-parse --abbrev-ref HEAD)"
echo "  Reset to commit: $(git rev-parse --short HEAD)"
echo "  Python cache: Cleaned"
echo "  Generated files: Cleaned"
echo ""
echo "Environment is ready for next participant."
echo ""
