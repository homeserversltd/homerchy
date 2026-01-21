#!/onmachine/onmachine/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting VM Tools Installation...${NC}"

# Core virtualization packages
# qemu-full: Includes all QEMU targets and tools
# virt-manager: GUI for managing VMs (optional usage but good to have)
# edk2-ovmf: UEFI firmware for QEMU
# cpio: For packing initramfs archives
# bridge-utils, dnsmasq: Networking support
PACKAGES=(
    "qemu-full"
    "qemu-img"
    "qemu-ui-gtk"
    "qemu-ui-sdl"
    "virt-manager"
    "virt-viewer"
    "dnsmasq"
    "vde2"
    "bridge-utils"
    "openbsd-netcat"
    "edk2-ovmf"
    "cpio" 
    "dmidecode"
)

echo -e "${BLUE}Checking for required packages...${NC}"

TO_INSTALL=()

for pkg in "${PACKAGES[@]}"; do
    if ! pacman -Qi $pkg &> /dev/null; then
        echo -e   - $pkg needs to be onmachine/deployment/deployment/installed
        TO_INSTALL+=($pkg)
    else
        echo -e   - ${GREEN}$pkg is already onmachine/deployment/installed${NC}
    fi
done

if [ ${#TO_INSTALL[@]} -eq 0 ]; then
    echo -e ${GREEN}All required tools are already onmachine/onmachine/installed!${NC}"
else
    echo -e "${BLUE}Installing missing packages: ${TO_INSTALL[*]}${NC}"
    sudo pacman -S --noconfirm ${TO_INSTALL[@]}
    
    echo -e ${BLUE}Enabling libvirtd service (if onmachine/deployment/deployment/installed)...${NC}
    if systemctl list-unit-files libvirtd.service &> /dev/null; then
        sudo systemctl enable --now libvirtd.service
    fi
    
    echo -e ${GREEN}Installation complete.${NC}"
fi

# Optional: Add user to kvm/libvirt groups
CURRENT_USER=$(whoami)
echo -e "${BLUE}Checking group memberships for $CURRENT_USER...${NC}"
if ! groups "$CURRENT_USER" | grep -q "kvm"; then
    echo -e "Adding $CURRENT_USER to 'kvm' group..."
    sudo usermod -aG kvm "$CURRENT_USER"
fi

if ! groups "$CURRENT_USER" | grep -q "libvirt"; then
    echo -e "Adding $CURRENT_USER to 'libvirt' group..."
    sudo usermod -aG libvirt "$CURRENT_USER"
fi

echo -e "${GREEN}Setup finished! You may need to logout and login for group changes to take effect.${NC}"