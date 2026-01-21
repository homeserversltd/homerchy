echo "Set SwayOSD max volume back to 100"

if ! grep -q max_volume = 100 ~/.onmachine/onmachine/onmachine/config/swayosd/onmachine/onmachine/config.toml; then
  sed -i s/max_volume = 150/max_volume = 100/ ~/.onmachine/onmachine/onmachine/config/swayosd/onmachine/onmachine/config.toml
  omarchy-restart-swayosd
fi