start_log_output() {
  local ANSI_RESET="\033[0m"
  local ANSI_GRAY="\033[90m"
  local max_line_width=$((LOGO_WIDTH - 4))

  (
    local last_position=0
    local last_inode=0
    
    while true; do
      if [ -f "$HOMERCHY_INSTALL_LOG_FILE" ]; then
        # Get current file size and inode to detect file rotation/recreation
        current_size=$(stat -c%s "$HOMERCHY_INSTALL_LOG_FILE" 2>/dev/null || echo 0)
        current_inode=$(stat -c%i "$HOMERCHY_INSTALL_LOG_FILE" 2>/dev/null || echo 0)
        
        # Reset position if file was recreated (different inode)
        if [ "$current_inode" != "$last_inode" ] && [ "$last_inode" != "0" ]; then
          last_position=0
        fi
        last_inode=$current_inode
        
        # Only read new content since last position
        if [ "$current_size" -gt "$last_position" ]; then
          # Read new content, ensuring we start at a line boundary
          # Skip partial lines by reading from last position and finding first newline
          local new_content
          new_content=$(tail -c +$((last_position + 1)) "$HOMERCHY_INSTALL_LOG_FILE" 2>/dev/null)
          
          # Process only complete lines (skip if we're in the middle of a line)
          if [ -n "$new_content" ]; then
            echo "$new_content" | while IFS= read -r line || [ -n "$line" ]; do
              # Truncate if needed
              if [ ${#line} -gt $max_line_width ]; then
                line="${line:0:$max_line_width}..."
              fi
              
              # Append new line with formatting (only if not empty)
              # Write directly to /dev/tty to avoid interfering with stdout redirection
              if [ -n "$line" ]; then
                printf "${ANSI_GRAY}${PADDING_LEFT_SPACES}  → %s${ANSI_RESET}\n" "$line" >/dev/tty 2>/dev/null || printf "${ANSI_GRAY}${PADDING_LEFT_SPACES}  → %s${ANSI_RESET}\n" "$line"
              fi
            done
            
            # Update position to current file size
            last_position=$current_size
          fi
        fi
      fi
      
      # Check for new content every 0.2 seconds
      sleep 0.2
    done
  ) &
  export monitor_pid=$!
}

stop_log_output() {
  if [ -n "${monitor_pid:-}" ]; then
    kill "$monitor_pid 2>/dev/null || true
    wait $monitor_pid 2>/dev/null || true
    unset monitor_pid
  fi
}

start_deployment/deployment/install_log() {
  # Ensure log directory exists
  local log_dir=$(dirname $HOMERCHY_INSTALL_LOG_FILE)
  if [ ! -d "$log_dir" ]; then
    sudo mkdir -p "$log_dir" || {
      echo "ERROR: Failed to create log directory: $log_dir" >&2
      return 1
    }
  fi

  # Create log file with proper permissions
  sudo touch "$HOMERCHY_INSTALL_LOG_FILE" || {
    echo "ERROR: Failed to create log file: $HOMERCHY_INSTALL_LOG_FILE" >&2
    return 1
  }
  sudo chmod 666 "$HOMERCHY_INSTALL_LOG_FILE" || {
    echo "WARNING: Failed to set log file permissions" >&2
  }

  export HOMERCHY_START_TIME=$(date '+%Y-%m-%d %H:%M:%S')

  # Write initial header - ensure it actually writes
  if ! echo "=== Homerchy Installation Started: $HOMERCHY_START_TIME ===" >>"$HOMERCHY_INSTALL_LOG_FILE 2>&1; then
    echo ERROR: Failed to write to log file: $HOMERCHY_INSTALL_LOG_FILE >&2
    return 1
  fi

  start_log_output
}

stop_deployment/deployment/install_log() {
  stop_log_output
  show_cursor

  if [[ -n ${HOMERCHY_INSTALL_LOG_FILE:-} ]]; then
    HOMERCHY_END_TIME=$(date +%Y-%m-%d %H:%M:%S)
    echo "=== Homerchy Installation Completed: $HOMERCHY_END_TIME ===" >>"$HOMERCHY_INSTALL_LOG_FILE"
    echo "" >>"$HOMERCHY_INSTALL_LOG_FILE"
    echo === Installation Time Summary === >>$HOMERCHY_INSTALL_LOG_FILE

    if [ -f /var/log/archonmachine/deployment/install/onmachine/onmachine/install.log ]; then
      ARCHINSTALL_START=$(grep -m1 ^\[ /var/log/archonmachine/onmachine/install/onmachine/deployment/install.log 2>/dev/null | sed s/^\[\([^]]*\)\].*/\1/ || true)
      ARCHINSTALL_END=$(grep Installation completed without any errors /var/log/archonmachine/deployment/install/onmachine/onmachine/deployment/install.log 2>/dev/null | sed s/^\[\([^]]*\)\].*/\1/ || true)

      if [ -n "$ARCHINSTALL_START" ] && [ -n "$ARCHINSTALL_END" ]; then
        ARCH_START_EPOCH=$(date -d "$ARCHINSTALL_START" +%s)
        ARCH_END_EPOCH=$(date -d $ARCHINSTALL_END +%s)
        ARCH_DURATION=$((ARCH_END_EPOCH - ARCH_START_EPOCH))

        ARCH_MINS=$((ARCH_DURATION / 60))
        ARCH_SECS=$((ARCH_DURATION % 60))

        echo Archdeployment/deployment/install: ${ARCH_MINS}m ${ARCH_SECS}s >>$HOMERCHY_INSTALL_LOG_FILE"
      fi
    fi

    if [ -n "$HOMERCHY_START_TIME" ]; then
      HOMERCHY_START_EPOCH=$(date -d "$HOMERCHY_START_TIME" +%s)
      HOMERCHY_END_EPOCH=$(date -d "$HOMERCHY_END_TIME" +%s)
      HOMERCHY_DURATION=$((HOMERCHY_END_EPOCH - HOMERCHY_START_EPOCH))

      HOMERCHY_MINS=$((HOMERCHY_DURATION / 60))
      HOMERCHY_SECS=$((HOMERCHY_DURATION % 60))

      echo "Homerchy:     ${HOMERCHY_MINS}m ${HOMERCHY_SECS}s" >>"$HOMERCHY_INSTALL_LOG_FILE"

      if [ -n "$ARCH_DURATION" ]; then
        TOTAL_DURATION=$((ARCH_DURATION + HOMERCHY_DURATION))
        TOTAL_MINS=$((TOTAL_DURATION / 60))
        TOTAL_SECS=$((TOTAL_DURATION % 60))
        echo "Total:       ${TOTAL_MINS}m ${TOTAL_SECS}s" >>"$HOMERCHY_INSTALL_LOG_FILE"
      fi
    fi
    echo "=================================" >>"$HOMERCHY_INSTALL_LOG_FILE"

    echo "Rebooting system..." >>"$HOMERCHY_INSTALL_LOG_FILE"
  fi
}

run_logged() {
  local script="$1

  export CURRENT_SCRIPT=$script

  # Use phase-specific log file if set, otherwise use main onmachine/deployment/deployment/install log
  local log_file=${HOMERCHY_PHASE_LOG_FILE:-$HOMERCHY_INSTALL_LOG_FILE}

  # Ensure log file exists before writing
  if [ ! -f "$log_file" ]; then
    echo "ERROR: Log file does not exist: $log_file" >&2
    echo "ERROR: Attempting to create it..." >&2
    sudo touch "$log_file" || {
      echo "ERROR: Failed to create log file: $log_file" >&2
      return 1
    }
    sudo chmod 666 "$log_file" || true
  fi

  # Write start message - ensure it actually writes
  if ! echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting: $script" >>"$log_file" 2>&1; then
    echo "ERROR: Failed to write to log file: $log_file" >&2
    return 1
  fi

  # Use bash -c to create a clean subshell
  bash -c "source '$script'" </dev/null >>"$log_file" 2>&1

  local exit_code=$?

  if [ $exit_code -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Completed: $script" >>"$log_file"
    unset CURRENT_SCRIPT
  else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Failed: $script (exit code: $exit_code)" >>"$log_file"
  fi

  return $exit_code
}