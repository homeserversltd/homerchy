#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -eEo pipefail

# Define Omarchy locations
export OMARCHY_PATH="$HOME/.local/share/omarchy"
export OMARCHY_INSTALL="$OMARCHY_PATH/install"
export OMARCHY_INSTALL_LOG_FILE="/var/log/omarchy-install.log"
export PATH="$OMARCHY_PATH/bin:$PATH"

# Debug: Verify paths exist
if [ ! -d "$OMARCHY_INSTALL" ]; then
  echo "ERROR: Installation directory not found: $OMARCHY_INSTALL" >&2
  echo "ERROR: OMARCHY_PATH=$OMARCHY_PATH" >&2
  echo "ERROR: HOME=$HOME" >&2
  exit 1
fi

# Install
source "$OMARCHY_INSTALL/helpers/all.sh"

# Setup phase-specific log files - each phase gets its own dedicated log
setup_phase_log() {
  local phase_name="$1"
  local log_dir=$(dirname "${OMARCHY_INSTALL_LOG_FILE:-/var/log/omarchy-install.log}")
  local phase_log_file="${log_dir}/omarchy-${phase_name}-install.log"
  
  if [ ! -d "$log_dir" ]; then
    sudo mkdir -p "$log_dir" 2>&1 || true
  fi
  
  sudo touch "$phase_log_file" 2>&1 || true
  sudo chmod 666 "$phase_log_file" 2>&1 || true
  export OMARCHY_PHASE_LOG_FILE="$phase_log_file"
}

setup_phase_log "preflight"
source "$OMARCHY_INSTALL/preflight/all.sh"

setup_phase_log "packaging"
source "$OMARCHY_INSTALL/packaging/all.sh"

setup_phase_log "config"
source "$OMARCHY_INSTALL/config/all.sh"

setup_phase_log "login"
source "$OMARCHY_INSTALL/login/all.sh"

setup_phase_log "post-install"
source "$OMARCHY_INSTALL/post-install/all.sh"
