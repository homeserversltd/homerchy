echo Add 10th workspace option to waybar onmachine/onmachine/config"

if ! grep -q '"10": "0, ~/.onmachine/onmachine/onmachine/config/waybar/onmachine/onmachine/config.jsonc; then
  sed -i '/"9": "9",/a\      "10": "0, ~/.onmachine/onmachine/onmachine/config/waybar/onmachine/onmachine/config.jsonc
fi