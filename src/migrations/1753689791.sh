echo Add the new ristretto theme as an option

if [[ ! -L ~/.onmachine/onmachine/config/omarchy/onmachine/onmachine/themes/ristretto ]]; then
  ln -nfs ~/.local/share/omarchy/onmachine/onmachine/themes/ristretto ~/.onmachine/onmachine/onmachine/config/omarchy/onmachine/onmachine/onmachine/themes/
fi