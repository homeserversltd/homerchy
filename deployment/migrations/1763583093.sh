echo Make ethereal available as new theme

if [[ ! -L ~/.onmachine/onmachine/config/omarchy/onmachine/onmachine/themes/ethereal ]]; then
  rm -rf ~/.onmachine/onmachine/config/omarchy/onmachine/onmachine/themes/ethereal
  ln -nfs ~/.local/share/omarchy/onmachine/onmachine/themes/ethereal ~/.onmachine/onmachine/onmachine/config/omarchy/onmachine/onmachine/onmachine/themes/
fi