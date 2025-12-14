#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_DIR="${REPO_ROOT}/isoprep/work"
OUT_DIR="${REPO_ROOT}/isoprep/isoout"
PROFILE_DIR="${WORK_DIR}/profile"

echo -e "${BLUE}Starting Homerchy ISO Build...${NC}"

# Check for dependencies
if ! command -v mkarchiso &> /dev/null; then
    echo "Error: 'mkarchiso' not found. Please install 'archiso' package."
    exit 1
fi

# Ensure output directory exists
mkdir -p "$OUT_DIR"

# Clean up previous work
if [ -d "$WORK_DIR" ]; then
    echo -e "${BLUE}Cleaning up previous work directory...${NC}"
    sudo rm -rf "$WORK_DIR"
fi
mkdir -p "$PROFILE_DIR"

echo -e "${BLUE}Assembling ISO profile...${NC}"

# 1. Copy base Releng config from submodule
cp -r "${REPO_ROOT}/iso-builder/archiso/configs/releng/"* "$PROFILE_DIR/"

# 2. Cleanup unwanted Releng defaults (reflector)
# We handle mirror selection differently or rely on what's provided
rm "$PROFILE_DIR/airootfs/etc/systemd/system/multi-user.target.wants/reflector.service" 2>/dev/null || true
rm -rf "$PROFILE_DIR/airootfs/etc/systemd/system/reflector.service.d" 2>/dev/null || true
rm -rf "$PROFILE_DIR/airootfs/etc/xdg/reflector" 2>/dev/null || true

# 3. Apply Homerchy Custom Overlays
# This overwrites files in the releng profile with our versions
cp -r "${REPO_ROOT}/iso-builder/configs/"* "$PROFILE_DIR/"

# 3a. Detect VM environment and adjust boot timeout
# If building in a VM, set syslinux timeout to 0 for instant boot
# Also check for environment variable override
IS_VM=false
if [ -n "${OMARCHY_VM_BUILD:-}" ]; then
    IS_VM=true
    echo -e "${BLUE}VM build mode forced via OMARCHY_VM_BUILD environment variable${NC}"
elif [ -f /sys/class/dmi/id/product_name ]; then
    PRODUCT_NAME=$(cat /sys/class/dmi/id/product_name 2>/dev/null || echo "")
    if echo "$PRODUCT_NAME" | grep -qiE "(QEMU|KVM|VMware|VirtualBox|Virtual Machine|Xen|Bochs)"; then
        IS_VM=true
        echo -e "${BLUE}VM detected via DMI ($PRODUCT_NAME)${NC}"
    fi
fi

# Also check systemd-detect-virt if available
if [ "$IS_VM" = false ] && command -v systemd-detect-virt &> /dev/null; then
    VIRT_TYPE=$(systemd-detect-virt 2>/dev/null || echo "none")
    if [ "$VIRT_TYPE" != "none" ]; then
        IS_VM=true
        echo -e "${BLUE}VM detected via systemd-detect-virt ($VIRT_TYPE)${NC}"
    fi
fi

if [ "$IS_VM" = true ]; then
    SYSLINUX_CFG="$PROFILE_DIR/syslinux/archiso_sys.cfg"
    if [ -f "$SYSLINUX_CFG" ]; then
        sed -i 's/^TIMEOUT [0-9]*/TIMEOUT 0/' "$SYSLINUX_CFG"
        echo -e "${GREEN}Boot timeout set to 0 for instant VM boot${NC}"
    fi
fi

# 3b. Force Online Build Config
# We want to build using online repos, not looking for a local offline cache
cp "${REPO_ROOT}/iso-builder/configs/pacman-online.conf" "$PROFILE_DIR/pacman.conf"

# 4. Inject Current Repository Source
# This allows the ISO to contain the latest changes from this workspace
# Note: prebuild/ directory is included in this copy and will be available
# at /root/homerchy/prebuild/ in the ISO, which will be deployed during installation
echo -e "${BLUE}Injecting current repository source...${NC}"
mkdir -p "$PROFILE_DIR/airootfs/root/homerchy"
# Copy excluding build artifacts and .git to save space/time
rsync -a --exclude 'isoprep/work' \
         --exclude 'isoprep/isoout' \
         --exclude '.git' \
         "${REPO_ROOT}/" "$PROFILE_DIR/airootfs/root/homerchy/"

# 4b. Inject VM specific environment signal and settings
mkdir -p "$PROFILE_DIR/airootfs/root/vmtools"
cp "${REPO_ROOT}/vmtools/vm-env.sh" "$PROFILE_DIR/airootfs/root/vm-env.sh"
cp "${REPO_ROOT}/vmtools/settings.json" "$PROFILE_DIR/airootfs/root/vmtools/settings.json"

# 5. Customize Package List
# Add packages defined in our tech stack logic
cat <<EOF >> "$PROFILE_DIR/packages.x86_64"
git
gum
jq
openssl
EOF

# 5b. Fix Permissions Targets
# Ensure directories/files referenced in profiledef.sh file_permissions exist
mkdir -p "$PROFILE_DIR/airootfs/var/cache/omarchy/mirror/offline"
mkdir -p "$PROFILE_DIR/airootfs/usr/local/bin"
cp "${REPO_ROOT}/bin/omarchy-upload-log" "$PROFILE_DIR/airootfs/usr/local/bin/"
chmod +x "$PROFILE_DIR/airootfs/usr/local/bin/omarchy-upload-log"

# 6. Ensure pacman config is strict for the build
# We use the pacman.conf provided in our configs for the ISO build process itself
# This ensures we use the correct mirrors/keys during image creation
# Note: mkarchiso uses the pacman.conf in the profile root for the build process
# We already copied it in step 3 (assuming iso-builder/configs/pacman.conf exists)

echo -e "${BLUE}Building ISO with mkarchiso (Requires Sudo)...${NC}"
echo -e "Output will be in: ${GREEN}$OUT_DIR${NC}"

# Run mkarchiso
sudo mkarchiso -v -w "$WORK_DIR/archiso-tmp" -o "$OUT_DIR" "$PROFILE_DIR"

echo -e "${GREEN}Build complete! ISO is located in $OUT_DIR${NC}"
