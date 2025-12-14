#!/bin/bash
set -e

# Config
REPO_ROOT="$(dirname "$(realpath "$0")")"
BUILD_SCRIPT="${REPO_ROOT}/isoprep/build.sh"
LAUNCH_SCRIPT="${REPO_ROOT}/vmtools/launch-iso.sh"
ISO_DIR="${REPO_ROOT}/isoprep/isoout"

function usage() {
    echo "Usage: ./controller.sh [OPTIONS]"
    echo "Options:"
    echo "  -b, --build       Generate a new Homerchy ISO"
    echo "  -l, --launch      Launch the VM using the filtered ISO"
    echo "  -f, --full        Rebuild the ISO and then launch the VM"
    echo "  -d, --deploy DEV  Deploy (dd) the ISO to a device (e.g. /dev/sdX)"
    echo "  -e, --eject       Cleanup (unmount and remove) the build work directory"
    echo "  -h, --help        Show this help message"
}

function do_eject() {
    echo ">>> Ejecting Cartridge (Cleaning up)..."
    local WORK_DIR="${REPO_ROOT}/isoprep/work"
    
    if [ -d "$WORK_DIR" ]; then
        echo "Safely cleaning up mount points in $WORK_DIR..."
        
        # Safe, targeted unmount of specific mkarchiso structures
        # We sort by length (descending) to unmount deepest paths first
        find "$WORK_DIR" -maxdepth 6 -name "work" -type d -prune -o -type d -mountpoint -print | \
        awk '{ print length($0) " " $0; }' | sort -rn | cut -d ' ' -f 2- | \
        while read -r mountpoint; do
            echo "Unmounting: $mountpoint"
            sudo umount "$mountpoint" || true
        done

        # One final targeted pass for stubborn known locations
        sudo umount "$WORK_DIR/archiso-tmp/x86_64/airootfs/proc" 2>/dev/null || true
        sudo umount "$WORK_DIR/archiso-tmp/x86_64/airootfs/sys" 2>/dev/null || true
        sudo umount "$WORK_DIR/archiso-tmp/x86_64/airootfs/dev" 2>/dev/null || true
        sudo umount "$WORK_DIR/archiso-tmp/x86_64/airootfs/run" 2>/dev/null || true
        
        echo "Removing work directory..."
        # Only remove if strictly inside the repo to be safe
        if [[ "$WORK_DIR" == *"/homerchy/isoprep/work" ]]; then
            sudo rm -rf "$WORK_DIR"
            echo "Cartridge ejected."
        else
             echo "Safety check failed: WORK_DIR path looks suspicious ($WORK_DIR). Skipping rm -rf."
        fi
    else
        echo "Nothing to eject (Work dir not found)."
    fi
}

function do_build() {
    echo ">>> Starting Build..."
    if [ -x "$BUILD_SCRIPT" ]; then
        "$BUILD_SCRIPT"
    else
        echo "Error: Build script not found or executable at $BUILD_SCRIPT"
        exit 1
    fi
}

function do_launch() {
    echo ">>> Launching VM..."
    if [ -x "$LAUNCH_SCRIPT" ]; then
        "$LAUNCH_SCRIPT"
    else
        echo "Error: Launch script not found or executable at $LAUNCH_SCRIPT"
        exit 1
    fi
}

function do_deploy() {
    local target_dev="$1"
    if [ -z "$target_dev" ]; then
        echo "Error: No target device specified for deploy."
        exit 1
    fi

    local iso_file=$(ls -t "$ISO_DIR"/omarchy-*.iso 2>/dev/null | head -n 1)
    if [ -z "$iso_file" ]; then
        echo "Error: No ISO found to deploy in $ISO_DIR"
        exit 1
    fi

    echo "WARNING: This will overwrite ALL data on $target_dev"
    echo "Target ISO: $iso_file"
    echo -n "Are you sure? [y/N] "
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "Writing to $target_dev..."
        sudo dd if="$iso_file" of="$target_dev" bs=4M status=progress oflag=sync
        echo "Deploy complete."
    else
        echo "Deploy cancelled."
    fi
}

# Parse Args
if [ $# -eq 0 ]; then
    usage
    exit 1
fi

while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--build)
            do_build
            shift
            ;;
        -l|--launch)
            do_launch
            shift
            ;;
        -f|--full)
            do_eject
            do_build
            do_launch
            shift
            ;;
        -d|--deploy)
            TARGET_DEVICE="$2"
            do_deploy "$TARGET_DEVICE"
            shift 2
            ;;
        -e|--eject)
            do_eject
            shift
            ;;
        -h|--help)
            usage
            shift
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done
