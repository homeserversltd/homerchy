#!/bin/bash
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# qcow2 is in work directory
WORK_DIR="${HOMERCHY_WORK_DIR:-/mnt/work/homerchy-isoprep-work}"
DISK_FILE="${WORK_DIR}/homerchy-test-disk.qcow2"

# Check if disk exists
if [ ! -f "$DISK_FILE" ]; then
    echo "Error: No disk found at $DISK_FILE"
    echo "Please run installation first (use -L to launch ISO for fresh install)."
    exit 1
fi

# Check if disk has any content (not just empty qcow2)
DISK_SIZE=$(qemu-img info "$DISK_FILE" 2>/dev/null | grep "virtual size" | awk '{print $3}' || echo "0")
if [ "$DISK_SIZE" = "0" ] || [ -z "$DISK_SIZE" ]; then
    echo "Error: Disk exists but appears to be empty"
    echo "Please run installation first (use -L to launch ISO for fresh install)."
    exit 1
fi

echo "Launching installed system from disk: $DISK_FILE"

# Check which profile was used (for reference)
INDEX_FILE="${REPO_ROOT}/vmtools/index.json"
if [ -f "$INDEX_FILE" ]; then
    PROFILE=$(jq -r '.default_profile // "homerchy-test"' "$INDEX_FILE" 2>/dev/null || echo "homerchy-test")
    echo "VM Profile: $PROFILE"
else
    echo "VM Profile: default (no index.json found)"
fi

# Boot from disk (no ISO, boot order=dc means disk first, then cdrom)
qemu-system-x86_64 \
    -enable-kvm \
    -machine q35,accel=kvm \
    -cpu host \
    -m 8G \
    -smp 4 \
    -boot order=d \
    -drive file="$DISK_FILE",format=qcow2,if=none,id=drive0 \
    -device virtio-blk-pci,drive=drive0 \
    -device virtio-vga \
    -display default \
    -netdev user,id=net0,hostfwd=tcp::2222-:22 \
    -device virtio-net-pci,netdev=net0 \
    -monitor unix:/tmp/homerchy-qemu-monitor.sock,server,nowait \
    -usb -device usb-tablet \
    -name "Homerchy Test VM"
