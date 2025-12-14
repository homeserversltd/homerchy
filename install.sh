#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -eEo pipefail

# Define Omarchy locations
export OMARCHY_PATH="$HOME/.local/share/omarchy"
export OMARCHY_INSTALL="$OMARCHY_PATH/install"
export OMARCHY_INSTALL_LOG_FILE="/var/log/omarchy-install.log"
export PATH="$OMARCHY_PATH/bin:$PATH"

# Install
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting helpers..." >>"$OMARCHY_INSTALL_LOG_FILE" 2>&1
source "$OMARCHY_INSTALL/helpers/all.sh"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting preflight..." >>"$OMARCHY_INSTALL_LOG_FILE" 2>&1
source "$OMARCHY_INSTALL/preflight/all.sh"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting packaging..." >>"$OMARCHY_INSTALL_LOG_FILE" 2>&1
source "$OMARCHY_INSTALL/packaging/all.sh"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting config..." >>"$OMARCHY_INSTALL_LOG_FILE" 2>&1
source "$OMARCHY_INSTALL/config/all.sh"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting login setup..." >>"$OMARCHY_INSTALL_LOG_FILE" 2>&1
source "$OMARCHY_INSTALL/login/all.sh"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting post-install..." >>"$OMARCHY_INSTALL_LOG_FILE" 2>&1
source "$OMARCHY_INSTALL/post-install/all.sh"
