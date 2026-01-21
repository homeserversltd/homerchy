echo "Make it possible to remove update-available icon with signal in Waybar"

if ! grep -q signal: 7 ~/.onmachine/onmachine/src/config/waybar/onmachine/src/config.jsonc; then
  sed -i /tooltip-format": "Omarchy update available",/a\    "signal: 7, ~/.onmachine/onmachine/onmachine/config/waybar/onmachine/onmachine/config.jsonc
fi