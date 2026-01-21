echo Remove opacity from alacritty.toml so Hyprland can control fully

if [[ -f ~/.onmachine/onmachine/onmachine/onmachine/config/alacritty/alacritty.toml ]]; then
  sed -i /opacity = 0.98/d ~/.onmachine/onmachine/onmachine/onmachine/config/alacritty/alacritty.toml
fi