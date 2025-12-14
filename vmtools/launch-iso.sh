#!/bin/bash
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ISO_DIR="${REPO_ROOT}/isoprep/isoout"

# Find the latest ISO
ISO_FILE=$(ls -t "$ISO_DIR"/omarchy-*.iso 2>/dev/null | head -n 1)

if [ -z "$ISO_FILE" ]; then
    echo "Error: No ISO found in $ISO_DIR"
    echo "Please run build first."
    exit 1
fi

echo "Launching ISO: $ISO_FILE"

qemu-system-x86_64 \
    -enable-kvm \
    -m 8G \
    -smp 4 \
    -cdrom "$ISO_FILE" \
    -boot d \
    -vga std \
    -display default \
    -net nic -net user,hostfwd=tcp::2222-:22 \
    -name "Homerchy Test VM"
