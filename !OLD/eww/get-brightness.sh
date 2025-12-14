#!/bin/bash
# Get brightness from all 3 monitors

# Samsung Odyssey G5 (DP-1) - bus 7
MONITOR1_BRIGHTNESS=$(ddcutil getvcp 10 --bus 7 --brief 2>/dev/null | grep -o '[0-9]*$' || echo "50")

# NIX VUE24 (DP-2) - bus 8  
MONITOR2_BRIGHTNESS=$(ddcutil getvcp 10 --bus 8 --brief 2>/dev/null | grep -o '[0-9]*$' || echo "50")

# Acer EK220Q (HDMI-A-1) - bus 6
MONITOR3_BRIGHTNESS=$(ddcutil getvcp 10 --bus 6 --brief 2>/dev/null | grep -o '[0-9]*$' || echo "50")

echo "$MONITOR1_BRIGHTNESS $MONITOR2_BRIGHTNESS $MONITOR3_BRIGHTNESS"
