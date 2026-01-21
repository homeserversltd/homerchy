echo "Update Waybar for new Omarchy menu"

if ! grep -q  ~/.onmachine/onmachine/onmachine/config/waybar/onmachine/onmachine/config.jsonc; then
  omarchy-refresh-waybar
fi