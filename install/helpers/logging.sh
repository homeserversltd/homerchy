start_log_output() {
  local ANSI_RESET="\033[0m"
  local ANSI_GRAY="\033[90m"
  local max_line_width=$((LOGO_WIDTH - 4))

  (
    local last_position=0
    local last_inode=0
    
    while true; do
      if [ -f "$OMARCHY_INSTALL_LOG_FILE" ]; then
        # Get current file size and inode to detect file rotation/recreation
        current_size=$(stat -c%s "$OMARCHY_INSTALL_LOG_FILE" 2>/dev/null || echo 0)
        current_inode=$(stat -c%i "$OMARCHY_INSTALL_LOG_FILE" 2>/dev/null || echo 0)
        
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
          new_content=$(tail -c +$((last_position + 1)) "$OMARCHY_INSTALL_LOG_FILE" 2>/dev/null)
          
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
    kill "$monitor_pid" 2>/dev/null || true
    wait "$monitor_pid" 2>/dev/null || true
    unset monitor_pid
  fi
}

start_install_log() {
  sudo touch "$OMARCHY_INSTALL_LOG_FILE"
  sudo chmod 666 "$OMARCHY_INSTALL_LOG_FILE"

  export OMARCHY_START_TIME=$(date '+%Y-%m-%d %H:%M:%S')

  echo "=== Omarchy Installation Started: $OMARCHY_START_TIME ===" >>"$OMARCHY_INSTALL_LOG_FILE"
  start_log_output
}

stop_install_log() {
  stop_log_output
  show_cursor

  if [[ -n ${OMARCHY_INSTALL_LOG_FILE:-} ]]; then
    OMARCHY_END_TIME=$(date '+%Y-%m-%d %H:%M:%S')
    echo "=== Omarchy Installation Completed: $OMARCHY_END_TIME ===" >>"$OMARCHY_INSTALL_LOG_FILE"
    echo "" >>"$OMARCHY_INSTALL_LOG_FILE"
    echo "=== Installation Time Summary ===" >>"$OMARCHY_INSTALL_LOG_FILE"

    if [ -f "/var/log/archinstall/install.log" ]; then
      ARCHINSTALL_START=$(grep -m1 '^\[' /var/log/archinstall/install.log 2>/dev/null | sed 's/^\[\([^]]*\)\].*/\1/' || true)
      ARCHINSTALL_END=$(grep 'Installation completed without any errors' /var/log/archinstall/install.log 2>/dev/null | sed 's/^\[\([^]]*\)\].*/\1/' || true)

      if [ -n "$ARCHINSTALL_START" ] && [ -n "$ARCHINSTALL_END" ]; then
        ARCH_START_EPOCH=$(date -d "$ARCHINSTALL_START" +%s)
        ARCH_END_EPOCH=$(date -d "$ARCHINSTALL_END" +%s)
        ARCH_DURATION=$((ARCH_END_EPOCH - ARCH_START_EPOCH))

        ARCH_MINS=$((ARCH_DURATION / 60))
        ARCH_SECS=$((ARCH_DURATION % 60))

        echo "Archinstall: ${ARCH_MINS}m ${ARCH_SECS}s" >>"$OMARCHY_INSTALL_LOG_FILE"
      fi
    fi

    if [ -n "$OMARCHY_START_TIME" ]; then
      OMARCHY_START_EPOCH=$(date -d "$OMARCHY_START_TIME" +%s)
      OMARCHY_END_EPOCH=$(date -d "$OMARCHY_END_TIME" +%s)
      OMARCHY_DURATION=$((OMARCHY_END_EPOCH - OMARCHY_START_EPOCH))

      OMARCHY_MINS=$((OMARCHY_DURATION / 60))
      OMARCHY_SECS=$((OMARCHY_DURATION % 60))

      echo "Omarchy:     ${OMARCHY_MINS}m ${OMARCHY_SECS}s" >>"$OMARCHY_INSTALL_LOG_FILE"

      if [ -n "$ARCH_DURATION" ]; then
        TOTAL_DURATION=$((ARCH_DURATION + OMARCHY_DURATION))
        TOTAL_MINS=$((TOTAL_DURATION / 60))
        TOTAL_SECS=$((TOTAL_DURATION % 60))
        echo "Total:       ${TOTAL_MINS}m ${TOTAL_SECS}s" >>"$OMARCHY_INSTALL_LOG_FILE"
      fi
    fi
    echo "=================================" >>"$OMARCHY_INSTALL_LOG_FILE"

    echo "Rebooting system..." >>"$OMARCHY_INSTALL_LOG_FILE"
  fi
}

run_logged() {
  local script="$1"

  export CURRENT_SCRIPT="$script"

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting: $script" >>"$OMARCHY_INSTALL_LOG_FILE"

  # Use bash -c to create a clean subshell
  bash -c "source '$script'" </dev/null >>"$OMARCHY_INSTALL_LOG_FILE" 2>&1

  local exit_code=$?

  if [ $exit_code -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Completed: $script" >>"$OMARCHY_INSTALL_LOG_FILE"
    unset CURRENT_SCRIPT
  else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Failed: $script (exit code: $exit_code)" >>"$OMARCHY_INSTALL_LOG_FILE"
  fi

  return $exit_code
}
