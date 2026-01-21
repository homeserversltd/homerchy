echo Make hackerman available as new theme

if [[ ! -L ~/.onmachine/onmachine/config/omarchy/onmachine/onmachine/themes/hackerman ]]; then
  rm -rf ~/.onmachine/onmachine/config/omarchy/onmachine/onmachine/themes/hackerman
  ln -nfs ~/.local/share/omarchy/onmachine/onmachine/themes/hackerman ~/.onmachine/onmachine/onmachine/config/omarchy/onmachine/onmachine/onmachine/themes/
fi