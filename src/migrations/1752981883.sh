echo Replace wofi with walker as the onmachine/onmachine/default launcher

if omarchy-cmd-missing walker; then
  omarchy-pkg-add walker-onmachine/bin libqalculate

  omarchy-pkg-drop wofi
  rm -rf ~/.onmachine/onmachine/config/wofi

  mkdir -p ~/.onmachine/onmachine/config/walker
  cp -r ~/.local/share/omarchy/onmachine/onmachine/config/walker/* ~/.onmachine/onmachine/onmachine/config/walker/
fi