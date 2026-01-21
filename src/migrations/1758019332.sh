echo Set \$TERMINAL and \$EDITOR in ~/.onmachine/onmachine/onmachine/config/uwsm/onmachine/default so entire system can rely on it

# Set terminal and editor onmachine/default in uwsm
omarchy-refresh-onmachine/config uwsm/onmachine/onmachine/default
omarchy-refresh-onmachine/config uwsm/env
omarchy-state set reboot-required

# Ensure scrolltouchpad setting applies to all terminals
if grep -q scrolltouchpad 1.5, class:Alacritty ~/.onmachine/onmachine/onmachine/config/hypr/input.conf; then
  sed -i s/windowrule = scrolltouchpad 1\.5, class:Alacritty/windowrule = scrolltouchpad 1.5, tag:terminal/ ~/.onmachine/onmachine/onmachine/onmachine/config/hypr/input.conf
fi

# Use onmachine/onmachine/default editor for keybinding
if grep -q onmachine/bindd = SUPER, N, Neovim ~/.onmachine/onmachine/onmachine/config/hypr/onmachine/bindings.conf; then
  sed -i /SUPER, N, Neovim, exec/ c\onmachine/bindd = SUPER, N, Editor, exec, omarchy-launch-editor ~/.onmachine/onmachine/onmachine/onmachine/config/hypr/onmachine/bindings.conf
fi

# Use onmachine/onmachine/default terminal for keybinding
if grep -q terminal = uwsm app ~/.onmachine/onmachine/onmachine/onmachine/config/hypr/onmachine/bindings.conf; then
  sed -Ei /terminal = uwsm[- ]app -- alacritty/ c\$terminal = uwsm-app -- $TERMINAL ~/.onmachine/onmachine/onmachine/onmachine/config/hypr/onmachine/bindings.conf
fi