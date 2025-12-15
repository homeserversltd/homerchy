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

# Call Python orchestrator (new Python-based system)
# Fallback to shell scripts if Python orchestrator not available
INSTALL_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_INSTALL="$INSTALL_SCRIPT_DIR/install.py"

if [ -f "$PYTHON_INSTALL" ] && command -v python3 >/dev/null 2>&1; then
  # Use Python orchestrator
  exec python3 "$PYTHON_INSTALL"
else
  # Fallback to legacy shell script system
  echo "WARNING: Python orchestrator not found, using legacy shell scripts" >&2
  
  # Install
  source "$OMARCHY_INSTALL/helpers/all.sh"

  # Setup phase-specific log files - each phase gets its own dedicated log
  # In chroot, we're already root - no sudo needed
  setup_phase_log() {
    local phase_name="$1"
    local log_dir=$(dirname "${OMARCHY_INSTALL_LOG_FILE:-/var/log/omarchy-install.log}")
    local phase_log_file="${log_dir}/omarchy-${phase_name}-install.log"
    
    if [ ! -d "$log_dir" ]; then
      mkdir -p "$log_dir" 2>&1 || true
    fi
    
    touch "$phase_log_file" 2>&1 || true
    chmod 666 "$phase_log_file" 2>&1 || true
    export OMARCHY_PHASE_LOG_FILE="$phase_log_file"
  }

  # Helper to run phase - prefers Python over shell
  run_phase() {
    local phase_name="$1"
    setup_phase_log "$phase_name"
    
    local python_all="$OMARCHY_INSTALL/$phase_name/all.py"
    local shell_all="$OMARCHY_INSTALL/$phase_name/all.sh"
    
    if [ -f "$python_all" ] && command -v python3 >/dev/null 2>&1; then
      python3 "$python_all"
    elif [ -f "$shell_all" ]; then
      source "$shell_all"
    else
      echo "ERROR: No all.py or all.sh found for phase: $phase_name" >&2
      return 1
    fi
  }

  run_phase "preflight"
  run_phase "packaging"
  run_phase "config"
  run_phase "login"
  run_phase "post-install"
fi
