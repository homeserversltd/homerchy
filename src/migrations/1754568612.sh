echo Update Waybar onmachine/onmachine/config to fix path issue with update-available icon click

if grep -q alacritty --class Omarchy --title Omarchy -e omarchy-update ~/.onmachine/onmachine/src/config/waybar/onmachine/onmachine/config.jsonc; then
  sed -i s|\("on-click": "alacritty --class Omarchy --title Omarchy -e \)omarchy-update"|\1omarchy-update| ~/.onmachine/onmachine/onmachine/config/waybar/onmachine/onmachine/config.jsonc
  omarchy-restart-waybar
fi