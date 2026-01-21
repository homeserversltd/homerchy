#!/onmachine/onmachine/bin/bash

# Review individual file changes
# Takes file path as argument and shows diff

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STATE_FILE="$SCRIPT_DIR/state/merge-state.json"

if [ $# -lt 1 ]; then
    echo "Usage: $0 <file_path>" >&2
    exit 1
fi

FILE_PATH="$1"
cd "$REPO_ROOT"

# Load state
if [ ! -f "$STATE_FILE" ]; then
    echo "Error: State file not found. Run fetch-upstream.sh first." >&2
    exit 1
fi

UPSTREAM_REMOTE=$(jq -r '.upstream_remote' "$STATE_FILE")
UPSTREAM_BRANCH=$(jq -r '.upstream_branch' "$STATE_FILE")
CURRENT_BRANCH=$(jq -r '.current_branch' "$STATE_FILE")

# Check if file exists in upstream
if ! git cat-file -e "$UPSTREAM_REMOTE/$UPSTREAM_BRANCH:$FILE_PATH" 2>/dev/null; then
    echo "File $FILE_PATH does not exist in upstream (new file in our branch)"
    exit 0
fi

# Check if file exists in current branch
if ! git cat-file -e "$CURRENT_BRANCH:$FILE_PATH" 2>/dev/null; then
    echo "File $FILE_PATH does not exist in current branch (new file in upstream)"
    exit 0
fi

# Check for conflicts
if git merge-tree "$(git merge-base "$CURRENT_BRANCH" "$UPSTREAM_REMOTE/$UPSTREAM_BRANCH")" "$CURRENT_BRANCH" "$UPSTREAM_REMOTE/$UPSTREAM_BRANCH" | grep -q "^+<<<<<<< " 2>/dev/null; then
    echo "CONFLICT"
    exit 2
fi

# Show diff
echo "=== Diff for $FILE_PATH ==="
echo ""
git diff "$CURRENT_BRANCH" "$UPSTREAM_REMOTE/$UPSTREAM_BRANCH" -- "$FILE_PATH" || \
git diff "$UPSTREAM_REMOTE/$UPSTREAM_BRANCH" "$CURRENT_BRANCH" -- "$FILE_PATH"