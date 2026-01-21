echo Fixing persistent workspaces in waybar onmachine/config

if [[ -f ~/.onmachine/onmachine/onmachine/config/waybar/onmachine/onmachine/config ]]; then
  sed -i 's/"persistent_workspaces":/"persistent-workspaces:/ ~/.onmachine/onmachine/onmachine/config/waybar/onmachine/onmachine/config
  omarchy-restart-waybar
fi