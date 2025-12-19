#!/bin/bash

# Main interactive merge script
# Iterates through changed files and allows review/accept/reject

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STATE_FILE="$SCRIPT_DIR/state/merge-state.json"
REVIEW_SCRIPT="$SCRIPT_DIR/review-change.sh"
APPLY_SCRIPT="$SCRIPT_DIR/apply-change.sh"
RESOLVE_SCRIPT="$SCRIPT_DIR/resolve-conflict.sh"

cd "$REPO_ROOT"

# Check if state file exists
if [ ! -f "$STATE_FILE" ]; then
    echo "Error: State file not found. Run fetch-upstream.sh first." >&2
    exit 1
fi

# Check for jq
if ! command -v jq &> /dev/null; then
    echo "Error: jq is required but not installed. Install with: pacman -S jq" >&2
    exit 1
fi

# Check for gum (optional but recommended)
if ! command -v gum &> /dev/null; then
    echo "Warning: gum is not installed. Some features may be limited." >&2
    echo "Install with: pacman -S gum" >&2
    USE_GUM=false
else
    USE_GUM=true
fi

# Load state
CURRENT_INDEX=$(jq -r '.current_file_index' "$STATE_FILE")
TOTAL_FILES=$(jq -r '.stats.total' "$STATE_FILE")
UPSTREAM_REMOTE=$(jq -r '.upstream_remote' "$STATE_FILE")
UPSTREAM_BRANCH=$(jq -r '.upstream_branch' "$STATE_FILE")
UPSTREAM_COMMIT=$(jq -r '.upstream_commit' "$STATE_FILE")

# Get pending files
PENDING_FILES=$(jq -r '.files[] | select(.status == "pending") | .path' "$STATE_FILE")

if [ -z "$PENDING_FILES" ]; then
    echo "No pending files to review."
    echo ""
    echo "Summary:"
    ACCEPTED=$(jq -r '.stats.accepted' "$STATE_FILE")
    REJECTED=$(jq -r '.stats.rejected' "$STATE_FILE")
    SKIPPED=$(jq -r '.stats.skipped' "$STATE_FILE")
    CONFLICTS=$(jq -r '.stats.conflicts' "$STATE_FILE")
    echo "  Accepted: $ACCEPTED"
    echo "  Rejected: $REJECTED"
    echo "  Skipped: $SKIPPED"
    echo "  Conflicts: $CONFLICTS"
    exit 0
fi

# Function to update current index in state
update_index() {
    local new_index=$1
    local temp_state=$(mktemp)
    jq --argjson idx "$new_index" '.current_file_index = $idx' "$STATE_FILE" > "$temp_state"
    mv "$temp_state" "$STATE_FILE"
}

# Function to show file diff
show_diff() {
    local file_path=$1
    "$REVIEW_SCRIPT" "$file_path" 2>&1
}

# Function to handle file review
review_file() {
    local file_path=$1
    local file_index=$2
    
    clear
    if [ "$USE_GUM" = true ]; then
        gum style --foreground 2 "=== File $((file_index + 1)) of $TOTAL_FILES: $file_path ==="
    else
        echo "=== File $((file_index + 1)) of $TOTAL_FILES: $file_path ==="
    fi
    echo ""
    
    # Show diff
    show_diff "$file_path"
    echo ""
    echo "----------------------------------------"
    
    # Check for conflict
    if "$REVIEW_SCRIPT" "$file_path" 2>&1 | grep -q "CONFLICT"; then
        if [ "$USE_GUM" = true ]; then
            gum style --foreground 1 "⚠ CONFLICT DETECTED"
        else
            echo "⚠ CONFLICT DETECTED"
        fi
        echo ""
        
        local choice
        if [ "$USE_GUM" = true ]; then
            choice=$(gum choose "Resolve with AI" "Resolve manually" "Skip for now" "Keep ours" "Accept theirs")
        else
            echo "Options:"
            echo "  1) Resolve with AI"
            echo "  2) Resolve manually"
            echo "  3) Skip for now"
            echo "  4) Keep ours (reject)"
            echo "  5) Accept theirs"
            read -p "Choice [1-5]: " choice_num
            case $choice_num in
                1) choice="Resolve with AI" ;;
                2) choice="Resolve manually" ;;
                3) choice="Skip for now" ;;
                4) choice="Keep ours" ;;
                5) choice="Accept theirs" ;;
                *) choice="Skip for now" ;;
            esac
        fi
        
        case "$choice" in
            "Resolve with AI")
                "$RESOLVE_SCRIPT" "$file_path"
                echo ""
                read -p "Press Enter after resolving the conflict..."
                # Mark as conflict in state
                local temp_state=$(mktemp)
                jq --arg path "$file_path" \
                   '(.files[] | select(.path == $path) | .status) = "conflict" |
                    (.files[] | select(.path == $path) | .conflict_resolved) = true |
                    .stats.conflicts = ([.files[] | select(.status == "conflict")] | length)' \
                   "$STATE_FILE" > "$temp_state"
                mv "$temp_state" "$STATE_FILE"
                ;;
            "Resolve manually")
                ${EDITOR:-nano} "$REPO_ROOT/$file_path"
                read -p "Press Enter after resolving the conflict..."
                local temp_state=$(mktemp)
                jq --arg path "$file_path" \
                   '(.files[] | select(.path == $path) | .status) = "accepted" |
                    (.files[] | select(.path == $path) | .action_taken) = "accept" |
                    (.files[] | select(.path == $path) | .conflict_resolved) = true |
                    .stats.accepted = ([.files[] | select(.status == "accepted")] | length) |
                    .stats.conflicts = ([.files[] | select(.status == "conflict")] | length)' \
                   "$STATE_FILE" > "$temp_state"
                mv "$temp_state" "$STATE_FILE"
                ;;
            "Skip for now")
                "$APPLY_SCRIPT" "$file_path" "skip"
                ;;
            "Keep ours")
                "$APPLY_SCRIPT" "$file_path" "reject"
                ;;
            "Accept theirs")
                "$APPLY_SCRIPT" "$file_path" "accept"
                ;;
        esac
    else
        # No conflict - show options
        local choice
        if [ "$USE_GUM" = true ]; then
            choice=$(gum choose "Accept upstream" "Keep ours" "Skip for now" "View full diff" "Add note")
        else
            echo "Options:"
            echo "  1) Accept upstream"
            echo "  2) Keep ours"
            echo "  3) Skip for now"
            echo "  4) View full diff"
            echo "  5) Add note"
            read -p "Choice [1-5]: " choice_num
            case $choice_num in
                1) choice="Accept upstream" ;;
                2) choice="Keep ours" ;;
                3) choice="Skip for now" ;;
                4) choice="View full diff" ;;
                5) choice="Add note" ;;
                *) choice="Skip for now" ;;
            esac
        fi
        
        case "$choice" in
            "Accept upstream")
                "$APPLY_SCRIPT" "$file_path" "accept"
                ;;
            "Keep ours")
                "$APPLY_SCRIPT" "$file_path" "reject"
                ;;
            "Skip for now")
                "$APPLY_SCRIPT" "$file_path" "skip"
                ;;
            "View full diff")
                git diff "$(git rev-parse --abbrev-ref HEAD)" "$UPSTREAM_REMOTE/$UPSTREAM_BRANCH" -- "$file_path" | ${PAGER:-less}
                review_file "$file_path" "$file_index"  # Recursive call to show menu again
                return
                ;;
            "Add note")
                read -p "Enter note: " note_text
                local temp_state=$(mktemp)
                jq --arg path "$file_path" --arg note "$note_text" \
                   '(.files[] | select(.path == $path) | .notes) = $note' \
                   "$STATE_FILE" > "$temp_state"
                mv "$temp_state" "$STATE_FILE"
                review_file "$file_path" "$file_index"  # Recursive call to show menu again
                return
                ;;
        esac
    fi
}

# Main loop
FILE_ARRAY=()
while IFS= read -r line; do
    [ -n "$line" ] && FILE_ARRAY+=("$line")
done <<< "$PENDING_FILES"

for i in "${!FILE_ARRAY[@]}"; do
    file_path="${FILE_ARRAY[$i]}"
    file_index=$((CURRENT_INDEX + i))
    
    review_file "$file_path" "$file_index"
    
    # Update index
    update_index $((file_index + 1))
    
    # Ask if user wants to continue
    if [ $i -lt $((${#FILE_ARRAY[@]} - 1)) ]; then
        echo ""
        if [ "$USE_GUM" = true ]; then
            gum confirm "Continue to next file?" && continue || break
        else
            read -p "Continue to next file? [Y/n]: " cont
            [ "${cont:-Y}" != "n" ] && [ "${cont:-Y}" != "N" ] || break
        fi
    fi
done

# Final summary
clear
echo "=== Merge Review Complete ==="
echo ""
ACCEPTED=$(jq -r '.stats.accepted' "$STATE_FILE")
REJECTED=$(jq -r '.stats.rejected' "$STATE_FILE")
SKIPPED=$(jq -r '.stats.skipped' "$STATE_FILE")
CONFLICTS=$(jq -r '.stats.conflicts' "$STATE_FILE")
PENDING=$(jq -r '[.files[] | select(.status == "pending")] | length' "$STATE_FILE")

echo "Summary:"
echo "  Accepted: $ACCEPTED"
echo "  Rejected: $REJECTED"
echo "  Skipped: $SKIPPED"
echo "  Conflicts: $CONFLICTS"
echo "  Pending: $PENDING"
echo ""

if [ "$ACCEPTED" -gt 0 ] || [ "$CONFLICTS" -gt 0 ]; then
    echo "Files have been staged. Review with 'git status' and commit when ready."
    echo ""
    if [ "$USE_GUM" = true ]; then
        gum confirm "View git status?" && git status
    else
        read -p "View git status? [Y/n]: " view_status
        [ "${view_status:-Y}" != "n" ] && [ "${view_status:-Y}" != "N" ] && git status
    fi
fi