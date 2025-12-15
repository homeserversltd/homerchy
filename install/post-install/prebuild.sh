#!/bin/bash
# Deploy prebuild configuration files based on index.json manifest

set -euo pipefail

# Determine prebuild directory location
PREBUILD_DIR="${OMARCHY_PATH}/prebuild"
INDEX_FILE="${PREBUILD_DIR}/index.json"

# Check if prebuild directory exists
if [[ ! -d "$PREBUILD_DIR" ]]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] prebuild: Prebuild directory not found: $PREBUILD_DIR"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] prebuild: Skipping prebuild deployment"
  return 0
fi

# Check if index.json exists
if [[ ! -f "$INDEX_FILE" ]]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] prebuild: index.json not found: $INDEX_FILE"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] prebuild: Skipping prebuild deployment"
  return 0
fi

# Check if jq is available
if ! command -v jq &>/dev/null; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] prebuild: ERROR: jq is required but not found"
  return 1
fi

# Validate JSON syntax
if ! jq empty "$INDEX_FILE" 2>/dev/null; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] prebuild: ERROR: Invalid JSON syntax in $INDEX_FILE"
  return 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] prebuild: Starting prebuild deployment"

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
echo "[$(date '+%Y-%m-%d %H:%M:%S')] prebuild: Installing prerequisite packages"

packages=$(jq -r '.packages[]?' "$INDEX_FILE" 2>/dev/null || true)
if [[ -n "$packages" ]]; then
  # Convert newline-separated list to array
  mapfile -t package_array < <(echo "$packages" | grep -v '^$')
  
  if [[ ${#package_array[@]} -gt 0 ]]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] prebuild: Installing packages: ${package_array[*]}"
    sudo pacman -S --noconfirm --needed "${package_array[@]}" || {
      echo "[$(date '+%Y-%m-%d %H:%M:%S')] prebuild: WARNING: Some packages failed to install"
    }
  fi
fi

# Deploy files
echo "[$(date '+%Y-%m-%d %H:%M:%S')] prebuild: Deploying configuration files"

deployment_count=$(jq '.deployments | length' "$INDEX_FILE" 2>/dev/null || echo "0")
if [[ "$deployment_count" -eq 0 ]]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] prebuild: No deployments found in index.json"
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
  
  # Check if source file exists
  if [[ ! -f "$source_path" ]]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] prebuild: WARNING: Source file not found: $source_path"
    ((failed++)) || true
    continue
  fi
  
  # Create destination directory if needed
  dest_dir=$(dirname "$dest_path")
  if [[ ! -d "$dest_dir" ]]; then
    mkdir -p "$dest_dir"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] prebuild: Created directory: $dest_dir"
  fi
  
  # Backup existing file if it exists
  if [[ -f "$dest_path" ]]; then
    backup_path="${dest_path}.backup"
    cp "$dest_path" "$backup_path" 2>/dev/null || true
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] prebuild: Backed up existing file: $dest_path -> $backup_path"
  fi
  
  # Copy file
  if cp "$source_path" "$dest_path" 2>/dev/null; then
    # Set permissions
    chmod "$permissions" "$dest_path" 2>/dev/null || true
    
    # Set ownership to user if in chroot context
    if [[ -n "${OMARCHY_USER:-}" ]]; then
      chown "$OMARCHY_USER:$OMARCHY_USER" "$dest_path" 2>/dev/null || true
    fi
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] prebuild: Deployed: $source_file -> $dest_path (perms: $permissions)"
    ((deployed++)) || true
  else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] prebuild: ERROR: Failed to deploy: $source_file -> $dest_path"
    ((failed++)) || true
  fi
done

echo "[$(date '+%Y-%m-%d %H:%M:%S')] prebuild: Deployment complete - $deployed deployed, $failed failed"

if [[ $failed -gt 0 ]]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] prebuild: WARNING: Some files failed to deploy"
  return 1
fi

return 0

