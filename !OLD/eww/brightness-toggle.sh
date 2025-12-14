#!/bin/bash
# Brightness Widget Toggle Script

EWW_CONFIG_DIR="/home/owner/git/omarchy/desktop/eww"

# Check if EWW daemon is running
if ! pgrep -x "eww" > /dev/null; then
    eww daemon --config $EWW_CONFIG_DIR
    sleep 2
fi

# Try to close first, if it fails, then open
if ! eww close brightness --config $EWW_CONFIG_DIR 2>/dev/null; then
    # Initialize brightness values with actual monitor readings
    $EWW_CONFIG_DIR/init-brightness.sh
    # Open the brightness window
    eww open brightness --config $EWW_CONFIG_DIR
fi
