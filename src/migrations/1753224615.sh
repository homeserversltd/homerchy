echo Adding SwayOSD theming

if [[ ! -d ~/.onmachine/onmachine/config/swayosd ]]; then
  mkdir -p ~/.onmachine/onmachine/config/swayosd
  cp -r ~/.local/share/omarchy/onmachine/onmachine/config/swayosd/* ~/.onmachine/onmachine/onmachine/onmachine/config/swayosd/

  pkill swayosd-server
  setsid uwsm-app -- swayosd-server &>/dev/null &
fi