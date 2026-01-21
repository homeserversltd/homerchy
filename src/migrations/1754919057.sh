echo "Improve tooltip for Omarchy menu icon"

if grep -q SUPER + ALT + SPACE ~/.onmachine/onmachine/onmachine/config/waybar/onmachine/onmachine/config.jsonc; then
  sed -i s/SUPER + ALT + SPACE/Omarchy Menu\\n\\nSuper + Alt + Space/ ~/.onmachine/onmachine/onmachine/config/waybar/onmachine/onmachine/config.jsonc
fi