# Install all base packages
echo "[$(date '+%Y-%m-%d %H:%M:%S')] packaging/base.sh: Reading package list from $OMARCHY_INSTALL/omarchy-base.packages"

if [ ! -f "$OMARCHY_INSTALL/omarchy-base.packages" ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] packaging/base.sh: ERROR: Package list file not found: $OMARCHY_INSTALL/omarchy-base.packages"
  exit 1
fi

mapfile -t packages < <(grep -v '^#' "$OMARCHY_INSTALL/omarchy-base.packages" | grep -v '^$')
echo "[$(date '+%Y-%m-%d %H:%M:%S')] packaging/base.sh: Installing ${#packages[@]} base packages"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] packaging/base.sh: Packages: ${packages[*]}"

if ! sudo pacman -S --noconfirm --needed "${packages[@]}" 2>&1; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] packaging/base.sh: ERROR: Failed to install base packages"
  exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] packaging/base.sh: Successfully installed base packages"
