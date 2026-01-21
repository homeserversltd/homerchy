#!/onmachine/onmachine/bin/bash

# Fetch latest changes from upstream omarchy repository
# This script sets up the upstream remote and identifies changed files

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STATE_FILE="$SCRIPT_DIR/state/merge-state.json"
UPSTREAM_REPO="https://github.com/basecamp/omarchy.git"
UPSTREAM_BRANCH="master"
UPSTREAM_REMOTE="upstream"

cd "$REPO_ROOT"

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not in a git repository" >&2
    exit 1
fi

# Add or update upstream remote
if git remote get-url "$UPSTREAM_REMOTE" > /dev/null 2>&1; then
    echo "Updating upstream remote..."
    git remote set-url "$UPSTREAM_REMOTE" "$UPSTREAM_REPO"
else
    echo "Adding upstream remote..."
    git remote add "$UPSTREAM_REMOTE" "$UPSTREAM_REPO"
fi

# Fetch latest from upstream
echo "Fetching latest changes from $UPSTREAM_REMOTE/$UPSTREAM_BRANCH..."
git fetch "$UPSTREAM_REMOTE" "$UPSTREAM_BRANCH"

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
UPSTREAM_COMMIT=$(git rev-parse "$UPSTREAM_REMOTE/$UPSTREAM_BRANCH")

# Find files that differ between current branch and upstream
echo "Identifying changed files..."
CHANGED_FILES=$(git diff --name-only "$CURRENT_BRANCH" "$UPSTREAM_REMOTE/$UPSTREAM_BRANCH" 2>/dev/null || \
                git diff --name-only "$UPSTREAM_REMOTE/$UPSTREAM_BRANCH" "$CURRENT_BRANCH" 2>/dev/null)

if [ -z "$CHANGED_FILES" ]; then
    echo "No differences found between $CURRENT_BRANCH and $UPSTREAM_REMOTE/$UPSTREAM_BRANCH"
    exit 0
fi

# Initialize state file
mkdir -p "$(dirname "$STATE_FILE")"

# Create JSON state structure
FILES_JSON="["
FIRST=true
while IFS= read -r file; do
    if [ -n "$file" ]; then
        if [ "$FIRST" = true ]; then
            FIRST=false
        else
            FILES_JSON+=","
        fi
        FILES_JSON+="{\"path\":\"$file\",\"status\":\"pending\",\"action_taken\":null,\"conflict_resolved\":false,\"notes\":\"\"}"
    fi
done <<< "$CHANGED_FILES"
FILES_JSON+="]"

FILE_COUNT=$(echo "$CHANGED_FILES" | grep -c . || echo "0")

cat > "$STATE_FILE" <<EOF
{
  "upstream_remote": "$UPSTREAM_REMOTE",
  "upstream_branch": "$UPSTREAM_BRANCH",
  "upstream_commit": "$UPSTREAM_COMMIT",
  "current_branch": "$CURRENT_BRANCH",
  "current_file_index": 0,
  "files": $FILES_JSON,
  "stats": {
    "total": $FILE_COUNT,
    "accepted": 0,
    "rejected": 0,
    "skipped": 0,
    "conflicts": 0
  }
}
EOF

echo "Found $FILE_COUNT changed file(s)"
echo "State saved to $STATE_FILE"
echo ""
echo "Run ./merge.sh to start the interactive merge process"