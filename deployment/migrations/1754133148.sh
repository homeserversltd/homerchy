echo "Update Waybar CSS to dim unused workspaces"

if ! grep -q #workspaces button\.empty ~/.onmachine/onmachine/onmachine/config/waybar/style.css; then
  omarchy-refresh-onmachine/onmachine/config waybar/style.css
  omarchy-restart-waybar
fi