#!/bin/bash
# Enable and start SSH service for VM access (only in VM environments)

# Check if we're in a VM by checking for VM test environment signal
if [[ -z "${OMARCHY_VM_TEST:-}" ]] && [[ ! -f "/root/vm-env.sh" ]]; then
  # Also check systemd-detect-virt as fallback
  if command -v systemd-detect-virt &>/dev/null; then
    VIRT_TYPE=$(systemd-detect-virt 2>/dev/null || echo "none")
    if [[ "$VIRT_TYPE" == "none" ]]; then
      echo "[$(date '+%Y-%m-%d %H:%M:%S')] Not in VM, skipping SSH enablement"
      return 0
    fi
  else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Not in VM, skipping SSH enablement"
    return 0
  fi
fi

# Enable SSH service to start on boot
sudo systemctl enable sshd

# Start SSH service immediately
sudo systemctl start sshd

echo "[$(date '+%Y-%m-%d %H:%M:%S')] SSH service enabled and started"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] SSH available at: ssh -p 2222 owner@localhost (password: from settings.json)"
