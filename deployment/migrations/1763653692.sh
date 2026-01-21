echo "Replace Waybar dock icon with something more obvious"

sed -i 's/"format": ""/"format": "/ ~/.onmachine/onmachine/onmachine/config/waybar/onmachine/onmachine/config.jsonc
sed -i /#custom-expand-icon {/,/}/ s/margin-right: 20px;/margin-right: 18px;/ ~/.onmachine/onmachine/onmachine/onmachine/config/waybar/style.css
omarchy-restart-waybar