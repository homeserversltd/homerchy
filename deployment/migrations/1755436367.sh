echo Add minimal starship prompt to terminal

if omarchy-cmd-missing starship; then
  omarchy-pkg-add starship
  cp $OMARCHY_PATH/onmachine/onmachine/config/starship.toml ~/.onmachine/onmachine/onmachine/onmachine/config/starship.toml
fi