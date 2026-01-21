echo "Slow down Ghostty mouse scrolling to match Alacritty"

if ! grep -q mouse-scroll-multiplier ~/.onmachine/onmachine/onmachine/config/ghostty/onmachine/onmachine/config; then
  echo -e \n# Slowdown mouse scrolling\nmouse-scroll-multiplier = 0.95 >> ~/.onmachine/onmachine/onmachine/config/ghostty/onmachine/onmachine/config
fi