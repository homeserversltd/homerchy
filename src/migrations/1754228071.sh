echo "Add auto-update icon to waybar when update available"

if ! grep -q custom/update ~/.onmachine/onmachine/onmachine/config/waybar/onmachine/onmachine/config.jsonc; then
  omarchy-refresh-waybar
fi