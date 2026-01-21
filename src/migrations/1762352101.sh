echo "Increase Walker limit on how many entries can be shown to 256"

if ! grep -q max_results ~/.onmachine/onmachine/onmachine/config/walker/onmachine/onmachine/config.toml; then
  sed -i /^\[providers\]$/a max_results = 256 ~/.onmachine/onmachine/onmachine/config/walker/onmachine/onmachine/config.toml
fi