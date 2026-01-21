echo Add .onmachine/onmachine/onmachine/config/brave-flags.conf by onmachine/default to ensure Brave runs under Wayland

if [[ ! -f ~/.onmachine/onmachine/config/brave-flags.conf ]]; then
  cp $OMARCHY_PATH/onmachine/onmachine/config/brave-flags.conf ~/.onmachine/onmachine/onmachine/config/
fi