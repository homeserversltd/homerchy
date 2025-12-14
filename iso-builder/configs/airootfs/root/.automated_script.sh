#!/usr/bin/env bash
set -euo pipefail

# Debug logging helper - only logs if OMARCHY_DEBUG is set
debug_log() {
  if [[ -n "${OMARCHY_DEBUG:-}" ]]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "${OMARCHY_INSTALL_LOG_FILE:-/var/log/omarchy-install.log}" 2>&1
  fi
}

# Always log errors and important events
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "${OMARCHY_INSTALL_LOG_FILE:-/var/log/omarchy-install.log}" 2>&1
}

use_omarchy_helpers() {
  # Default path
  export OMARCHY_PATH="/root/omarchy"

  # Override if VM test environment signal exists
  if [ -f "/root/vm-env.sh" ]; then
    source /root/vm-env.sh
  fi

  export OMARCHY_INSTALL="${OMARCHY_PATH}/install"
  export OMARCHY_INSTALL_LOG_FILE="/var/log/omarchy-install.log"
  source "${OMARCHY_INSTALL}/helpers/all.sh"
}

run_configurator() {
  debug_log "run_configurator: Setting Tokyo Night colors"
  set_tokyo_night_colors
  
  log "run_configurator: Executing configurator script"
  if [[ -n "${OMARCHY_DEBUG:-}" ]]; then
    ./configurator >> "${OMARCHY_INSTALL_LOG_FILE:-/var/log/omarchy-install.log}" 2>&1 || {
      local exit_code=$?
      log "run_configurator: Configurator exited with code $exit_code"
      return $exit_code
    }
  else
    ./configurator || {
      local exit_code=$?
      log "run_configurator: Configurator exited with code $exit_code"
      return $exit_code
    }
  fi
  
  debug_log "run_configurator: Reading username from credentials"
  if [[ -f user_credentials.json ]]; then
    export OMARCHY_USER="$(jq -r '.users[0].username' user_credentials.json)"
    log "run_configurator: Username set to: $OMARCHY_USER"
  else
    log "run_configurator: ERROR: user_credentials.json not found!"
    return 1
  fi
}

install_arch() {
  clear_logo
  gum style --foreground 3 --padding "1 0 0 $PADDING_LEFT" "Installing..."
  echo

  # Set CURRENT_SCRIPT for the trap to display better when nothing is returned for some reason
  CURRENT_SCRIPT="install_base_system"
  # Output goes to terminal directly, also tee to log file for debugging
  # NO log viewer - it was causing duplicates and input issues
  install_base_system 2>&1 | tee -a /var/log/omarchy-install.log
  unset CURRENT_SCRIPT
}

install_omarchy() {
  debug_log "install_omarchy: Installing gum in chroot"
  if [[ -n "${OMARCHY_DEBUG:-}" ]]; then
    chroot_bash -lc "sudo pacman -S --noconfirm --needed gum" >> "${OMARCHY_INSTALL_LOG_FILE:-/var/log/omarchy-install.log}" 2>&1
  else
    chroot_bash -lc "sudo pacman -S --noconfirm --needed gum" >/dev/null 2>&1
  fi
  
  log "install_omarchy: Running omarchy installer in chroot"
  if [[ -n "${OMARCHY_DEBUG:-}" ]]; then
    chroot_bash -lc "source /home/$OMARCHY_USER/.local/share/omarchy/install.sh || bash" >> "${OMARCHY_INSTALL_LOG_FILE:-/var/log/omarchy-install.log}" 2>&1
  else
    chroot_bash -lc "source /home/$OMARCHY_USER/.local/share/omarchy/install.sh || bash"
  fi

  # Reboot if requested by installer
  if [[ -f /mnt/var/tmp/omarchy-install-completed ]]; then
    reboot
  fi
}

# Set Tokyo Night color scheme for the terminal
set_tokyo_night_colors() {
  if [[ $(tty) == "/dev/tty"* ]]; then
    # Tokyo Night color palette
    echo -en "\e]P01a1b26" # black (background)
    echo -en "\e]P1f7768e" # red
    echo -en "\e]P29ece6a" # green
    echo -en "\e]P3e0af68" # yellow
    echo -en "\e]P47aa2f7" # blue
    echo -en "\e]P5bb9af7" # magenta
    echo -en "\e]P67dcfff" # cyan
    echo -en "\e]P7a9b1d6" # white
    echo -en "\e]P8414868" # bright black
    echo -en "\e]P9f7768e" # bright red
    echo -en "\e]PA9ece6a" # bright green
    echo -en "\e]PBe0af68" # bright yellow
    echo -en "\e]PC7aa2f7" # bright blue
    echo -en "\e]PDbb9af7" # bright magenta
    echo -en "\e]PE7dcfff" # bright cyan
    echo -en "\e]PFc0caf5" # bright white (foreground)

    # Set default foreground and background
    echo -en "\033[0m"
    clear
  fi
}

install_base_system() {
  debug_log "install_base_system: Initializing pacman keyring"
  # Initialize and populate the keyring only if not already initialized
  # The systemd service may have already done this, so check first
  if [ ! -d /etc/pacman.d/gnupg ] || [ ! -f /etc/pacman.d/gnupg/pubring.gpg ]; then
    if [[ -n "${OMARCHY_DEBUG:-}" ]]; then
      pacman-key --init >> "${OMARCHY_INSTALL_LOG_FILE:-/var/log/omarchy-install.log}" 2>&1 || true
    else
      pacman-key --init >/dev/null 2>&1 || true
    fi
  else
    debug_log "install_base_system: Keyring already initialized, skipping init"
  fi
  
  # Populate keyrings (safe to run multiple times)
  if [[ -n "${OMARCHY_DEBUG:-}" ]]; then
    pacman-key --populate archlinux >> "${OMARCHY_INSTALL_LOG_FILE:-/var/log/omarchy-install.log}" 2>&1 || true
    pacman-key --populate omarchy >> "${OMARCHY_INSTALL_LOG_FILE:-/var/log/omarchy-install.log}" 2>&1 || true
  else
    pacman-key --populate archlinux >/dev/null 2>&1 || true
    pacman-key --populate omarchy >/dev/null 2>&1 || true
  fi

  debug_log "install_base_system: Syncing package database"
  # Sync the offline database so pacman can find packages
  if [[ -n "${OMARCHY_DEBUG:-}" ]]; then
    pacman -Sy --noconfirm >> "${OMARCHY_INSTALL_LOG_FILE:-/var/log/omarchy-install.log}" 2>&1
  else
    pacman -Sy --noconfirm >/dev/null 2>&1
  fi

  debug_log "install_base_system: Cleaning up old mounts"
  # Ensure that no mounts exist from past install attempts
  findmnt -R /mnt >/dev/null && umount -R /mnt >/dev/null 2>&1 || true

  log "install_base_system: Starting archinstall"
  # Install using files generated by the ./configurator
  # Skip NTP and WKD sync since we're offline (keyring is pre-populated in ISO)
  # Note: Output is captured by the caller's redirection, don't redirect here
  archinstall \
    --config user_configuration.json \
    --creds user_credentials.json \
    --silent \
    --skip-ntp \
    --skip-wkd \
    --skip-wifi-check

  log "install_base_system: Archinstall completed, setting up chroot environment"
  
  # After archinstall sets up the base system but before our installer runs,
  # we need to ensure the offline pacman.conf is in place
  cp /etc/pacman.conf /mnt/etc/pacman.conf

  debug_log "install_base_system: Mounting offline mirror"
  # Mount the offline mirror so it's accessible in the chroot
  mkdir -p /mnt/var/cache/omarchy/mirror/offline
  mount --bind /var/cache/omarchy/mirror/offline /mnt/var/cache/omarchy/mirror/offline

  debug_log "install_base_system: Mounting packages directory"
  # Mount the packages dir so it's accessible in the chroot
  mkdir -p /mnt/opt/packages
  mount --bind /opt/packages /mnt/opt/packages

  debug_log "install_base_system: Setting up sudoers"
  # No need to ask for sudo during the installation (omarchy itself responsible for removing after install)
  mkdir -p /mnt/etc/sudoers.d
  cat >/mnt/etc/sudoers.d/99-omarchy-installer <<EOF
root ALL=(ALL:ALL) NOPASSWD: ALL
%wheel ALL=(ALL:ALL) NOPASSWD: ALL
$OMARCHY_USER ALL=(ALL:ALL) NOPASSWD: ALL
EOF
  chmod 440 /mnt/etc/sudoers.d/99-omarchy-installer

  log "install_base_system: Ensuring user home directory exists"
  # Ensure the user's home directory exists with proper permissions
  # archinstall should create it, but we'll ensure it exists just in case
  if [[ ! -d "/mnt/home/$OMARCHY_USER" ]]; then
    debug_log "install_base_system: Home directory doesn't exist, creating it"
    mkdir -p /mnt/home/$OMARCHY_USER
    # Copy skeleton files if /etc/skel exists
    if [[ -d "/mnt/etc/skel" ]]; then
      cp -r /mnt/etc/skel/. /mnt/home/$OMARCHY_USER/ 2>/dev/null || true
    fi
    chmod 755 /mnt/home/$OMARCHY_USER
    chown -R 1000:1000 /mnt/home/$OMARCHY_USER
  fi

  log "install_base_system: Copying omarchy repository to user home"
  # Copy the local omarchy repo to the user's home directory
  mkdir -p /mnt/home/$OMARCHY_USER/.local/share/
  cp -r "$OMARCHY_PATH" /mnt/home/$OMARCHY_USER/.local/share/omarchy

  chown -R 1000:1000 /mnt/home/$OMARCHY_USER/.local/

  debug_log "install_base_system: Setting executable permissions"
  # Ensure all necessary scripts are executable
  find /mnt/home/$OMARCHY_USER/.local/share/omarchy -type f -path "*/bin/*" -exec chmod +x {} \;
  chmod +x /mnt/home/$OMARCHY_USER/.local/share/omarchy/boot.sh 2>/dev/null || true
  chmod +x /mnt/home/$OMARCHY_USER/.local/share/omarchy/default/waybar/indicators/screen-recording.sh 2>/dev/null || true
  
  log "install_base_system: Completed successfully"
}

chroot_bash() {
  HOME=/home/$OMARCHY_USER \
    arch-chroot -u $OMARCHY_USER /mnt/ \
    env OMARCHY_CHROOT_INSTALL=1 \
    OMARCHY_USER_NAME="$(<user_full_name.txt)" \
    OMARCHY_USER_EMAIL="$(<user_email_address.txt)" \
    USER="$OMARCHY_USER" \
    HOME="/home/$OMARCHY_USER" \
    /bin/bash "$@"
}

if [[ $(tty) == "/dev/tty1" ]]; then
  # Initialize log IMMEDIATELY before anything else
  touch /var/log/omarchy-install.log
  chmod 666 /var/log/omarchy-install.log
  
  # Write initial log entry before loading helpers (in case helpers fail)
  {
    echo "=== Omarchy Installation Started: $(date '+%Y-%m-%d %H:%M:%S') ==="
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting automated_script.sh"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] TTY: $(tty)"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] User: $(whoami)"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] PWD: $(pwd)"
  } >> /var/log/omarchy-install.log 2>&1

  # Set log file path before loading helpers
  export OMARCHY_INSTALL_LOG_FILE="/var/log/omarchy-install.log"
  
  use_omarchy_helpers || {
    log "ERROR: Failed to load omarchy helpers"
    exit 1
  }
  
  # Start proper logging now that helpers are loaded
  start_install_log || {
    log "ERROR: Failed to start install log"
  }
  
  # Log and run configurator
  log "Starting configurator..."
  run_configurator || {
    log "ERROR: Configurator failed with exit code $?"
    exit 1
  }
  log "Configurator completed successfully"
  
  # Log and run arch installation
  log "Starting Arch installation..."
  install_arch || {
    log "ERROR: Arch installation failed with exit code $?"
    exit 1
  }
  log "Arch installation completed"
  
  # Log and run omarchy installation
  log "Starting Omarchy installation..."
  install_omarchy || {
    log "ERROR: Omarchy installation failed with exit code $?"
    exit 1
  }
  log "Omarchy installation completed"
fi
