# Install all base packages
echo "[$(date '+%Y-%m-%d %H:%M:%S')] packaging/base.sh: Reading package list from $OMARCHY_INSTALL/omarchy-base.packages" >>"$OMARCHY_INSTALL_LOG_FILE" 2>&1

if [ ! -f "$OMARCHY_INSTALL/omarchy-base.packages" ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] packaging/base.sh: ERROR: Package list file not found: $OMARCHY_INSTALL/omarchy-base.packages" >>"$OMARCHY_INSTALL_LOG_FILE" 2>&1
  exit 1
fi

mapfile -t packages < <(grep -v '^#' "$OMARCHY_INSTALL/omarchy-base.packages" | grep -v '^$')
echo "[$(date '+%Y-%m-%d %H:%M:%S')] packaging/base.sh: Installing ${#packages[@]} base packages" >>"$OMARCHY_INSTALL_LOG_FILE" 2>&1
echo "[$(date '+%Y-%m-%d %H:%M:%S')] packaging/base.sh: Packages: ${packages[*]}" >>"$OMARCHY_INSTALL_LOG_FILE" 2>&1

if ! sudo pacman -S --noconfirm --needed "${packages[@]}" >>"$OMARCHY_INSTALL_LOG_FILE" 2>&1; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] packaging/base.sh: ERROR: Failed to install base packages" >>"$OMARCHY_INSTALL_LOG_FILE" 2>&1
  exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] packaging/base.sh: Successfully installed base packages" >>"$OMARCHY_INSTALL_LOG_FILE" 2>&1
