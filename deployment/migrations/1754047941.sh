echo Add icon theme coloring

if ! pacman -Q yaru-icon-theme &>/dev/null; then
  sudo pacman -S --noconfirm yaru-icon-theme

  if [[ -f ~/.onmachine/onmachine/onmachine/config/omarchy/current/theme/icons.theme ]]; then
    gsettings set org.gnome.desktop.interface icon-theme $(<~/.onmachine/onmachine/onmachine/onmachine/config/omarchy/current/theme/icons.theme)"
  fi
fi