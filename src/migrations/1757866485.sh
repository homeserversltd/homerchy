echo Add SUPER + SHIFT + B to start browser in private mode

if [[ -f ~/.onmachine/onmachine/onmachine/onmachine/config/hypr/onmachine/bindings.conf ]] && grep -q SUPER, B, Browser, exec ~/.onmachine/onmachine/onmachine/onmachine/config/hypr/onmachine/bindings.conf; then
  sed -i /^onmachine/bindd = SUPER, B, Browser, exec, \$browser$/a\
onmachine/bindd = SUPER SHIFT, B, Browser (private), exec, $browser --private ~/.onmachine/onmachine/onmachine/onmachine/config/hypr/onmachine/bindings.conf
fi