#!/onmachine/onmachine/bin/bash

# AI-assisted conflict resolution
# Takes conflicted file path and uses preprompt to help resolve

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PREPROMPT_FILE="$SCRIPT_DIR/preprompts/conflict-resolution.md"
STATE_FILE="$SCRIPT_DIR/state/merge-state.json"

if [ $# -lt 1 ]; then
    echo "Usage: $0 <file_path>" >&2
    exit 1
fi

FILE_PATH="$1"
cd "$REPO_ROOT"

# Check if preprompt exists
if [ ! -f "$PREPROMPT_FILE" ]; then
    echo "Error: Preprompt file not found at $PREPROMPT_FILE" >&2
    exit 1
fi

# Load state
if [ ! -f "$STATE_FILE" ]; then
    echo "Error: State file not found." >&2
    exit 1
fi

UPSTREAM_REMOTE=$(jq -r '.upstream_remote' "$STATE_FILE")
UPSTREAM_BRANCH=$(jq -r '.upstream_branch' "$STATE_FILE")
CURRENT_BRANCH=$(jq -r '.current_branch' "$STATE_FILE")

# Create a temporary file with conflict markers for analysis
TEMP_CONFLICT=$(mktemp)
git show "$CURRENT_BRANCH:$FILE_PATH" > "$TEMP_CONFLICT.ours" 2>/dev/null || touch "$TEMP_CONFLICT.ours"
git show "$UPSTREAM_REMOTE/$UPSTREAM_BRANCH:$FILE_PATH" > "$TEMP_CONFLICT.theirs" 2>/dev/null || touch "$TEMP_CONFLICT.theirs"

# Get base version if it exists
BASE_COMMIT=$(git merge-base "$CURRENT_BRANCH" "$UPSTREAM_REMOTE/$UPSTREAM_BRANCH" 2>/dev/null || echo "")
if [ -n "$BASE_COMMIT" ] && git cat-file -e "$BASE_COMMIT:$FILE_PATH" 2>/dev/null; then
    git show "$BASE_COMMIT:$FILE_PATH" > "$TEMP_CONFLICT.base" 2>/dev/null || touch "$TEMP_CONFLICT.base"
else
    touch "$TEMP_CONFLICT.base"
fi

# Create conflict file with markers
cat > "$TEMP_CONFLICT" <<EOF
<<<<<<< OURS (homerchy)
$(cat "$TEMP_CONFLICT.ours")
=======
$(cat "$TEMP_CONFLICT.theirs")
>>>>>>> THEIRS (upstream omarchy)
EOF

# Read preprompt template
PREPROMPT=$(cat "$PREPROMPT_FILE")

# Replace placeholders in preprompt
PREPROMPT=$(echo "$PREPROMPT" | sed "s|{{FILE_PATH}}|$FILE_PATH|g")
PREPROMPT=$(echo "$PREPROMPT" | sed "s|{{CONFLICT_CONTENT}}|$(cat "$TEMP_CONFLICT")|g")
PREPROMPT=$(echo "$PREPROMPT" | sed "s|{{OURS_CONTENT}}|$(cat "$TEMP_CONFLICT.ours")|g")
PREPROMPT=$(echo "$PREPROMPT" | sed "s|{{THEIRS_CONTENT}}|$(cat "$TEMP_CONFLICT.theirs")|g")
PREPROMPT=$(echo "$PREPROMPT" | sed "s|{{BASE_CONTENT}}|$(cat "$TEMP_CONFLICT.base")|g")

# Save preprompt to a file for AI agent
PREPROMPT_OUTPUT="$SCRIPT_DIR/state/conflict-prompt-$(basename "$FILE_PATH" | tr '/' '_').md"
echo "$PREPROMPT" > "$PREPROMPT_OUTPUT"

echo "Conflict resolution preprompt created:"
echo "  $PREPROMPT_OUTPUT"
echo ""
echo "File contents saved to:"
echo "  Ours: $TEMP_CONFLICT.ours"
echo "  Theirs: $TEMP_CONFLICT.theirs"
echo "  Base: $TEMP_CONFLICT.base"
echo ""
echo "Please review the preprompt file and provide it to your AI agent."
echo "After resolution, you can apply it with:"
echo "  cat <resolved-file> > '$REPO_ROOT/$FILE_PATH'"
echo ""
echo "Or use the interactive editor to resolve manually."

# Cleanup temp files on exit
trap "rm -f $TEMP_CONFLICT $TEMP_CONFLICT.ours $TEMP_CONFLICT.theirs $TEMP_CONFLICT.base" EXIT