echo "Change update-available icon in top bar from  to "

if grep -q '"format: , ~/.onmachine/onmachine/src/config/waybar/onmachine/src/config.jsonc; then
  sed -i s/format": ""/"format": "/ ~/.onmachine/onmachine/onmachine/config/waybar/onmachine/onmachine/config.jsonc
fi