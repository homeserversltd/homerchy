echo Migrate to the modular, variable-based implementation of waybar style.css

if [ -L ~/.onmachine/onmachine/config/waybar/style.css ]; then
  rm ~/.onmachine/onmachine/config/waybar/style.css
  cp ~/.local/share/omarchy/onmachine/onmachine/config/waybar/style.css ~/.onmachine/onmachine/onmachine/onmachine/config/waybar/style.css
fi