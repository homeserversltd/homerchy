#!/bin/bash

# Hyprland Window Manager Startup Script
# Starts applications and places them on designated monitors
# Based on ~/.config/hypr/envs.conf rules

# Log file for startup output
LOG_FILE="/tmp/startup.txt"

# Configuration file discovery
CONFIG_FILE=""

# Default settings (can be overridden by config)
TIMEOUT=30
CHECK_INTERVAL=0.5
STAGGER_DELAY=0.2
DEBUG_MODE=0

# Function to log output to both console and log file
log_output() {
    echo "$1" | tee -a "$LOG_FILE"
}

# Function to log debug output only when DEBUG=1
debug_log() {
    if [[ "$DEBUG_MODE" == "1" ]]; then
        echo "[DEBUG] $1" | tee -a "$LOG_FILE"
    fi
}

# Function to find configuration file
find_config_file() {
    # Priority order: bin directory, then XDG config directory
    if [[ -f "/home/owner/bin/hyprstarter.conf" ]]; then
        CONFIG_FILE="/home/owner/bin/hyprstarter.conf"
        debug_log "Using config file: $CONFIG_FILE"
    elif [[ -f "$HOME/.config/hypr/hyprstarter.conf" ]]; then
        CONFIG_FILE="$HOME/.config/hypr/hyprstarter.conf"
        debug_log "Using config file: $CONFIG_FILE"
    else
        log_output "No configuration file found. Expected locations:"
        log_output "  - /home/owner/bin/hyprstarter.conf"
        log_output "  - $HOME/.config/hypr/hyprstarter.conf"
        log_output "Exiting gracefully."
        exit 0
    fi
}

# Function to load configuration from JSON
load_config() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_output "Configuration file not found: $CONFIG_FILE"
        exit 1
    fi
    
    # Check if jq is available
    if ! command -v jq &> /dev/null; then
        log_output "ERROR: jq is required to parse JSON configuration but not found"
        log_output "Please install jq: pacman -S jq"
        exit 1
    fi
    
    # Validate JSON syntax
    if ! jq empty "$CONFIG_FILE" 2>/dev/null; then
        log_output "ERROR: Invalid JSON syntax in configuration file: $CONFIG_FILE"
        exit 1
    fi
    
    # Load settings
    TIMEOUT=$(jq -r '.settings.timeout // 30' "$CONFIG_FILE")
    CHECK_INTERVAL=$(jq -r '.settings.check_interval // 0.5' "$CONFIG_FILE")
    STAGGER_DELAY=$(jq -r '.settings.stagger_delay // 0.2' "$CONFIG_FILE")
    DEBUG_MODE=$(jq -r '.settings.debug_mode // false' "$CONFIG_FILE")
    
    debug_log "Loaded settings: timeout=$TIMEOUT, check_interval=$CHECK_INTERVAL, stagger_delay=$STAGGER_DELAY, debug_mode=$DEBUG_MODE"
    
    # Build WINDOW_RULES and STARTUP_APPS arrays from JSON
    while read -r monitor; do
        debug_log "Processing monitor: $monitor"
        while read -r app command; do
            if [[ -n "$app" && -n "$command" ]]; then
                WINDOW_RULES["$app"]="$monitor"
                STARTUP_APPS["$app"]="$command"
                debug_log "Added app: $app -> $monitor (command: $command)"
            fi
        done < <(jq -r ".[\"$monitor\"] | to_entries | .[] | \"\(.key) \(.value)\"" "$CONFIG_FILE" 2>/dev/null)
    done < <(jq -r 'keys[] | select(. != "settings")' "$CONFIG_FILE" 2>/dev/null)
    
    # Check if any applications were configured
    if [[ ${#WINDOW_RULES[@]} -eq 0 ]]; then
        log_output "No applications configured in $CONFIG_FILE"
        log_output "Exiting gracefully."
        exit 0
    fi
    
    debug_log "Configuration loaded: ${#WINDOW_RULES[@]} applications configured"
}

# Dynamic arrays populated from JSON configuration
declare -A WINDOW_RULES
declare -A STARTUP_APPS


# Function to start an application
start_app() {
    local app="$1"
    local command="${STARTUP_APPS[$app]}"
    
    debug_log "Looking up app key: '$app'"
    debug_log "Raw command from array: '$command'"
    
    if [[ -n "$command" ]]; then
        log_output "Starting $app..."
        # Use simple variable expansion (Method 2 from test results)
        # This fixes the critical bug where eval was breaking commands with arguments
        command_expanded="$command"
        debug_log "Expanded command: '$command_expanded'"
        log_output "Command: $command_expanded"
        $command_expanded &
        log_output "App $app started in background"
    else
        debug_log "ERROR: No command found for app '$app' in STARTUP_APPS array"
        log_output "ERROR: No command found for app '$app'"
    fi
}


# Function to monitor and move a specific app window
monitor_and_move_window() {
    local class="$1"
    local monitor="$2"
    local timeout=$TIMEOUT  # Configurable timeout per app
    
    log_output "Starting monitor thread for $class -> $monitor"
    
    local start_time=$(date +%s)
    local found=false
    local check_count=0
    
    while [[ $found == false ]] && [[ $(($(date +%s) - start_time)) -lt $timeout ]]; do
        ((check_count++))
        
        # Get all windows (reduced debug output)
        local all_windows=$(hyprctl clients -j)
        debug_log "Checking for $class windows (total windows: $(echo "$all_windows" | jq length))"
        
        # Check if window exists - get the newest window (highest address)
        local jq_query=".[] | select(.class == \"$class\") | .address" 
        local addresses=$(echo "$all_windows" | jq -r "$jq_query")
        local address_count=$(echo "$addresses" | wc -l)
        
        debug_log "Found $address_count windows matching class '$class'"
        
        if [[ $address_count -gt 1 ]]; then
            debug_log "WARNING: Multiple windows found for class '$class'! Selecting newest (highest address)"
        fi
        
        # Select the newest window (highest address) instead of first one
        local address=$(echo "$addresses" | sort -V | tail -1)
        
        if [[ -n "$address" ]]; then
            log_output "Found window for $class: $address"
            
            # Focus the window
            local focus_result=$(hyprctl dispatch focuswindow address:"$address" 2>&1)
            debug_log "Focus result: $focus_result"
            
            sleep 0.1  # Small delay to ensure focus is set
            
            # Move the window
            local move_result=$(hyprctl dispatch movewindow mon:"$monitor" 2>&1)
            debug_log "Move result: $move_result"
            
            # Add small delay to prevent race conditions when multiple windows move to same monitor
            sleep 0.1
            
            # Verify the window actually moved
            sleep 0.2  # Give it time to move
            local actual_monitor_id=$(hyprctl clients -j | jq -r ".[] | select(.address == \"$address\") | .monitor" | head -1)
            
            # Map monitor names to IDs for verification
            local expected_monitor_id=""
            case "$monitor" in
                "DP-1") expected_monitor_id="0" ;;
                "DP-2") expected_monitor_id="1" ;;
                "HDMI-A-1") expected_monitor_id="2" ;;
                *) expected_monitor_id="$monitor" ;; # Fallback for other monitor names
            esac
            
            debug_log "Window $address is now on monitor ID: '$actual_monitor_id' (expected: '$expected_monitor_id' for '$monitor')"
            
            if [[ "$actual_monitor_id" != "$expected_monitor_id" ]]; then
                debug_log "ERROR: Window did not move to expected monitor! Expected: '$monitor' (ID: $expected_monitor_id), Actual: ID '$actual_monitor_id'"
                log_output "WARNING: Window may not have moved to correct monitor"
            fi
            
            found=true
            log_output "Successfully moved $class to $monitor"
        else
            # Only log every 5th check to reduce verbosity
            if [[ $((check_count % 5)) -eq 0 ]]; then
                debug_log "No window found for class '$class' after $check_count checks"
            fi
            sleep $CHECK_INTERVAL  # Configurable check interval
        fi
    done
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    if [[ $found == false ]]; then
        log_output "Timeout: Could not find window for $class within ${timeout}s"
        debug_log "Thread for $class timed out after ${duration}s and $check_count checks"
    else
        debug_log "Thread for $class completed in ${duration}s after $check_count checks"
    fi
}


# Function to start all applications and place them
startup_workspace() {
    # Initialize log file
    echo "=== Hyprland Window Manager Startup Log - $(date) ===" > "$LOG_FILE"
    log_output "Starting applications in parallel..."
    
    # Debug: Dump array contents (condensed)
    debug_log "DEBUG MODE ENABLED - ${#WINDOW_RULES[@]} apps configured"
    debug_log "Window rules: $(printf '%s->%s ' "${!WINDOW_RULES[@]}" "${WINDOW_RULES[@]}")"
    debug_log "Startup commands: $(printf '%s->%s ' "${!STARTUP_APPS[@]}" "${STARTUP_APPS[@]}")"
    
    # Start all apps with 1-second delays
    local app_count=0
    for app in "${!WINDOW_RULES[@]}"; do
        debug_log "Starting app #$((++app_count)): '$app'"
        start_app "$app"
        
        # Add 1-second delay between app launches (except for the last one)
        if [[ $app_count -lt ${#WINDOW_RULES[@]} ]]; then
            sleep 1
        fi
    done
    
    # Start monitor threads for each app with staggered delays to prevent race conditions
    log_output "Starting parallel monitor threads for window placement..."
    local monitor_pids=()
    local thread_start_time=$(date +%s)
    local delay_counter=0
    
    for app in "${!WINDOW_RULES[@]}"; do
        local monitor="${WINDOW_RULES[$app]}"
        
        # Add staggered delay to prevent race conditions (configurable delay between each thread)
        if [[ $delay_counter -gt 0 ]]; then
            sleep $STAGGER_DELAY
        fi
        
        # Start monitor thread in background
        monitor_and_move_window "$app" "$monitor" &
        local pid=$!
        monitor_pids+=($pid)
        log_output "Started monitor thread (PID: $pid) for $app -> $monitor"
        ((delay_counter++))
    done
    
    # Wait for all monitor threads to complete
    log_output "Waiting for all monitor threads to complete..."
    local completed_count=0
    local total_threads=${#monitor_pids[@]}
    
    for pid in "${monitor_pids[@]}"; do
        local thread_start=$(date +%s)
        wait $pid
        local thread_end=$(date +%s)
        local thread_duration=$((thread_end - thread_start))
        ((completed_count++))
        
        # Find which app this PID was handling
        local app_for_pid="unknown"
        local i=0
        for check_pid in "${monitor_pids[@]}"; do
            if [[ "$check_pid" == "$pid" ]]; then
                local keys_array=($(printf '%s\n' "${!WINDOW_RULES[@]}"))
                app_for_pid="${keys_array[$i]}"
                break
            fi
            ((i++))
        done
        
        log_output "Monitor thread $pid (for $app_for_pid) completed in ${thread_duration}s ($completed_count/$total_threads)"
    done
    
    local total_duration=$(($(date +%s) - thread_start_time))
    log_output "Startup complete! All $completed_count monitor threads finished in ${total_duration}s total."
    log_output "=== Startup completed at $(date) ==="
}

# Function to show help
show_help() {
    log_output "Hyprland Window Manager Startup Script"
    log_output ""
    log_output "Usage: $0 [OPTION]"
    log_output ""
    log_output "Options:"
    log_output "  -h, --help       Show this help message"
    log_output "  --debug, --DEBUG Enable debug mode with verbose logging"
    log_output ""
    log_output "This script starts applications and places them on their designated monitors."
    log_output "All output is logged to: $LOG_FILE"
    log_output ""
    log_output "Usage:"
    log_output "  Normal mode: $0"
    log_output "  Debug mode:  $0 --debug"
    log_output ""
    log_output "Window Rules:"
    for app in "${!WINDOW_RULES[@]}"; do
        log_output "  $app -> ${WINDOW_RULES[$app]}"
    done
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        --debug|--DEBUG)
            DEBUG_MODE=1
            shift
            ;;
        *)
            log_output "Unknown option: $1"
            log_output "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Main script logic
# Find and load configuration
find_config_file
load_config

# Start the workspace
startup_workspace