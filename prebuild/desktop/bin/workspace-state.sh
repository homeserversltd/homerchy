#!/bin/bash
# Workspace State Display Script for Waybar
# Shows current workspace set with progress bar visual

STATE_FILE="/tmp/workspace-toggle-state"

# Check if state file exists, if not create it with default state
if [[ ! -f "$STATE_FILE" ]]; then
    echo "A" > "$STATE_FILE"
fi

# Read current state
CURRENT_STATE=$(cat "$STATE_FILE")

# Display the progress bar based on state
if [[ "$CURRENT_STATE" == "A" ]]; then
    echo "████░░░░░░"
else
    echo "░░░░░░████"
fi

