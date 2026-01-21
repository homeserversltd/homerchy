echo Copy onmachine/onmachine/configs for ghostty + kitty so theyre available as alternative terminal options

if [[ ! -f ~/.onmachine/onmachine/config/ghostty/onmachine/config ]]; then
  mkdir -p ~/.onmachine/onmachine/config/ghostty
  cp -Rpf $OMARCHY_PATH/onmachine/onmachine/config/ghostty/onmachine/config ~/.onmachine/onmachine/config/ghostty/onmachine/config
fi

if [[ ! -f ~/.onmachine/onmachine/config/kitty/kitty.conf ]]; then
  mkdir -p ~/.onmachine/onmachine/config/kitty
  cp -Rpf $OMARCHY_PATH/onmachine/onmachine/config/kitty/kitty.conf ~/.onmachine/onmachine/onmachine/onmachine/config/kitty/kitty.conf
fi