#!/bin/bash
# Enable and start SSH service for VM access (only in VM environments)
# This script logs EVERYTHING to a separate detailed log file for debugging
# Normal output goes to stdout (captured by run_logged), detailed logs go to SSH_LOG_FILE

# Use phase log file if set, otherwise create script-specific log file
# Phase log is set up by install.sh before sourcing post-install/all.sh
if [ -n "${OMARCHY_PHASE_LOG_FILE:-}" ]; then
  SSH_LOG_FILE="$OMARCHY_PHASE_LOG_FILE"
else
  # Fallback: create script-specific log file
  LOG_DIR=$(dirname "${OMARCHY_INSTALL_LOG_FILE:-/var/log/omarchy-install.log}")
  SSH_LOG_FILE="${LOG_DIR}/omarchy-ssh-install.log"
  
  # In chroot, we're already root - no sudo needed
  if [ ! -d "$LOG_DIR" ]; then
    mkdir -p "$LOG_DIR" 2>&1 || true
  fi
  
  touch "$SSH_LOG_FILE" 2>&1 || true
  chmod 666 "$SSH_LOG_FILE" 2>&1 || true
fi

TIMESTAMP() { date '+%Y-%m-%d %H:%M:%S'; }

# NOW define LOG functions (file exists, so they can write to it)
LOG() {
  local msg="[$(TIMESTAMP)] post-install/ssh.sh: $*"
  # Write ONLY to the separate ssh log file
  echo "$msg" >> "$SSH_LOG_FILE" 2>&1 || true
  # Also output to stdout so it's visible in main log (via run_logged)
  echo "$msg"
}
LOG_ERROR() {
  local msg="[$(TIMESTAMP)] post-install/ssh.sh: ERROR: $*"
  # Write ONLY to the separate ssh log file
  echo "$msg" >> "$SSH_LOG_FILE" 2>&1 || true
  # Also output to stderr so it's visible
  echo "$msg" >&2
}

# NOW safe to call LOG() - file exists
LOG "=== SSH.SH STARTED ==="
LOG "Detailed log file: $SSH_LOG_FILE"
LOG "Main install log: ${OMARCHY_INSTALL_LOG_FILE:-/var/log/omarchy-install.log}"
LOG "OMARCHY_VM_TEST: ${OMARCHY_VM_TEST:-NOT SET}"
LOG "Current directory: $(pwd)"
LOG "User: $(whoami)"
LOG "SSH log file created successfully"

# Check if we're in a VM by checking for VM test environment signal
LOG "Checking if running in VM..."
LOG "OMARCHY_VM_TEST: ${OMARCHY_VM_TEST:-not set}"
LOG "/root/vm-env.sh exists: $([ -f "/root/vm-env.sh" ] && echo 'YES' || echo 'NO')"

if [[ -z "${OMARCHY_VM_TEST:-}" ]] && [[ ! -f "/root/vm-env.sh" ]]; then
  # Also check systemd-detect-virt as fallback
  if command -v systemd-detect-virt &>/dev/null; then
    VIRT_TYPE=$(systemd-detect-virt 2>/dev/null || echo "none")
    LOG "systemd-detect-virt result: $VIRT_TYPE"
    if [[ "$VIRT_TYPE" == "none" ]]; then
      LOG "Not in VM, skipping SSH enablement"
      return 0
    fi
  else
    LOG "systemd-detect-virt not available, assuming not in VM"
    LOG "Not in VM, skipping SSH enablement"
    return 0
  fi
fi

LOG "VM environment detected, proceeding with SSH setup"

# Check which SSH service exists
LOG "Checking for SSH service..."
if systemctl list-unit-files | grep -q "^ssh\.service"; then
  SSH_SERVICE="ssh.service"
  LOG "Found ssh.service (Arch Linux standard)"
elif systemctl list-unit-files | grep -q "^sshd\.service"; then
  SSH_SERVICE="sshd.service"
  LOG "Found sshd.service (non-standard)"
else
  LOG_ERROR "No SSH service found (neither ssh.service nor sshd.service)"
  LOG_ERROR "Available services:"
  systemctl list-unit-files | grep -i ssh | while IFS= read -r line; do
    LOG_ERROR "  $line"
  done
  return 1
fi

LOG "Using SSH service: $SSH_SERVICE"

# Enable SSH service to start on boot
LOG "Enabling $SSH_SERVICE to start on boot..."
enable_output=$(sudo systemctl enable "$SSH_SERVICE" 2>&1)
enable_exit=$?
if [ $enable_exit -eq 0 ]; then
  LOG "SSH service enabled successfully"
else
  LOG_ERROR "Failed to enable SSH service (exit code: $enable_exit)"
  LOG_ERROR "Enable output: $enable_output"
  # Continue anyway - might be in chroot where enable doesn't work
fi

# Start SSH service immediately
LOG "Starting $SSH_SERVICE..."
start_output=$(sudo systemctl start "$SSH_SERVICE" 2>&1)
start_exit=$?
if [ $start_exit -eq 0 ]; then
  LOG "SSH service started successfully"
else
  LOG_ERROR "Failed to start SSH service (exit code: $start_exit)"
  LOG_ERROR "Start output: $start_output"
  # Check if we're in chroot (start command ignored)
  if echo "$start_output" | grep -q "Running in chroot"; then
    LOG "Running in chroot - start command ignored (expected)"
  fi
fi

# Verify service status
LOG "Checking SSH service status..."
status_output=$(sudo systemctl status "$SSH_SERVICE" --no-pager 2>&1 || true)
echo "$status_output" | while IFS= read -r line; do
  echo "[$(TIMESTAMP)] post-install/ssh.sh: STATUS: $line" >> "$SSH_LOG_FILE" 2>&1 || true
done

LOG "=== SSH.SH COMPLETED ==="
LOG "SSH service: $SSH_SERVICE"
LOG "SSH available at: ssh -p 2222 owner@localhost (password: from settings.json)"

