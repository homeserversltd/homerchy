stop_install_log

echo_in_style() {
  echo "$1" | tte --canvas-width 0 --anchor-text c --frame-rate 640 print
}

clear
echo
tte -i ~/.local/share/omarchy/logo.txt --canvas-width 0 --anchor-text c --frame-rate 920 laseretch
echo

# Display installation time if available (check postinstall log first, then preinstall)
TOTAL_TIME=""
if [[ -f /var/log/omarchy-postinstall.log ]] && grep -q "Total:" /var/log/omarchy-postinstall.log 2>/dev/null; then
  TOTAL_TIME=$(tail -n 20 /var/log/omarchy-postinstall.log | grep "^Total:" | sed 's/^Total:[[:space:]]*//')
elif [[ -f /var/log/omarchy-preinstall.log ]] && grep -q "Total:" /var/log/omarchy-preinstall.log 2>/dev/null; then
  TOTAL_TIME=$(tail -n 20 /var/log/omarchy-preinstall.log | grep "^Total:" | sed 's/^Total:[[:space:]]*//')
fi

if [ -n "$TOTAL_TIME" ]; then
  echo
  echo_in_style "Installed in $TOTAL_TIME"
else
  echo_in_style "Finished installing"
fi

if sudo test -f /etc/sudoers.d/99-omarchy-installer; then
  sudo rm -f /etc/sudoers.d/99-omarchy-installer &>/dev/null
fi

# Exit gracefully if user chooses not to reboot
if gum confirm --padding "0 0 0 $((PADDING_LEFT + 32))" --show-help=false --default --affirmative "Reboot Now" --negative "" ""; then
  # Clear screen to hide any shutdown messages
  clear

  if [[ -n "${OMARCHY_CHROOT_INSTALL:-}" ]]; then
    touch /var/tmp/omarchy-install-completed
    exit 0
  else
    sudo reboot 2>/dev/null
  fi
fi
