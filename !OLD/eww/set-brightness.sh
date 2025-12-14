#!/bin/bash
# Set brightness for a specific monitor
# Usage: set-brightness.sh <bus_number> <brightness_value>

BUS_NUMBER=$1
BRIGHTNESS_VALUE=$2

if [ -z "$BUS_NUMBER" ] || [ -z "$BRIGHTNESS_VALUE" ]; then
    echo "Usage: $0 <bus_number> <brightness_value>"
    exit 1
fi

# Validate brightness value (0-100)
if [ "$BRIGHTNESS_VALUE" -lt 0 ] || [ "$BRIGHTNESS_VALUE" -gt 100 ]; then
    echo "Brightness value must be between 0 and 100"
    exit 1
fi

# Set brightness using ddcutil
ddcutil setvcp 10 "$BRIGHTNESS_VALUE" --bus "$BUS_NUMBER" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "Brightness set to $BRIGHTNESS_VALUE% on bus $BUS_NUMBER"
else
    echo "Failed to set brightness on bus $BUS_NUMBER"
    exit 1
fi
