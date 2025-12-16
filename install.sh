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

# Call Python orchestrator (Python-only installation system)
INSTALL_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_INSTALL="$INSTALL_SCRIPT_DIR/install.py"

# Check for Python
if ! command -v python3 >/dev/null 2>&1; then
  echo "" >&2
  echo "════════════════════════════════════════════════════════════════" >&2
  echo "ERROR: Python 3 is required but not found" >&2
  echo "════════════════════════════════════════════════════════════════" >&2
  echo "" >&2
  echo "Installation requires Python 3 to be available in PATH" >&2
  echo "  PATH: $PATH" >&2
  echo "" >&2
  echo "Please install Python 3 and ensure it's in your PATH" >&2
  echo "" >&2
  echo "════════════════════════════════════════════════════════════════" >&2
  echo "" >&2
  exit 1
fi

# Check for install.py
if [ ! -f "$PYTHON_INSTALL" ]; then
  echo "" >&2
  echo "════════════════════════════════════════════════════════════════" >&2
  echo "ERROR: Python orchestrator (install.py) not found" >&2
  echo "════════════════════════════════════════════════════════════════" >&2
  echo "" >&2
  echo "Expected file: $PYTHON_INSTALL" >&2
  echo "  File exists: $(if [ -f "$PYTHON_INSTALL" ]; then echo "YES"; elif [ -e "$PYTHON_INSTALL" ]; then echo "EXISTS BUT NOT FILE"; else echo "NO"; fi)" >&2
  echo "" >&2
  echo "Script directory: $INSTALL_SCRIPT_DIR" >&2
  echo "  Directory exists: $(if [ -d "$INSTALL_SCRIPT_DIR" ]; then echo "YES"; else echo "NO"; fi)" >&2
  if [ -d "$INSTALL_SCRIPT_DIR" ]; then
    echo "  Contents:" >&2
    if command -v ls >/dev/null 2>&1; then
      ls -la "$INSTALL_SCRIPT_DIR" 2>&1 | sed 's/^/    /' >&2
    else
      find "$INSTALL_SCRIPT_DIR" -maxdepth 1 2>/dev/null | sed 's/^/    /' >&2
    fi
  fi
  echo "" >&2
  echo "Environment context:" >&2
  echo "  Current directory: $(pwd)" >&2
  echo "  HOME: ${HOME:-[NOT SET]}" >&2
  echo "  USER: ${USER:-[NOT SET]}" >&2
  echo "  Python3 version: $(python3 --version 2>&1)" >&2
  echo "" >&2
  echo "════════════════════════════════════════════════════════════════" >&2
  echo "" >&2
  exit 1
fi

# Execute Python orchestrator
exec python3 "$PYTHON_INSTALL"
