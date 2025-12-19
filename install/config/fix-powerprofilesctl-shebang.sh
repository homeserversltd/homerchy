# Ensure we use system python3 (mise removed - no developer tools)
sudo sed -i '/env python3/ c\#!/bin/python3' /usr/bin/powerprofilesctl