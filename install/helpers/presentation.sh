# Ensure we have gum available
if ! command -v gum &>/dev/null; then
  sudo pacman -S --needed --noconfirm gum
fi

# Get terminal size from /dev/tty (works in all scenarios: direct, sourced, or piped)
if [ -e /dev/tty ]; then
  TERM_SIZE=$(stty size 2>/dev/null </dev/tty)

  if [ -n "$TERM_SIZE" ]; then
    export TERM_HEIGHT=$(echo "$TERM_SIZE" | cut -d' ' -f1)
    export TERM_WIDTH=$(echo "$TERM_SIZE" | cut -d' ' -f2)
  else
    # Fallback to reasonable defaults if stty fails
    export TERM_WIDTH=80
    export TERM_HEIGHT=24
  fi
else
  # No terminal available (e.g., non-interactive environment)
  export TERM_WIDTH=80
  export TERM_HEIGHT=24
fi

export LOGO_PATH="$OMARCHY_PATH/logo.txt"
export LOGO_WIDTH=$(awk '{ if (length > max) max = length } END { print max+0 }' "$LOGO_PATH" 2>/dev/null || echo 0)
export LOGO_HEIGHT=$(wc -l <"$LOGO_PATH" 2>/dev/null || echo 0)

export PADDING_LEFT=$((($TERM_WIDTH - $LOGO_WIDTH) / 2))
export PADDING_LEFT_SPACES=$(printf "%*s" $PADDING_LEFT "")

# Tokyo Night theme for gum confirm
export GUM_CONFIRM_PROMPT_FOREGROUND="6"     # Cyan for prompt
export GUM_CONFIRM_SELECTED_FOREGROUND="0"   # Black text on selected
export GUM_CONFIRM_SELECTED_BACKGROUND="2"   # Green background for selected
export GUM_CONFIRM_UNSELECTED_FOREGROUND="7" # White for unselected
export GUM_CONFIRM_UNSELECTED_BACKGROUND="0" # Black background for unselected
export PADDING="0 0 0 $PADDING_LEFT"         # Gum Style
export GUM_CHOOSE_PADDING="$PADDING"
export GUM_FILTER_PADDING="$PADDING"
export GUM_INPUT_PADDING="$PADDING"
export GUM_SPIN_PADDING="$PADDING"
export GUM_TABLE_PADDING="$PADDING"
export GUM_CONFIRM_PADDING="$PADDING"

# Detect if we're running in a VM (QEMU, VirtualBox, etc.)
# ANSI escape sequences often don't work well in VM consoles
is_vm_environment() {
  # Check DMI system vendor/product for common VM indicators
  if [ -f /sys/class/dmi/id/sys_vendor ]; then
    local vendor=$(cat /sys/class/dmi/id/sys_vendor 2>/dev/null | tr '[:upper:]' '[:lower:]')
    case "$vendor" in
      *qemu*|*kvm*|*vmware*|*virtualbox*|*microsoft*|*xen*)
        return 0
        ;;
    esac
  fi
  
  # Check for virtio devices (common in QEMU/KVM)
  if [ -d /sys/bus/virtio ]; then
    local virtio_count=$(find /sys/bus/virtio/devices -mindepth 1 -maxdepth 1 2>/dev/null | wc -l)
    if [ "$virtio_count" -gt 2 ]; then
      return 0
    fi
  fi
  
  # Check if TERM is set to something that doesn't support ANSI well
  case "${TERM:-}" in
    linux|vt220|dumb)
      return 0
      ;;
  esac
  
  return 1
}

clear_logo() {
  if is_vm_environment; then
    # Simple clear for VM environments
    clear
    echo
    cat "$LOGO_PATH"
    echo
  else
    # ANSI-based clear for real hardware
    printf "\033[H\033[2J" # Clear screen and move cursor to top-left
    gum style --foreground 2 --padding "1 0 0 $PADDING_LEFT" "$(<"$LOGO_PATH")"
  fi
}
