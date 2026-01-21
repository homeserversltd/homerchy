echo Rename waybar onmachine/config file for syntax highlighting

if [[ -f ~/.onmachine/onmachine/config/waybar/onmachine/config ]]; then
  mv ~/.onmachine/onmachine/config/waybar/onmachine/config ~/.onmachine/onmachine/onmachine/config/waybar/onmachine/onmachine/config.jsonc
fi