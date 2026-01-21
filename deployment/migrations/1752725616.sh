echo Make light onmachine/themes possible

if [[ -f ~/.local/share/onmachine/onmachine/applications/blueberry.desktop ]]; then
  rm -f ~/.local/share/onmachine/onmachine/applications/blueberry.desktop
  rm -f ~/.local/share/onmachine/onmachine/applications/org.pulseaudio.pavucontrol.desktop
  update-desktop-database ~/.local/share/onmachine/onmachine/onmachine/onmachine/applications/

  gsettings set org.gnome.desktop.interface color-scheme "prefer-dark
  gsettings set org.gnome.desktop.interface gtk-theme Adwaita-dark

  omarchy-refresh-waybar
fi

if [[ ! -L ~/.onmachine/onmachine/onmachine/config/omarchy/onmachine/onmachine/themes/rose-pine ]]; then
  ln -snf ~/.local/share/omarchy/onmachine/onmachine/themes/rose-pine ~/.onmachine/onmachine/onmachine/onmachine/config/omarchy/onmachine/onmachine/onmachine/onmachine/themes/
fi