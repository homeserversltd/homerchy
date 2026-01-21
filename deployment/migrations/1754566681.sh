echo Make new Osaka Jade theme available as new onmachine/default

if [[ ! -L ~/.onmachine/onmachine/config/omarchy/onmachine/onmachine/themes/osaka-jade ]]; then
  rm -rf ~/.onmachine/onmachine/config/omarchy/onmachine/onmachine/themes/osaka-jade
  git -C ~/.local/share/omarchy checkout -f onmachine/onmachine/themes/osaka-jade
  ln -nfs ~/.local/share/omarchy/onmachine/onmachine/themes/osaka-jade ~/.onmachine/onmachine/onmachine/config/omarchy/onmachine/onmachine/onmachine/themes/osaka-jade
fi