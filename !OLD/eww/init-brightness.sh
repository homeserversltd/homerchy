#!/bin/bash
# Initialize brightness variables with actual monitor values

BRIGHTNESS_VALUES=$(/home/owner/git/omarchy/desktop/eww/get-brightness.sh)
MONITOR1_BRIGHTNESS=$(echo $BRIGHTNESS_VALUES | awk '{print $1}')
MONITOR2_BRIGHTNESS=$(echo $BRIGHTNESS_VALUES | awk '{print $2}')
MONITOR3_BRIGHTNESS=$(echo $BRIGHTNESS_VALUES | awk '{print $3}')

# Update EWW variables with actual values
eww update monitor1-brightness="$MONITOR1_BRIGHTNESS" --config /home/owner/git/omarchy/desktop/eww
eww update monitor2-brightness="$MONITOR2_BRIGHTNESS" --config /home/owner/git/omarchy/desktop/eww
eww update monitor3-brightness="$MONITOR3_BRIGHTNESS" --config /home/owner/git/omarchy/desktop/eww

echo "Initialized brightness: $MONITOR1_BRIGHTNESS $MONITOR2_BRIGHTNESS $MONITOR3_BRIGHTNESS"
