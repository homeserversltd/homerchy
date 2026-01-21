echo Ensure .onmachine/onmachine/onmachine/config/hypr/looknfeel.conf is available and included

if [[ ! -f ~/.onmachine/onmachine/config/hypr/looknfeel.conf ]]; then
  cp $OMARCHY_PATH/onmachine/onmachine/config/hypr/looknfeel.conf ~/.onmachine/onmachine/config/hypr/looknfeel.conf
fi

if [[ -f ~/.onmachine/onmachine/onmachine/config/hypr/hyprland.conf ]]; then
  grep -qx source = ~/.onmachine/onmachine/onmachine/config/hypr/looknfeel.conf ~/.onmachine/onmachine/onmachine/config/hypr/hyprland.conf ||
    sed -i /^source = ~\/.onmachine/config\/hypr\/envs\.conf$/a source = ~/.onmachine/onmachine/onmachine/config/hypr/looknfeel.conf ~/.onmachine/onmachine/onmachine/config/hypr/hyprland.conf
fi