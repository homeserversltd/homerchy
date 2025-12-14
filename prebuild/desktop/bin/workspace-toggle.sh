#!/bin/bash
# Workspace Toggle Script with State Tracking
# Toggles between Set A (1,2,3...) and Set B (4,5,6...) across all monitors
# Usage: workspace-toggle.sh [move-window]
#   - No args: Just toggle workspaces
#   - 'move-window': Move active window along with workspace transition

# State file to track current workspace set
STATE_FILE="/tmp/workspace-toggle-state"

# Get all monitor names
MONITORS=($(hyprctl monitors | grep "^Monitor" | awk '{print $2}' | sed 's/://'))

# Check current workspace on first monitor to determine current set
FIRST_MONITOR="${MONITORS[0]}"
CURRENT_WS=$(hyprctl monitors | grep -A 10 "$FIRST_MONITOR" | grep "active workspace" | awk '{print $3}' | cut -d, -f1)

echo "Detected monitors: ${MONITORS[*]}"
echo "Current workspace on $FIRST_MONITOR: $CURRENT_WS"

# Determine target workspaces based on current set
if [[ "$CURRENT_WS" == "1" ]]; then
    # Currently on Set A (1,2,3...), switch to Set B (4,5,6...)
    echo "Switching to Set B: workspaces 4,5,6..."
    TARGET_START=4
    NEW_STATE="B"
else
    # Currently on Set B (4,5,6...) or other, switch to Set A (1,2,3...)
    echo "Switching to Set A: workspaces 1,2,3..."
    TARGET_START=1
    NEW_STATE="A"
fi

# Get active window info if we need to move it
ACTIVE_WINDOW=""
if [[ "$1" == "move-window" ]]; then
    ACTIVE_WINDOW=$(hyprctl activewindow -j | jq -r '.address')
    if [[ -n "$ACTIVE_WINDOW" && "$ACTIVE_WINDOW" != "null" && "$ACTIVE_WINDOW" != "0x0" ]]; then
        echo "Moving active window $ACTIVE_WINDOW with workspace transition"
    else
        echo "No active window to move"
        ACTIVE_WINDOW=""
    fi
fi

# If we have an active window to move, move it first to the target workspace
if [[ -n "$ACTIVE_WINDOW" ]]; then
    echo "Moving window $ACTIVE_WINDOW to workspace $TARGET_START"
    hyprctl dispatch movetoworkspace "$TARGET_START,address:$ACTIVE_WINDOW"
fi

# Loop through each monitor and forcefully bind workspaces
for i in "${!MONITORS[@]}"; do
    MONITOR="${MONITORS[$i]}"
    TARGET_WS=$((TARGET_START + i))
    
    echo "Binding workspace $TARGET_WS to $MONITOR"
    # Move workspace to monitor (creates if doesn't exist)
    hyprctl dispatch moveworkspacetomonitor "$TARGET_WS" "$MONITOR"
    # Focus the monitor
    hyprctl dispatch focusmonitor "$MONITOR"
    # Switch to the workspace
    hyprctl dispatch workspace "$TARGET_WS"
done

# Save the new state
echo "$NEW_STATE" > "$STATE_FILE"

echo "Workspace toggle complete! Now on Set $NEW_STATE"