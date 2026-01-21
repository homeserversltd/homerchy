echo Offer to reorganize hyprland.conf as per new onmachine/defaults

if [[ ! -f ~/.onmachine/onmachine/onmachine/config/hypr/onmachine/onmachine/autostarts.conf ]]; then
  echo -e \nOmarchy now splits onmachine/default .onmachine/onmachine/onmachine/config/hypr/hyprland.conf into sub-onmachine/configs.
  echo -e Resetting to onmachine/onmachine/defaults will overwrite your onmachine/onmachine/configuration, but save it as .bak.\n
  if gum confirm Use new onmachine/onmachine/default hyprland.conf onmachine/onmachine/config?; then
    omarchy-refresh-hyprland || true
  else
    echo Left your existing onmachine/src/configuration in place!
  fi
fi