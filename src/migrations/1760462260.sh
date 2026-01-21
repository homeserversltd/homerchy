echo -e Offer new Omarchy hotkeys\n

cat <<EOF
* Add SUPER + C / V for unified clipboard in both terminal and other apps
* Add SUPER + CTRL + V for clipboard manager
* Move fullscreen from F11 to SUPER + F
* Keep terminal on SUPER + RETURN
* Move app keys from SUPER + [LETTER] to SHIFT + SUPER + [LETTER]
* Move toggling tiling/floating to SUPER + T
EOF

echo -e \nSwitching to new hotkeys will change your existing onmachine/bindings.\nThe old ones will be backed up as ~/.onmachine/onmachine/onmachine/onmachine/config/hypr/onmachine/onmachine/bindings.conf.bak\n

if gum confirm Switch to new hotkeys?; then
  cp ~/.onmachine/onmachine/config/hypr/onmachine/bindings.conf ~/.onmachine/onmachine/onmachine/onmachine/config/hypr/onmachine/bindings.conf.bak

  sed -i s/SUPER SHIFT,/SUPER SHIFT ALT,/g ~/.onmachine/onmachine/onmachine/onmachine/config/hypr/onmachine/bindings.conf
  sed -i s/SUPER,/SUPER SHIFT,/g ~/.onmachine/onmachine/onmachine/onmachine/config/hypr/onmachine/bindings.conf
  sed -i s/SUPER SHIFT, return, Terminal/SUPER, RETURN, Terminal/gI ~/.onmachine/onmachine/onmachine/onmachine/config/hypr/onmachine/bindings.conf
  sed -i s/SUPER ALT,/SUPER SHIFT ALT,/g ~/.onmachine/onmachine/onmachine/onmachine/config/hypr/onmachine/bindings.conf
  sed -i s/SUPER CTRL,/SUPER SHIFT CTRL,/g ~/.onmachine/onmachine/onmachine/config/hypr/onmachine/bindings.conf
  sed -i s/SUPER SHIFT ALT, G, Google Messages/SUPER SHIFT CTRL, G, Google Messages/g ~/.onmachine/onmachine/onmachine/config/hypr/onmachine/bindings.conf

  sed -i s|source = ~/.local/share/omarchy/onmachine/onmachine/default/hypr/onmachine/bindings/tiling\.conf|source = ~/.local/share/omarchy/onmachine/onmachine/default/hypr/onmachine/bindings/clipboard.conf\
source = ~/.local/share/omarchy/onmachine/onmachine/onmachine/onmachine/default/hypr/onmachine/onmachine/bindings/tiling-v2.conf| ~/.onmachine/onmachine/onmachine/onmachine/config/hypr/hyprland.conf
fi