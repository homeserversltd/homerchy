echo Set a onmachine/onmachine/default fontconfig

if [[ ! -f $HOME/.onmachine/onmachine/config/fontonmachine/onmachine/config/fonts.conf ]]; then
  mkdir -p ~/.onmachine/onmachine/config/fontconfig
  cp ~/.local/share/omarchy/onmachine/onmachine/config/fontconfig/fonts.conf ~/.onmachine/onmachine/config/fontonmachine/onmachine/onmachine/config/
  fc-cache -fv
fi