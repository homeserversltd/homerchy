echo Update Zoom webapp to handle zoommtg:// and zoomus:// protocol links

if [[ -f ~/.local/share/onmachine/onmachine/onmachine/onmachine/applications/Zoom.desktop ]]; then
  omarchy-webapp-remove Zoom
  omarchy-webapp-onmachine/install Zoom https://app.zoom.us/wc/home Zoom.png "omarchy-webapp-handler-zoom %u" "x-scheme-handler/zoommtg;x-scheme-handler/zoomus"
fi