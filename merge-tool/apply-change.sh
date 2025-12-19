#!/bin/bash

# Apply accepted changes to a file
# Usage: apply-change.sh <file_path> <action>
# Actions: accept, reject, skip

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STATE_FILE="$SCRIPT_DIR/state/merge-state.json"

if [ $# -lt 2 ]; then
    echo "Usage: $0 <file_path> <action>" >&2
    echo "Actions: accept, reject, skip" >&2
    exit 1
fi

FILE_PATH="$1"
ACTION="$2"

cd "$REPO_ROOT"

# Load state
if [ ! -f "$STATE_FILE" ]; then
    echo "Error: State file not found." >&2
    exit 1
fi

UPSTREAM_REMOTE=$(jq -r '.upstream_remote' "$STATE_FILE")
UPSTREAM_BRANCH=$(jq -r '.upstream_branch' "$STATE_FILE")
CURRENT_BRANCH=$(jq -r '.current_branch' "$STATE_FILE")

# Update state file
TEMP_STATE=$(mktemp)
jq --arg path "$FILE_PATH" \
   --arg action "$ACTION" \
   --arg status "$(case $ACTION in accept) echo "accepted" ;; reject) echo "rejected" ;; skip) echo "skipped" ;; *) echo "pending" ;; esac)" \
   '(.files[] | select(.path == $path) | .status) = $status | 
    (.files[] | select(.path == $path) | .action_taken) = $action |
    .stats.accepted = ([.files[] | select(.status == "accepted")] | length) |
    .stats.rejected = ([.files[] | select(.status == "rejected")] | length) |
    .stats.skipped = ([.files[] | select(.status == "skipped")] | length)' \
   "$STATE_FILE" > "$TEMP_STATE"
mv "$TEMP_STATE" "$STATE_FILE"

case "$ACTION" in
    accept)
        # Check if file exists in upstream
        if git cat-file -e "$UPSTREAM_REMOTE/$UPSTREAM_BRANCH:$FILE_PATH" 2>/dev/null; then
            # File exists in upstream - checkout that version
            git checkout "$UPSTREAM_REMOTE/$UPSTREAM_BRANCH" -- "$FILE_PATH"
            echo "Applied upstream version of $FILE_PATH"
        else
            # File doesn't exist in upstream - remove it
            git rm "$FILE_PATH" 2>/dev/null || rm -f "$FILE_PATH"
            echo "Removed $FILE_PATH (doesn't exist in upstream)"
        fi
        ;;
    reject)
        # Keep our version - do nothing, just mark in state
        echo "Kept our version of $FILE_PATH"
        ;;
    skip)
        # Do nothing, will be reviewed later
        echo "Skipped $FILE_PATH"
        ;;
    *)
        echo "Unknown action: $ACTION" >&2
        exit 1
        ;;
esac