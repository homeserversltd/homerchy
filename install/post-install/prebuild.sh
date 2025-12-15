#!/bin/bash
# Deploy prebuild configuration files based on index.json manifest
# This script logs EVERYTHING to a separate detailed log file for debugging
# Normal output goes to stdout (captured by run_logged), detailed logs go to PREBUILD_LOG_FILE

set -euo pipefail

# Use same directory as main install log - if that works, this will work
LOG_DIR=$(dirname "${OMARCHY_INSTALL_LOG_FILE:-/var/log/omarchy-install.log}")
PREBUILD_LOG_FILE="${LOG_DIR}/omarchy-prebuild-install.log"
TIMESTAMP() { date '+%Y-%m-%d %H:%M:%S'; }

# Create the separate prebuild log file FIRST, before defining LOG functions
# Use same approach as main log file - ensure directory exists, then create file
if [ ! -d "$LOG_DIR" ]; then
  sudo mkdir -p "$LOG_DIR" 2>&1 || true
fi

create_output=$(sudo touch "$PREBUILD_LOG_FILE" 2>&1)
if [ $? -ne 0 ]; then
  echo "[$(TIMESTAMP)] post-install/prebuild.sh: ERROR: Failed to create prebuild log file: $create_output" >&2
else
  sudo chmod 666 "$PREBUILD_LOG_FILE" 2>&1 || true
fi

# NOW define LOG functions (file exists, so they can write to it)
LOG() {
  local msg="[$(TIMESTAMP)] post-install/prebuild.sh: $*"
  # Write ONLY to the separate prebuild log file
  echo "$msg" >> "$PREBUILD_LOG_FILE" 2>&1 || true
  # Also output to stdout so it's visible in main log (via run_logged)
  echo "$msg"
}
LOG_ERROR() {
  local msg="[$(TIMESTAMP)] post-install/prebuild.sh: ERROR: $*"
  # Write ONLY to the separate prebuild log file
  echo "$msg" >> "$PREBUILD_LOG_FILE" 2>&1 || true
  # Also output to stderr so it's visible
  echo "$msg" >&2
}

# NOW safe to call LOG() - file exists
LOG "=== PREBUILD.SH STARTED ==="
LOG "Detailed log file: $PREBUILD_LOG_FILE"
LOG "Main install log: ${OMARCHY_INSTALL_LOG_FILE:-/var/log/omarchy-install.log}"
LOG "OMARCHY_PATH: ${OMARCHY_PATH:-NOT SET}"
LOG "Current directory: $(pwd)"
LOG "User: $(whoami)"
LOG "Prebuild log file created successfully"

# Determine prebuild directory location
PREBUILD_DIR="${OMARCHY_PATH}/prebuild"
INDEX_FILE="${PREBUILD_DIR}/index.json"
LOG "PREBUILD_DIR: $PREBUILD_DIR"
LOG "INDEX_FILE: $INDEX_FILE"

# Check if prebuild directory exists
if [[ ! -d "$PREBUILD_DIR" ]]; then
  LOG_ERROR "Prebuild directory not found: $PREBUILD_DIR"
  LOG "Skipping prebuild deployment"
  return 0
fi

LOG "Prebuild directory exists: $PREBUILD_DIR"

# Check if index.json exists
if [[ ! -f "$INDEX_FILE" ]]; then
  LOG_ERROR "index.json not found: $INDEX_FILE"
  LOG "Skipping prebuild deployment"
  return 0
fi

LOG "index.json exists: $INDEX_FILE"
LOG "index.json size: $(stat -c%s "$INDEX_FILE" 2>/dev/null || echo 'unknown') bytes"

# Check if jq is available, install if missing
LOG "Checking for jq..."
if ! command -v jq &>/dev/null; then
  LOG_ERROR "jq not found, attempting to install..."
  jq_install_output=$(sudo pacman -S --noconfirm --needed jq 2>&1)
  jq_install_exit=$?
  echo "$jq_install_output" | while IFS= read -r line; do
    echo "[$(TIMESTAMP)] post-install/prebuild.sh: PACMAN: $line" >> "$PREBUILD_LOG_FILE" 2>&1 || true
  done
  if [ $jq_install_exit -eq 0 ]; then
    LOG "jq installed successfully"
    jq_path=$(command -v jq)
    jq_version=$(jq --version 2>&1 || echo "unknown")
    LOG "jq verified: $jq_path (version: $jq_version)"
  else
    LOG_ERROR "Failed to install jq (exit code: $jq_install_exit)"
    LOG_ERROR "jq installation output logged to $PREBUILD_LOG_FILE"
    return 1
  fi
else
  jq_path=$(command -v jq)
  jq_version=$(jq --version 2>&1 || echo "unknown")
  LOG "jq already installed: $jq_path (version: $jq_version)"
fi

# Validate JSON syntax
LOG "Validating JSON syntax in $INDEX_FILE..."
if ! jq empty "$INDEX_FILE" 2>/dev/null; then
  LOG_ERROR "Invalid JSON syntax in $INDEX_FILE"
  LOG "JSON validation output:"
  jq empty "$INDEX_FILE" 2>&1 | while IFS= read -r line; do
    LOG_ERROR "  $line"
  done
  return 1
fi
LOG "JSON syntax valid"

LOG "Starting prebuild deployment"

# Determine user home directory
# In chroot context, use OMARCHY_USER; otherwise use $HOME
if [[ -n "${OMARCHY_USER:-}" ]]; then
  USER_HOME="/home/$OMARCHY_USER"
else
  USER_HOME="$HOME"
fi

# Expand ~ in paths to actual home directory
expand_path() {
  local path="$1"
  echo "${path//\~/$USER_HOME}"
}

# Install packages
LOG "Installing prerequisite packages"

packages=$(jq -r '.packages[]?' "$INDEX_FILE" 2>/dev/null || true)
if [[ -n "$packages" ]]; then
  # Convert newline-separated list to array
  mapfile -t package_array < <(echo "$packages" | grep -v '^$')
  
  if [[ ${#package_array[@]} -gt 0 ]]; then
    LOG "Found ${#package_array[@]} packages to install"
    LOG "Package list: ${package_array[*]}"
    LOG "--- PACMAN OUTPUT START ---"
    pacman_output=$(sudo pacman -S --noconfirm --needed "${package_array[@]}" 2>&1)
    pacman_exit=$?
    echo "$pacman_output" | while IFS= read -r line; do
      echo "[$(TIMESTAMP)] post-install/prebuild.sh: PACMAN: $line" >> "$PREBUILD_LOG_FILE" 2>&1 || true
    done
    LOG "--- PACMAN OUTPUT END ---"
    LOG "Pacman exit code: $pacman_exit"
    if [ $pacman_exit -ne 0 ]; then
      LOG_ERROR "Some packages failed to install (exit code: $pacman_exit)"
      LOG_ERROR "Full pacman output logged to $PREBUILD_LOG_FILE"
    else
      LOG "All packages installed successfully"
    fi
  else
    LOG "No packages found in index.json"
  fi
else
  LOG "No packages section found in index.json"
fi

# Deploy files
LOG "Deploying configuration files"

deployment_count=$(jq '.deployments | length' "$INDEX_FILE" 2>/dev/null || echo "0")
LOG "Found $deployment_count deployments in index.json"
if [[ "$deployment_count" -eq 0 ]]; then
  LOG "No deployments found in index.json"
  return 0
fi

deployed=0
failed=0

# Process each deployment
for ((i = 0; i < deployment_count; i++)); do
  source_file=$(jq -r ".deployments[$i].source" "$INDEX_FILE" 2>/dev/null)
  dest_path=$(jq -r ".deployments[$i].destination" "$INDEX_FILE" 2>/dev/null)
  permissions=$(jq -r ".deployments[$i].permissions // \"644\"" "$INDEX_FILE" 2>/dev/null)
  
  # Skip if source or destination is null or empty
  if [[ -z "$source_file" || "$source_file" == "null" ]] || [[ -z "$dest_path" || "$dest_path" == "null" ]]; then
    continue
  fi
  
  # Expand destination path
  dest_path=$(expand_path "$dest_path")
  
  # Build full source path
  source_path="${PREBUILD_DIR}/${source_file}"
  
  LOG "Processing deployment [$((i+1))/$deployment_count]: $source_file -> $dest_path"
  
  # Check if source file exists
  if [[ ! -f "$source_path" ]]; then
    LOG_ERROR "Source file not found: $source_path"
    ((failed++)) || true
    continue
  fi
  
  LOG "Source file exists: $source_path"
  
  # Create destination directory if needed
  dest_dir=$(dirname "$dest_path")
  if [[ ! -d "$dest_dir" ]]; then
    LOG "Creating directory: $dest_dir"
    mkdir_output=$(mkdir -p "$dest_dir" 2>&1)
    if [ $? -eq 0 ]; then
      LOG "Directory created successfully"
    else
      LOG_ERROR "Failed to create directory: $mkdir_output"
    fi
  else
    LOG "Destination directory exists: $dest_dir"
  fi
  
  # Backup existing file if it exists
  if [[ -f "$dest_path" ]]; then
    backup_path="${dest_path}.backup"
    LOG "Backing up existing file: $dest_path -> $backup_path"
    cp_output=$(cp "$dest_path" "$backup_path" 2>&1)
    if [ $? -eq 0 ]; then
      LOG "Backup created successfully"
    else
      LOG_ERROR "Failed to create backup: $cp_output"
    fi
  fi
  
  # Copy file
  LOG "Copying file: $source_path -> $dest_path"
  cp_output=$(cp "$source_path" "$dest_path" 2>&1)
  cp_exit=$?
  if [ $cp_exit -eq 0 ]; then
    # Set permissions
    chmod_output=$(chmod "$permissions" "$dest_path" 2>&1)
    if [ $? -ne 0 ]; then
      LOG_ERROR "Failed to set permissions: $chmod_output"
    else
      LOG "Permissions set to $permissions"
    fi
    
    # Set ownership to user if in chroot context
    if [[ -n "${OMARCHY_USER:-}" ]]; then
      chown_output=$(chown "$OMARCHY_USER:$OMARCHY_USER" "$dest_path" 2>&1)
      if [ $? -ne 0 ]; then
        LOG_ERROR "Failed to set ownership: $chown_output"
      else
        LOG "Ownership set to $OMARCHY_USER:$OMARCHY_USER"
      fi
    fi
    
    LOG "Deployed successfully: $source_file -> $dest_path (perms: $permissions)"
    ((deployed++)) || true
  else
    LOG_ERROR "Failed to deploy: $source_file -> $dest_path"
    LOG_ERROR "Copy output: $cp_output"
    ((failed++)) || true
  fi
done

LOG "=== PREBUILD.SH COMPLETED ==="
LOG "Deployment summary: $deployed deployed, $failed failed"

if [[ $failed -gt 0 ]]; then
  LOG_ERROR "Some files failed to deploy"
  return 1
fi

LOG "All deployments completed successfully"
return 0

