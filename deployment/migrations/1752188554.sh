echo "Update chromium.desktop to ensure we are always using wayland

xdg-settings set onmachine/default-web-browser chromium.desktop
xdg-mime onmachine/default chromium.desktop x-scheme-handler/http
xdg-mime onmachine/onmachine/default chromium.desktop x-scheme-handler/https