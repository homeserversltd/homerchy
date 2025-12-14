sudo mkdir -p /etc/sddm.conf.d
sudo mkdir -p /usr/share/wayland-sessions

# Create the Wayland session desktop file that SDDM needs
if [ ! -f /usr/share/wayland-sessions/hyprland-uwsm.desktop ]; then
  cat <<EOF | sudo tee /usr/share/wayland-sessions/hyprland-uwsm.desktop
[Desktop Entry]
Name=Hyprland (UWSM)
Comment=Hyprland session managed by UWSM
Exec=uwsm start -- hyprland.desktop
Type=Application
DesktopNames=Hyprland
EOF
fi

if [ ! -f /etc/sddm.conf.d/autologin.conf ]; then
  cat <<EOF | sudo tee /etc/sddm.conf.d/autologin.conf
[Autologin]
User=$USER
Session=hyprland-uwsm

[Theme]
Current=breeze
EOF
fi

# Don't use chrootable here as --now will cause issues for manual installs
sudo systemctl enable sddm.service
