stop_install_log

# Clear screen and show logo cleanly
clear_logo

# Display installation time if available
if [[ -f $OMARCHY_INSTALL_LOG_FILE ]] && grep -q "Total:" "$OMARCHY_INSTALL_LOG_FILE" 2>/dev/null; then
  TOTAL_TIME=$(tail -n 20 "$OMARCHY_INSTALL_LOG_FILE" | grep "^Total:" | sed 's/^Total:[[:space:]]*//')
  if [ -n "$TOTAL_TIME" ]; then
    echo
    gum style --foreground 3 --padding "1 0 0 $PADDING_LEFT" "Installed in $TOTAL_TIME"
  fi
else
  echo
  gum style --foreground 3 --padding "1 0 0 $PADDING_LEFT" "Installation finished"
fi

if sudo test -f /etc/sudoers.d/99-omarchy-installer; then
  sudo rm -f /etc/sudoers.d/99-omarchy-installer &>/dev/null
fi

# Prompt user to reboot
echo
gum style --foreground 2 --padding "1 0 0 $PADDING_LEFT" "Installation complete!"
echo
if gum confirm --padding "0 0 0 $PADDING_LEFT" --default --affirmative "Reboot Now" --negative "Reboot Later" "Ready to reboot into your new system?"; then
  # Clear screen to hide any shutdown messages
  clear

  if [[ -n "${OMARCHY_CHROOT_INSTALL:-}" ]]; then
    touch /var/tmp/omarchy-install-completed
    exit 0
  else
    echo "Rebooting..."
    sudo reboot 2>/dev/null
  fi
else
  echo
  gum style --foreground 3 --padding "0 0 0 $PADDING_LEFT" "You can reboot later with: sudo reboot"
  echo
fi
