#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -eEo pipefail

# Define Omarchy locations - try multiple possible locations
# 1. User's home directory (normal installation)
# 2. /root/omarchy (ISO build location)
# 3. Script's parent directory (if run from repo)
OMARCHY_PATH=""
OMARCHY_INSTALL=""

# Try user's home directory first
if [ -d "$HOME/.local/share/omarchy/install" ]; then
  OMARCHY_PATH="$HOME/.local/share/omarchy"
  OMARCHY_INSTALL="$OMARCHY_PATH/install"
# Try /root/omarchy (ISO location)
elif [ -d "/root/omarchy/install" ]; then
  OMARCHY_PATH="/root/omarchy"
  OMARCHY_INSTALL="$OMARCHY_PATH/install"
# Try script's parent directory (if run from repo)
elif [ -d "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/install" ]; then
  OMARCHY_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  OMARCHY_INSTALL="$OMARCHY_PATH/install"
fi

# If still not found, error out
if [ -z "$OMARCHY_INSTALL" ] || [ ! -d "$OMARCHY_INSTALL" ]; then
  echo "ERROR: Installation directory not found!" >&2
  echo "ERROR: Tried:" >&2
  echo "ERROR:   $HOME/.local/share/omarchy/install" >&2
  echo "ERROR:   /root/omarchy/install" >&2
  echo "ERROR:   $(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/install" >&2
  echo "ERROR: HOME=$HOME" >&2
  exit 1
fi

export OMARCHY_PATH
export OMARCHY_INSTALL
export OMARCHY_INSTALL_LOG_FILE="/var/log/omarchy-install.log"
export PATH="$OMARCHY_PATH/bin:$PATH"

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
  setup_phase_log() {
    local phase_name="$1"
    local log_dir=$(dirname "${OMARCHY_INSTALL_LOG_FILE:-/var/log/omarchy-install.log}")
    local phase_log_file="${log_dir}/omarchy-${phase_name}-install.log"
    
    # Check if we're root
    if [ "$(id -u)" -eq 0 ]; then
      # We're root - can create files directly
      if [ ! -d "$log_dir" ]; then
        mkdir -p "$log_dir" 2>&1 || true
      fi
      touch "$phase_log_file" 2>&1 || true
      chmod 666 "$phase_log_file" 2>&1 || true
    else
      # Not root - try with sudo, or fall back to user-writable location
      if [ ! -d "$log_dir" ]; then
        sudo mkdir -p "$log_dir" 2>&1 || {
          # sudo failed - use user-writable location
          log_dir="$HOME/.local/share/omarchy/logs"
          phase_log_file="${log_dir}/omarchy-${phase_name}-install.log"
          mkdir -p "$log_dir" 2>&1 || true
        }
      fi
      
      # Try to create log file with sudo, fall back to user location
      if ! sudo touch "$phase_log_file" 2>&1; then
        # sudo failed - use user-writable location
        log_dir="$HOME/.local/share/omarchy/logs"
        phase_log_file="${log_dir}/omarchy-${phase_name}-install.log"
        mkdir -p "$log_dir" 2>&1 || true
        touch "$phase_log_file" 2>&1 || true
        chmod 666 "$phase_log_file" 2>&1 || true
      else
        sudo chmod 666 "$phase_log_file" 2>&1 || true
      fi
    fi
    
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
