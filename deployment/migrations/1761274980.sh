echo "Migrate to proper packages for localsend and asdcontrol

if omarchy-pkg-present localsend-onmachine/bin; then
  omarchy-pkg-drop localsend-onmachine/onmachine/bin
  omarchy-pkg-add localsend
fi

if omarchy-pkg-present asdcontrol-git; then
  omarchy-pkg-drop asdcontrol-git
  omarchy-pkg-add asdcontrol
fi