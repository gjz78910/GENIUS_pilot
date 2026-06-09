#!/usr/bin/env bash
# Prepare participant git branches for a GENIUS experiment session and print
# the matching terraform.tfvars roster block.
#
# Usage:
#   ./SCRIPTS/prepare_vms.sh --type manual --count 4 --session S1
#   ./SCRIPTS/prepare_vms.sh --type ai     --count 4 --session S1 [--start-id 1]
#
# What it does:
#   1. Creates git branches participant/<type>-01 … participant/<type>-N from
#      the current main HEAD and pushes them to origin.
#   2. Prints the participant_roster HCL block to paste into terraform.tfvars.
#
# Run this from the root of the GENIUS_pilot repo on the main branch.

set -euo pipefail

TYPE=""
COUNT=""
SESSION="S1"
START_ID=1

usage() {
  echo "Usage: $0 --type manual|ai --count N [--session S1] [--start-id 1]"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --type)     TYPE="$2";     shift 2 ;;
    --count)    COUNT="$2";    shift 2 ;;
    --session)  SESSION="$2";  shift 2 ;;
    --start-id) START_ID="$2"; shift 2 ;;
    *) usage ;;
  esac
done

[[ -z "$TYPE" || -z "$COUNT" ]] && usage
[[ "$TYPE" != "manual" && "$TYPE" != "ai" ]] && { echo "ERROR: --type must be manual or ai"; exit 1; }
[[ ! "$COUNT" =~ ^[1-9][0-9]*$ ]] && { echo "ERROR: --count must be a positive integer"; exit 1; }

# Must be on main and repo clean of unstaged changes to critical files
CURRENT_BRANCH=$(git branch --show-current)
if [[ "$CURRENT_BRANCH" != "main" ]]; then
  echo "WARNING: currently on branch '$CURRENT_BRANCH', not 'main'."
  echo "Participant branches will be created from HEAD of '$CURRENT_BRANCH'."
  read -r -p "Continue? [y/N] " confirm
  [[ "$confirm" =~ ^[Yy]$ ]] || exit 1
fi

HEAD_COMMIT=$(git rev-parse HEAD)
echo "Creating participant branches from HEAD: $HEAD_COMMIT"
echo ""

# --- Phase 1: create and push branches ---

CREATED=()
SKIPPED=()

for i in $(seq "$START_ID" $((START_ID + COUNT - 1))); do
  ID=$(printf "%s-%02d" "$TYPE" "$i")
  BRANCH="participant/$ID"

  if git ls-remote --exit-code --heads origin "$BRANCH" > /dev/null 2>&1; then
    echo "  SKIP  $BRANCH  (already exists on remote)"
    SKIPPED+=("$BRANCH")
  else
    git push origin "$HEAD_COMMIT:refs/heads/$BRANCH" --no-verify
    echo "  OK    $BRANCH"
    CREATED+=("$BRANCH")
  fi
done

echo ""
if [[ ${#SKIPPED[@]} -gt 0 ]]; then
  echo "Skipped (already exist): ${SKIPPED[*]}"
fi
echo "Created: ${#CREATED[@]} branch(es)"
echo ""

# --- Phase 2: print terraform roster block ---

echo "======================================================================"
echo "Add the following to infrastructure/aws-dcv/terraform/terraform.tfvars"
echo "======================================================================"
echo ""

# Determine indent: if this is the first block, print the full variable
# declaration; otherwise just the list entries so it can be appended.
echo "# --- $TYPE group ---"
for i in $(seq "$START_ID" $((START_ID + COUNT - 1))); do
  ID=$(printf "%s-%02d" "$TYPE" "$i")
  printf '  { participant_id = "%s", session_id = "%s", condition = "%s" },\n' \
    "$ID" "$SESSION" "$TYPE"
done
echo ""
echo "(Paste these lines inside the participant_roster = [ ... ] block)"
