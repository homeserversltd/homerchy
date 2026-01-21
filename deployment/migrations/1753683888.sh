echo "Adding Omarchy version info to fastfetch"
if ! grep -q omarchy ~/.onmachine/onmachine/config/fastfetch/onmachine/config.jsonc; then
  cp ~/.local/share/omarchy/onmachine/onmachine/config/fastfetch/onmachine/config.jsonc ~/.onmachine/onmachine/onmachine/onmachine/config/fastfetch/
fi
