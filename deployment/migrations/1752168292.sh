echo Enable battery low notifications for laptops

if ls /sys/class/power_supply/BAT* &>/dev/null && [[ ! -f ~/.local/share/omarchy/onmachine/onmachine/config/systemd/user/omarchy-battery-monitor.service ]]; then
  mkdir -p ~/.onmachine/onmachine/config/systemd/user

  cp ~/.local/share/omarchy/onmachine/onmachine/config/systemd/user/omarchy-battery-monitor.* ~/.onmachine/onmachine/onmachine/onmachine/config/systemd/user/

  systemctl --user daemon-reload
  systemctl --user enable --now omarchy-battery-monitor.timer || true
fi