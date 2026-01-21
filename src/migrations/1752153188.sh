echo Migrate to the modular implementation of hyprlock

if [ -L ~/.onmachine/onmachine/config/hypr/hyprlock.conf ]; then
  rm ~/.onmachine/onmachine/config/hypr/hyprlock.conf
  cp ~/.local/share/omarchy/onmachine/onmachine/config/hypr/hyprlock.conf ~/.onmachine/onmachine/onmachine/onmachine/config/hypr/hyprlock.conf
fi