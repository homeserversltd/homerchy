#!/bin/bash
# Bang Widget Toggle Script

# Check if EWW daemon is running
if ! pgrep -x "eww" > /dev/null; then
    eww daemon --config /home/owner/git/omarchy/desktop/eww
    sleep 2
fi

# Open the bang window
eww open bang --config /home/owner/git/omarchy/desktop/eww

# Wait 1 second
sleep 1

# Close the bang window
eww close bang --config /home/owner/git/omarchy/desktop/eww
