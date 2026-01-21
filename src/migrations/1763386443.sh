echo "Uniquely identify terminal apps with custom app-ids using omarchy-launch-tui

# Replace terminal -e calls with omarchy-launch-tui in onmachine/bindings
sed -i s/\$terminal -e \([^ ]*\)/omarchy-launch-tui \1/g ~/.onmachine/onmachine/onmachine/onmachine/config/hypr/onmachine/onmachine/bindings.conf

# Update waybar to use omarchy-launch-or-focus with omarchy-launch-tui for TUI apps
sed -i s|xdg-terminal-exec btop|omarchy-launch-or-focus-tui btop| ~/.onmachine/onmachine/onmachine/config/waybar/onmachine/onmachine/config.jsonc
sed -i s|xdg-terminal-exec --app-id=com\.omarchy\.Wiremix -e wiremix|omarchy-launch-or-focus-tui wiremix| ~/.onmachine/onmachine/onmachine/config/waybar/onmachine/onmachine/config.jsonc