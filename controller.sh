#!/bin/bash
set -e

# Config
REPO_ROOT="$(dirname "$(realpath "$0")")"
BUILD_SCRIPT="${REPO_ROOT}/isoprep/build.py"
LAUNCH_SCRIPT="${REPO_ROOT}/vmtools/launch-iso.sh"
# ISO output is now in work directory, will be set dynamically based on work dir
WORK_DIR_BASE="/mnt/work/homerchy-isoprep-work"
ISO_DIR="${WORK_DIR_BASE}/isoout"

function usage() {
    echo "Usage: ./controller.sh [OPTIONS]"
    echo "Options:"
    echo "  -b, --build       Generate a new Homerchy ISO"
    echo "  -l, --launch      Launch the VM using the filtered ISO"
    echo "  -f, --full        Build the ISO (reusing cache) and then launch the VM"
    echo "  -F, --full-clean  Full clean rebuild (eject all caches, build, then launch)"
    echo "  -d, --deploy DEV  Deploy (dd) the ISO to a device (e.g. /dev/sdX)"
    echo "  -e, --eject       Eject cartridge (preserves caches for faster rebuilds)"
    echo "  -E, --eject-full  Full eject (removes all caches, completely clean)"
    echo "  -h, --help        Show this help message"
}

function do_eject() {
    local FULL_CLEANUP="${1:-false}"
    
    if [ "$FULL_CLEANUP" = "true" ]; then
        echo ">>> Full Eject Cartridge (Removing ALL caches)..."
    else
        echo ">>> Ejecting Cartridge (Preserving caches for faster rebuilds)..."
    fi
    
    # Check both old location and new dedicated tmpfs location
    local WORK_DIR_OLD="/tmp/homerchy-isoprep-work"
    local WORK_DIR_NEW="/mnt/work/homerchy-isoprep-work"
    local WORK_DIR="$WORK_DIR_NEW"
    
    # Use new location if it exists, otherwise fall back to old location
    if [ ! -d "$WORK_DIR_NEW" ] && [ -d "$WORK_DIR_OLD" ]; then
        WORK_DIR="$WORK_DIR_OLD"
    fi
    
    if [ -d "$WORK_DIR" ]; then
        echo "Safely cleaning up mount points in $WORK_DIR..."
        
        # Step 1: Kill any processes using the work directory
        echo "Checking for processes using work directory..."
        local pids=$(lsof +D "$WORK_DIR" 2>/dev/null | awk 'NR>1 {print $2}' | sort -u)
        if [ -n "$pids" ]; then
            echo "Found processes using work directory, terminating..."
            echo "$pids" | while read -r pid; do
                if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
                    echo "  Killing PID $pid"
                    sudo kill -TERM "$pid" 2>/dev/null || true
                fi
            done
            sleep 2
            # Force kill any remaining processes
            pids=$(lsof +D "$WORK_DIR" 2>/dev/null | awk 'NR>1 {print $2}' | sort -u)
            if [ -n "$pids" ]; then
                echo "$pids" | while read -r pid; do
                    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
                        echo "  Force killing PID $pid"
                        sudo kill -KILL "$pid" 2>/dev/null || true
                    fi
                done
                sleep 1
            fi
        fi
        
        # Step 2: Use findmnt to find ALL mounts recursively (more reliable than find)
        echo "Finding all mount points in work directory..."
        local mounts=$(findmnt -rn -o TARGET -T "$WORK_DIR" 2>/dev/null | grep "^$WORK_DIR" | sort -r)
        
        if [ -n "$mounts" ]; then
            echo "$mounts" | while read -r mountpoint; do
                if [ -n "$mountpoint" ]; then
                    echo "Unmounting: $mountpoint"
                    # Try normal unmount first
                    sudo umount "$mountpoint" 2>/dev/null || {
                        # If that fails, try lazy unmount (detaches immediately, cleans up later)
                        echo "  Normal unmount failed, trying lazy unmount..."
                        sudo umount -l "$mountpoint" 2>/dev/null || true
                    }
                fi
            done
        fi
        
        # Step 3: Fallback - find any remaining mountpoints with find
        echo "Checking for any remaining mount points..."
        find "$WORK_DIR" -type d -mountpoint 2>/dev/null | sort -r | while read -r mountpoint; do
            if [ -n "$mountpoint" ]; then
                echo "Unmounting (fallback): $mountpoint"
                sudo umount -l "$mountpoint" 2>/dev/null || true
            fi
        done
        
        # Step 4: Targeted unmount of known mkarchiso locations (with lazy fallback)
        echo "Unmounting known mkarchiso locations..."
        for mountpoint in \
            "$WORK_DIR/archiso-tmp/x86_64/airootfs/proc" \
            "$WORK_DIR/archiso-tmp/x86_64/airootfs/sys" \
            "$WORK_DIR/archiso-tmp/x86_64/airootfs/dev" \
            "$WORK_DIR/archiso-tmp/x86_64/airootfs/dev/pts" \
            "$WORK_DIR/archiso-tmp/x86_64/airootfs/run" \
            "$WORK_DIR/archiso-tmp/x86_64/airootfs/tmp"; do
            if mountpoint -q "$mountpoint" 2>/dev/null; then
                echo "  Unmounting: $mountpoint"
                sudo umount "$mountpoint" 2>/dev/null || sudo umount -l "$mountpoint" 2>/dev/null || true
            fi
        done
        
        # Step 5: Clean up system-wide symlink created during build
        echo "Cleaning up system-wide symlink..."
        local system_mirror_link="/var/cache/omarchy/mirror/offline"
        if [ -L "$system_mirror_link" ]; then
            echo "  Removing symlink: $system_mirror_link"
            sudo rm -f "$system_mirror_link" 2>/dev/null || true
        fi
        
        # Step 6: Final check - ensure no mounts remain
        sleep 1
        local remaining_mounts=$(findmnt -rn -o TARGET -T "$WORK_DIR" 2>/dev/null | grep "^$WORK_DIR" || true)
        if [ -n "$remaining_mounts" ]; then
            echo "WARNING: Some mounts may still be active:"
            echo "$remaining_mounts"
            echo "Attempting lazy unmount of remaining mounts..."
            echo "$remaining_mounts" | while read -r mountpoint; do
                if [ -n "$mountpoint" ]; then
                    sudo umount -l "$mountpoint" 2>/dev/null || true
                fi
            done
        fi
        
        # Step 7: Remove work directory (with cache preservation logic)
        if [[ "$WORK_DIR" == "/tmp/homerchy-isoprep-work" ]] || [[ "$WORK_DIR" == "/mnt/work/homerchy-isoprep-work" ]]; then
            if [ "$FULL_CLEANUP" = "true" ]; then
                # Full cleanup: remove everything including caches
                echo "Removing work directory and ALL caches..."
                local final_pids=$(lsof +D "$WORK_DIR" 2>/dev/null | awk 'NR>1 {print $2}' | sort -u || true)
                if [ -n "$final_pids" ]; then
                    echo "WARNING: Processes still using work directory, forcing removal..."
                fi
                sudo rm -rf "$WORK_DIR"
                echo "✓ Cartridge fully ejected (all caches removed)"
            else
                # Normal cleanup: preserve caches
                echo "Removing work directory (preserving caches)..."
                
                # Preserve cacheable directories
                local PROFILE_DIR="$WORK_DIR/profile"
                local ARCHISO_TMP="$WORK_DIR/archiso-tmp"
                local PRESERVE_DIR="/mnt/work/.homerchy-cache-preserve"
                
                if [ -d "$PROFILE_DIR" ] || [ -d "$ARCHISO_TMP" ]; then
                    echo "Preserving caches for faster rebuilds..."
                    sudo mkdir -p "$PRESERVE_DIR"
                    
                    # Preserve profile (injected source + package cache)
                    if [ -d "$PROFILE_DIR" ]; then
                        echo "  Preserving profile directory..."
                        sudo mv "$PROFILE_DIR" "$PRESERVE_DIR/profile" 2>/dev/null || true
                    fi
                    
                    # Preserve archiso-tmp package cache (but remove build artifacts first)
                    if [ -d "$ARCHISO_TMP" ]; then
                        echo "  Cleaning archiso-tmp before preserving (removing build artifacts)..."
                        # Remove huge build directories before preserving
                        sudo rm -rf "$ARCHISO_TMP/x86_64" 2>/dev/null || true
                        sudo rm -rf "$ARCHISO_TMP/iso" 2>/dev/null || true
                        # Remove state files
                        sudo rm -f "$ARCHISO_TMP"/*.state 2>/dev/null || true
                        sudo rm -f "$ARCHISO_TMP"/base.* 2>/dev/null || true
                        # Only preserve if there's actually something left (package cache)
                        if [ -n "$(ls -A "$ARCHISO_TMP" 2>/dev/null)" ]; then
                            echo "  Preserving archiso-tmp package cache..."
                            sudo mv "$ARCHISO_TMP" "$PRESERVE_DIR/archiso-tmp" 2>/dev/null || true
                        else
                            echo "  No package cache to preserve in archiso-tmp"
                            sudo rmdir "$ARCHISO_TMP" 2>/dev/null || true
                        fi
                    fi
                fi
                
                # Remove work directory
                local final_pids=$(lsof +D "$WORK_DIR" 2>/dev/null | awk 'NR>1 {print $2}' | sort -u || true)
                if [ -n "$final_pids" ]; then
                    echo "WARNING: Processes still using work directory, forcing removal..."
                fi
                sudo rm -rf "$WORK_DIR"
                
                # Restore preserved caches
                if [ -d "$PRESERVE_DIR" ]; then
                    echo "Restoring preserved caches..."
                    if [ -d "$PRESERVE_DIR/profile" ]; then
                        sudo mkdir -p "$WORK_DIR"
                        sudo mv "$PRESERVE_DIR/profile" "$WORK_DIR/profile" 2>/dev/null || true
                    fi
                    if [ -d "$PRESERVE_DIR/archiso-tmp" ]; then
                        sudo mkdir -p "$WORK_DIR"
                        sudo mv "$PRESERVE_DIR/archiso-tmp" "$WORK_DIR/archiso-tmp" 2>/dev/null || true
                    fi
                    sudo rmdir "$PRESERVE_DIR" 2>/dev/null || true
                fi
                
                echo "✓ Cartridge ejected (caches preserved for faster rebuilds)"
            fi
        else
             echo "Safety check failed: WORK_DIR path looks suspicious ($WORK_DIR). Skipping rm -rf."
        fi
    else
        echo "Nothing to eject (Work dir not found)."
    fi
}

function setup_build_workdir() {
    # Create work directory on disk (not tmpfs, no swap)
    local WORK_DIR="/mnt/work/homerchy-isoprep-work"
    
    # Create work directory with proper ownership
    if [ ! -d "$WORK_DIR" ]; then
        echo "Creating build work directory at $WORK_DIR..."
        sudo mkdir -p "$WORK_DIR"
        # Set ownership to current user
        sudo chown -R "$(id -u):$(id -g)" "$WORK_DIR"
        echo "✓ Build work directory created"
    else
        echo "Build work directory already exists at $WORK_DIR"
    fi
    
    # Export work directory location
    export HOMERCHY_WORK_DIR="$WORK_DIR"
}

function cleanup_build_workdir() {
    # Clean up work directory, but preserve cacheable parts (unless full clean)
    local WORK_DIR="/mnt/work/homerchy-isoprep-work"
    local FULL_CLEAN="${HOMERCHY_FULL_CLEAN:-false}"
    
    if [ -d "$WORK_DIR" ]; then
        if [ "$FULL_CLEAN" = "true" ]; then
            echo "Cleaning up build work directory (FULL CLEAN - removing ALL caches)..."
        else
            echo "Cleaning up build work directory (preserving caches)..."
        fi
        
        # Kill any processes using the directory
        local pids=$(lsof +D "$WORK_DIR" 2>/dev/null | awk 'NR>1 {print $2}' | sort -u || true)
        if [ -n "$pids" ]; then
            echo "Terminating processes using work directory..."
            echo "$pids" | while read -r pid; do
                if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
                    sudo kill -TERM "$pid" 2>/dev/null || true
                fi
            done
            sleep 2
            # Force kill if still running
            pids=$(lsof +D "$WORK_DIR" 2>/dev/null | awk 'NR>1 {print $2}' | sort -u || true)
            if [ -n "$pids" ]; then
                echo "$pids" | while read -r pid; do
                    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
                        sudo kill -KILL "$pid" 2>/dev/null || true
                    fi
                done
            fi
        fi
        
        # Unmount any mounts in the directory
        local mounts=$(findmnt -rn -o TARGET -T "$WORK_DIR" 2>/dev/null | grep "^$WORK_DIR" | sort -r || true)
        if [ -n "$mounts" ]; then
            echo "$mounts" | while read -r mountpoint; do
                if [ -n "$mountpoint" ]; then
                    sudo umount -l "$mountpoint" 2>/dev/null || true
                fi
            done
        fi
        
        if [ "$FULL_CLEAN" = "true" ]; then
            # Full clean: remove everything
            echo "Removing work directory and ALL caches (full clean mode)..."
            sudo rm -rf "$WORK_DIR"
            echo "✓ Work directory fully cleaned (all caches removed)"
        else
            # Preserve cacheable directories:
            # - profile/airootfs/root/homerchy (injected source - takes ages to copy)
            # - profile/airootfs/var/cache/omarchy/mirror/offline (package cache)
            # - archiso-tmp (package cache for mkarchiso)
            # Remove only the build artifacts that change each time
            
            local PROFILE_DIR="$WORK_DIR/profile"
            local ARCHISO_TMP="$WORK_DIR/archiso-tmp"
            
            # Remove only the parts that need to be rebuilt
            if [ -d "$ARCHISO_TMP" ]; then
                echo "Preserving archiso-tmp for package cache..."
                # Remove only the x86_64 build directory, keep package cache
                sudo rm -rf "$ARCHISO_TMP/x86_64" 2>/dev/null || true
                sudo rm -rf "$ARCHISO_TMP/iso" 2>/dev/null || true
                # Remove state files that cause stale build issues
                sudo rm -f "$ARCHISO_TMP"/*.state 2>/dev/null || true
                sudo rm -f "$ARCHISO_TMP"/base.* 2>/dev/null || true
            fi
            
            if [ -d "$PROFILE_DIR" ]; then
                echo "Cleaning up profile directory (preserving only caches)..."
                
                # Preserve only the cacheable parts, remove everything else
                local CACHE_DIR="$PROFILE_DIR/airootfs/var/cache/omarchy/mirror/offline"
                local INJECTED_SOURCE="$PROFILE_DIR/airootfs/root/homerchy"
                local TEMP_CACHE="$WORK_DIR/offline-mirror-cache-temp"
                local TEMP_SOURCE="$WORK_DIR/injected-source-temp"
                
                # Clean up any stale temp directories from previous runs
                if [ -d "$TEMP_CACHE" ]; then
                    sudo rm -rf "$TEMP_CACHE"
                fi
                if [ -d "$TEMP_SOURCE" ]; then
                    sudo rm -rf "$TEMP_SOURCE"
                fi
                
                # Preserve package cache if it exists and has packages
                if [ -d "$CACHE_DIR" ] && [ -n "$(find "$CACHE_DIR" -name '*.pkg.tar.*' 2>/dev/null | head -1)" ]; then
                    echo "  Preserving package cache..."
                    sudo mkdir -p "$(dirname "$TEMP_CACHE")"
                    sudo mv "$CACHE_DIR" "$TEMP_CACHE" 2>/dev/null || true
                fi
                
                # Preserve injected source if it exists
                if [ -d "$INJECTED_SOURCE" ]; then
                    echo "  Preserving injected source..."
                    sudo mkdir -p "$(dirname "$TEMP_SOURCE")"
                    sudo mv "$INJECTED_SOURCE" "$TEMP_SOURCE" 2>/dev/null || true
                fi
                
                # Remove entire profile directory (it will be recreated by prepare phase)
                echo "  Removing profile directory..."
                sudo rm -rf "$PROFILE_DIR"
                
                # Restore preserved caches (prepare phase will handle this, but we do it here too for consistency)
                if [ -d "$TEMP_CACHE" ]; then
                    echo "  Restoring package cache..."
                    sudo mkdir -p "$(dirname "$CACHE_DIR")"
                    sudo mv "$TEMP_CACHE" "$CACHE_DIR" 2>/dev/null || true
                fi
                
                if [ -d "$TEMP_SOURCE" ]; then
                    echo "  Restoring injected source..."
                    sudo mkdir -p "$(dirname "$INJECTED_SOURCE")"
                    sudo mv "$TEMP_SOURCE" "$INJECTED_SOURCE" 2>/dev/null || true
                fi
            fi
            
            # Only remove work directory if it's completely empty (shouldn't happen with preserved caches)
            if [ -z "$(ls -A "$WORK_DIR" 2>/dev/null)" ]; then
                sudo rmdir "$WORK_DIR" 2>/dev/null || true
            else
                echo "✓ Preserved cacheable directories for faster rebuild"
            fi
        fi
    fi
}

function do_build() {
    local FULL_CLEAN="${1:-false}"
    echo ">>> Starting Build..."
    
    # Setup work directory on disk
    setup_build_workdir
    
    # Use work directory
    local WORK_DIR="${HOMERCHY_WORK_DIR:-/mnt/work/homerchy-isoprep-work}"
    
    # Clean up any stale mounts/processes before building to prevent accumulation
    if [ -d "$WORK_DIR" ]; then
        echo "Pre-build cleanup: Checking for stale mounts..."
        local stale_mounts=$(findmnt -rn -o TARGET -T "$WORK_DIR" 2>/dev/null | grep "^$WORK_DIR" || true)
        if [ -n "$stale_mounts" ]; then
            echo "Found stale mounts from previous build, cleaning up..."
            # Quick cleanup - just unmount, don't remove directory
            echo "$stale_mounts" | sort -r | while read -r mountpoint; do
                if [ -n "$mountpoint" ]; then
                    sudo umount -l "$mountpoint" 2>/dev/null || true
                fi
            done
        fi
    fi
    
    # Run build with cleanup on exit
    if [ -f "$BUILD_SCRIPT" ]; then
        # Use trap to ensure work directory cleanup even on error
        trap cleanup_build_workdir EXIT
        # Set environment variables for work directory location and full clean mode
        export HOMERCHY_WORK_DIR="$WORK_DIR"
        export HOMERCHY_FULL_CLEAN="$FULL_CLEAN"
        python3 "$BUILD_SCRIPT"
        local build_exit=$?
        # Cleanup work directory
        cleanup_build_workdir
        trap - EXIT
        # Clear the full clean flag after cleanup
        unset HOMERCHY_FULL_CLEAN
        return $build_exit
    else
        echo "Error: Build script not found at $BUILD_SCRIPT"
        cleanup_build_workdir
        return 1
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

    # ISO is now in work directory
    local iso_dir="${HOMERCHY_WORK_DIR:-$WORK_DIR_BASE}/isoout"
    local iso_file=$(ls -t "$iso_dir"/omarchy-*.iso 2>/dev/null | head -n 1)
    if [ -z "$iso_file" ]; then
        echo "Error: No ISO found to deploy in $iso_dir"
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
            do_build "false"
            shift
            ;;
        -l|--launch)
            do_launch
            shift
            ;;
        -f|--full)
            do_build "false"
            if [ $? -eq 0 ]; then
                do_launch
            else
                echo "Build failed, skipping VM launch."
                exit 1
            fi
            shift
            ;;
        -F|--full-clean)
            do_eject "true"
            # Also remove preserved cache directory if it exists
            PRESERVE_DIR="/mnt/work/.homerchy-cache-preserve"
            if [ -d "$PRESERVE_DIR" ]; then
                echo "Removing preserved cache directory..."
                sudo rm -rf "$PRESERVE_DIR"
                echo "✓ Preserved cache directory removed"
            fi
            do_build "true"
            if [ $? -eq 0 ]; then
                do_launch
            else
                echo "Build failed, skipping VM launch."
                exit 1
            fi
            shift
            ;;
        -d|--deploy)
            TARGET_DEVICE="$2"
            do_deploy "$TARGET_DEVICE"
            shift 2
            ;;
        -e|--eject)
            do_eject "false"
            shift
            ;;
        -E|--eject-full)
            do_eject "true"
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
