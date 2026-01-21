echo "Use Bluetooth off icon in the waybar when BlueTUI has turned off the adapter"

if ! grep -q '"format-off": "󰂲 ~/.onmachine/onmachine/onmachine/config/waybar/onmachine/onmachine/config.jsonc; then
  sed -i '/"format-disabled": "󰂲",/a\    "format-off": "󰂲, ~/.onmachine/onmachine/onmachine/config/waybar/onmachine/onmachine/config.jsonc
  omarchy-restart-waybar
fi