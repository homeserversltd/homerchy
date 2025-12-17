#!/bin/bash
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# ISO output and qcow2 are now in work directory so they get cleaned up with eject
WORK_DIR="${HOMERCHY_WORK_DIR:-/mnt/work/homerchy-isoprep-work}"
ISO_DIR="${WORK_DIR}/isoout"
DISK_FILE="${WORK_DIR}/homerchy-test-disk.qcow2"

# Find the latest ISO
ISO_FILE=$(ls -t "$ISO_DIR"/omarchy-*.iso 2>/dev/null | head -n 1)

if [ -z "$ISO_FILE" ]; then
    echo "Error: No ISO found in $ISO_DIR"
    echo "Please run build first."
    exit 1
fi

# Ensure work directory exists for qcow2 file with correct permissions
if [ ! -d "$WORK_DIR" ]; then
    sudo mkdir -p "$WORK_DIR"
    sudo chown -R "$(id -u):$(id -g)" "$WORK_DIR"
else
    # Fix permissions if directory exists but user doesn't own it
    if [ ! -w "$WORK_DIR" ]; then
        sudo chown -R "$(id -u):$(id -g)" "$WORK_DIR"
    fi
fi

# Always remove existing disk and create fresh one
if [ -f "$DISK_FILE" ]; then
    echo "Removing existing disk: $DISK_FILE"
    rm -f "$DISK_FILE"
fi

echo "Creating virtual disk: $DISK_FILE"
qemu-img create -f qcow2 "$DISK_FILE" 100G

echo "Launching ISO: $ISO_FILE"
echo "Using disk: $DISK_FILE"

# Check which profile will be used
INDEX_FILE="${REPO_ROOT}/vmtools/index.json"
if [ -f "$INDEX_FILE" ]; then
    PROFILE=$(jq -r '.default_profile // "homerchy-test"' "$INDEX_FILE" 2>/dev/null || echo "homerchy-test")
    echo "VM Profile: $PROFILE"
else
    echo "VM Profile: default (no index.json found)"
fi

qemu-system-x86_64 \
    -enable-kvm \
    -machine q35,accel=kvm \
    -cpu host \
    -m 8G \
    -smp 4 \
    -cdrom "$ISO_FILE" \
    -boot order=dc \
    -drive file="$DISK_FILE",format=qcow2,if=none,id=drive0 \
    -device virtio-blk-pci,drive=drive0 \
    -device virtio-vga \
    -display default \
    -netdev user,id=net0,hostfwd=tcp::2222-:22 \
    -device virtio-net-pci,netdev=net0 \
    -monitor unix:/tmp/homerchy-qemu-monitor.sock,server,nowait \
    -usb -device usb-tablet \
    -name "Homerchy Test VM"
