#!/bin/bash
# Install all base packages
# This script logs EVERYTHING to a separate detailed log file for debugging
# Normal output goes to stdout (captured by run_logged), detailed logs go to BASE_LOG_FILE

# Use same directory as main install log - if that works, this will work
LOG_DIR=$(dirname "${OMARCHY_INSTALL_LOG_FILE:-/var/log/omarchy-install.log}")
BASE_LOG_FILE="${LOG_DIR}/omarchy-base-install.log"
TIMESTAMP() { date '+%Y-%m-%d %H:%M:%S'; }

# Create the separate base log file FIRST, before defining LOG functions
# Use same approach as main log file - ensure directory exists, then create file
if [ ! -d "$LOG_DIR" ]; then
  sudo mkdir -p "$LOG_DIR" 2>&1 || true
fi

create_output=$(sudo touch "$BASE_LOG_FILE" 2>&1)
if [ $? -ne 0 ]; then
  echo "[$(TIMESTAMP)] packaging/base.sh: ERROR: Failed to create base log file: $create_output" >&2
  # Don't exit - continue without detailed logging
else
  sudo chmod 666 "$BASE_LOG_FILE" 2>&1 || true
fi

# NOW define LOG functions (file exists, so they can write to it)
LOG() {
  local msg="[$(TIMESTAMP)] packaging/base.sh: $*"
  # Write ONLY to the separate base log file
  echo "$msg" >> "$BASE_LOG_FILE" 2>&1 || true
  # Also output to stdout so it's visible in main log (via run_logged)
  echo "$msg"
}
LOG_ERROR() {
  local msg="[$(TIMESTAMP)] packaging/base.sh: ERROR: $*"
  # Write ONLY to the separate base log file
  echo "$msg" >> "$BASE_LOG_FILE" 2>&1 || true
  # Also output to stderr so it's visible
  echo "$msg" >&2
}

# NOW safe to call LOG() - file exists
LOG "=== BASE.SH STARTED ==="
LOG "Detailed log file: $BASE_LOG_FILE"
LOG "Main install log: ${OMARCHY_INSTALL_LOG_FILE:-/var/log/omarchy-install.log}"
LOG "OMARCHY_INSTALL: ${OMARCHY_INSTALL:-NOT SET}"
LOG "Current directory: $(pwd)"
LOG "User: $(whoami)"
LOG "Sudo available: $(command -v sudo >/dev/null && echo 'YES' || echo 'NO')"
LOG "Pacman available: $(command -v pacman >/dev/null && echo 'YES' || echo 'NO')"
LOG "Base log file created successfully"

PACKAGE_FILE="${OMARCHY_INSTALL}/omarchy-base.packages"
LOG "Reading package list from: $PACKAGE_FILE"

if [ ! -f "$PACKAGE_FILE" ]; then
  LOG_ERROR "Package list file not found: $PACKAGE_FILE"
  LOG "Checking if OMARCHY_INSTALL is correct..."
  LOG "OMARCHY_INSTALL value: ${OMARCHY_INSTALL:-NOT SET}"
  LOG "Looking for package file in common locations..."
  for dir in "/root/omarchy" "/home/$OMARCHY_USER/.local/share/omarchy" "/usr/local/share/omarchy"; do
    if [ -f "$dir/install/omarchy-base.packages" ]; then
      LOG "Found package file at: $dir/install/omarchy-base.packages"
      PACKAGE_FILE="$dir/install/omarchy-base.packages"
      break
    fi
  done
  if [ ! -f "$PACKAGE_FILE" ]; then
    LOG_ERROR "Package file still not found after search"
    exit 1
  fi
fi

LOG "Package file exists: $PACKAGE_FILE"
LOG "Package file size: $(stat -c%s "$PACKAGE_FILE" 2>/dev/null || echo 'unknown') bytes"
LOG "Package file readable: $([ -r "$PACKAGE_FILE" ] && echo 'YES' || echo 'NO')"

LOG "Parsing package list (excluding comments and empty lines)..."
mapfile -t packages < <(grep -v '^#' "$PACKAGE_FILE" | grep -v '^$' || true)
PACKAGE_COUNT=${#packages[@]}
LOG "Found $PACKAGE_COUNT packages to install"

if [ $PACKAGE_COUNT -eq 0 ]; then
  LOG_ERROR "No packages found in package list!"
  LOG "Package file contents (first 20 lines):"
  head -n 20 "$PACKAGE_FILE" | while IFS= read -r line; do
    LOG "  $line"
  done
  exit 1
fi

LOG "Package list:"
for i in "${!packages[@]}"; do
  LOG "  [$((i+1))/$PACKAGE_COUNT] ${packages[$i]}"
done

# Check pacman database
LOG "Checking pacman database..."
pacman_db_check=$(sudo pacman -Sy 2>&1)
pacman_db_exit=$?
if [ $pacman_db_exit -ne 0 ]; then
  LOG_ERROR "Failed to sync pacman database (exit code: $pacman_db_exit)"
  echo "$pacman_db_check" | while IFS= read -r line; do
    LOG "  $line"
  done
  exit 1
fi
LOG "Pacman database synced successfully"

# Verify jq is in the list
if printf '%s\n' "${packages[@]}" | grep -q "^jq$"; then
  LOG "✓ jq is in package list"
else
  LOG_ERROR "jq is NOT in package list!"
  LOG "This is a critical dependency for prebuild.sh"
fi

# Check if jq is already installed
if command -v jq >/dev/null 2>&1; then
  LOG "jq is already installed: $(command -v jq)"
  jq_version=$(jq --version 2>&1 || echo "unknown")
  LOG "jq version: $jq_version"
else
  LOG "jq is NOT currently installed"
fi

LOG "Starting package installation..."
LOG "Command: sudo pacman -S --noconfirm --needed ${packages[*]}"
LOG "--- PACMAN OUTPUT START ---"

# Install packages with explicit error handling and FULL output logging
pacman_start_time=$(date +%s)
pacman_output=$(sudo pacman -S --noconfirm --needed "${packages[@]}" 2>&1)
pacman_exit=$?
pacman_end_time=$(date +%s)
pacman_duration=$((pacman_end_time - pacman_start_time))

# Log ALL pacman output line by line to the separate base log file
echo "$pacman_output" | while IFS= read -r line; do
  echo "[$(TIMESTAMP)] packaging/base.sh: PACMAN: $line" >> "$BASE_LOG_FILE" 2>&1 || true
done
# Also show summary in main output
echo "[$(TIMESTAMP)] packaging/base.sh: Pacman output logged to $BASE_LOG_FILE"

LOG "--- PACMAN OUTPUT END ---"
LOG "Pacman exit code: $pacman_exit"
LOG "Installation duration: ${pacman_duration}s"

if [ $pacman_exit -ne 0 ]; then
  LOG_ERROR "Failed to install base packages (exit code: $pacman_exit)"
  LOG_ERROR "Check pacman database and network connectivity"
  LOG "Full pacman output saved above"
  
  # Check which packages failed
  LOG "Checking which packages are installed..."
  for pkg in "${packages[@]}"; do
    if pacman -Qi "$pkg" >/dev/null 2>&1; then
      LOG "  ✓ $pkg is installed"
    else
      LOG_ERROR "  ✗ $pkg is NOT installed"
    fi
  done
  
  exit 1
fi

LOG "Package installation completed successfully"
LOG "Verifying critical packages..."

# Verify jq installation
if command -v jq >/dev/null 2>&1; then
  jq_path=$(command -v jq)
  jq_version=$(jq --version 2>&1 || echo "unknown")
  LOG "✓ jq verified: $jq_path (version: $jq_version)"
else
  LOG_ERROR "✗ jq verification FAILED - command not found after installation!"
  LOG_ERROR "This will cause prebuild.sh to fail!"
fi

# Verify a few other critical packages
for critical_pkg in "pacman" "sudo" "bash"; do
  if command -v "$critical_pkg" >/dev/null 2>&1; then
    LOG "✓ $critical_pkg verified: $(command -v $critical_pkg)"
  else
    LOG_ERROR "✗ $critical_pkg verification FAILED"
  fi
done

LOG "=== BASE.SH COMPLETED SUCCESSFULLY ==="
LOG "Total packages processed: $PACKAGE_COUNT"
LOG "Installation time: ${pacman_duration}s"
