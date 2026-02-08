# First-Boot TTY Blocking & Marker File System

Reference for Homerchy first-boot install TTY behavior. Co-located in homerchy root; see also `deployment/ADD_BACK_CHECKLIST.md` for install.py add-back history.

**Current architecture (2025):** ExecStartPre getty blocking was *removed* to prevent stuck boot when service fails to spawn. install.py blocks TTY in main() via `block_tty_and_display_message()`; ExecStopPost restores gettys on any service exit (success, failure, crash).

---

## Overview

This document explains how HOMERCHY successfully blocks TTY login during first-boot installation and how the marker file system ensures installation only runs once.

## The Problem

During first-boot installation, TTY login prompts were appearing, allowing users to log in while the system was still configuring. This created several issues:

1. **User could interrupt installation** by logging in during configuration
2. **Systemd was re-enabling getty services** even after we blocked them
3. **No way to display persistent messages** during installation
4. **Installation would reboot immediately** without allowing log review

## The Solution: Three-Layer TTY Blocking

### Layer 1: Systemd Service Pre-Start Blocking (OBSOLETE)

**Note:** This layer was removed. ExecStartPre getty masking caused stuck boot when ExecStart failed to spawn (ExecStartPost does not run). We now rely on install.py to block TTY in main().

### Layer 2: Install.py Persistent Blocking

When `install.py` starts, it immediately blocks TTY and starts a background thread to continuously refresh the installation message:

```python
def block_tty_and_display_message():
    """Block TTY login and display persistent installation message."""
    # Stop, mask, and disable all getty services
    for tty_num in range(1, 7):
        subprocess.run(['systemctl', 'stop', f'getty@tty{tty_num}.service'], ...)
        subprocess.run(['systemctl', 'mask', f'getty@tty{tty_num}.service'], ...)
        subprocess.run(['systemctl', 'disable', f'getty@tty{tty_num}.service'], ...)
    
    # Switch to TTY1 and display message
    subprocess.run(['chvt', '1'], ...)
    display_persistent_message()

def persistent_message_loop():
    """Background thread that continuously refreshes the installation message."""
    while True:
        display_persistent_message()
        time.sleep(5)  # Refresh every 5 seconds
```

**Key Features:**
- **Redundant blocking**: Even if systemd service fails, install.py blocks TTY
- **Persistent message**: Red "HOMERCHY INSTALLATION IN PROGRESS" message stays visible
- **Background refresh**: Thread refreshes message every 5 seconds to prevent overwriting
- **Dual output**: Writes to both `/dev/tty1` and `/dev/console` for maximum visibility

### Layer 3: Completion TUI Direct Capture (post-install, to implement)

At installation completion, `completion_tui.py` (in post-install) will capture TTY directly in raw mode.

## The Marker File System: First-Boot Detection

### How It Works

The marker file system ensures installation **only runs once** on first boot:

#### 1. Marker File Creation (During ISO Installation)

During ISO installation, `.automated_script.py` creates a marker file:

```python
# Create marker file to indicate Homerchy installation is needed
install_marker = Path('/mnt/var/lib/homerchy-install-needed')
install_marker.parent.mkdir(parents=True, exist_ok=True)
install_marker.touch()
```

**Location**: `/var/lib/homerchy-install-needed`
- Created in the **installed system** (not ISO)
- Empty file - just a flag
- Persists across reboots (in `/var/lib` which is on root filesystem)

#### 2. Systemd Service Condition

The systemd service **only runs if the marker file exists**:

```systemd
[Unit]
# Only run if marker file exists AND root filesystem is mounted
ConditionPathExists=/var/lib/homerchy-install-needed
ConditionPathIsMountPoint=/
```

#### 3. Marker File Removal

The marker file is removed in ExecStartPost (on success) and ExecStopPost (on any exit).

#### 4. Cleanup on Failure

ExecStopPost runs even when service fails to start; it removes marker and restores gettys.

### Complete First-Boot Flow

```
1. ISO Installation (archinstall)
   └─> Creates /var/lib/homerchy-install-needed marker file
   └─> Creates and enables homerchy.service
   └─> Reboots into installed system

2. First Boot
   └─> System boots normally
   └─> Systemd reaches multi-user.target
   └─> Checks ConditionPathExists=/var/lib/homerchy-install-needed
   └─> ✅ Marker exists → Service starts
   └─> ExecStart: Runs install.py (no ExecStartPre getty block)
   └─> install.py: Blocks TTY in main(), starts message refresh thread
   └─> install.py: Runs orchestrator (preflight, packaging, config, login, first-run, display-test, hacker-demo, post-install)
   └─> Completion TUI (post-install): Will show congratulations, wait for Enter when implemented
   └─> ExecStartPost/ExecStopPost: Removes marker, restores gettys

3. Second Boot (and all subsequent boots)
   └─> Marker doesn't exist → Service does NOT start
   └─> Normal boot continues, TTY login available
```

## File Locations

### Marker File
- **Path**: `/var/lib/homerchy-install-needed`
- **Created**: During ISO installation (in `.automated_script.py`)
- **Removed**: In systemd service ExecStartPost and ExecStopPost
- **Purpose**: Flag to indicate first-boot installation needed

### Systemd Service
- **Path**: `/etc/systemd/system/homerchy.service`
- **Created**: During ISO installation (in `.automated_script.py`)
- **Enabled**: During ISO installation (systemctl enable)
- **Runs**: Only if marker file exists

### Installation Scripts
- **Main entry**: `/home/{user}/.local/share/homerchy/install.py`
- **Orchestrator**: `/home/{user}/.local/share/homerchy/install/index.py`
- **Completion TUI**: Will be in post-install (completion_tui.py, finished.py) when implemented

## Testing & Verification

### Verify Marker File System

```bash
# Check if marker file exists (should only exist before first boot)
ls -l /var/lib/homerchy-install-needed

# Check service status
systemctl status homerchy.service

# Check service conditions
systemctl show homerchy.service | grep Condition
```

### Verify TTY Blocking

```bash
# Check getty service status (should be inactive, masked, disabled during install)
systemctl status getty@tty1.service
systemctl is-enabled getty@tty1.service  # Should show "masked" or "disabled"

# Check if getty is running (should show nothing during install)
ps aux | grep getty
```

## Troubleshooting

### Service Not Starting

**Check:**
- Marker file exists: `ls /var/lib/homerchy-install-needed`
- Service enabled: `systemctl is-enabled homerchy.service`
- Service conditions: `systemctl show homerchy.service | grep Condition`

### Stuck Without Login Prompt

ExecStopPost should restore gettys. If stuck, boot from ISO/live USB and check:
```bash
journalctl -u homerchy.service -b
```

### Reboot Loop

**Cause**: Marker file not removed before reboot

**Fix**: Marker should be removed in ExecStopPost. Check service logs:
```bash
journalctl -u homerchy.service
```

## TUI Methods: Current Architecture

- **During installation**: `install.py` + `reporting.py` own the display. Direct TTY write to `/dev/tty1` and `/dev/console` with ANSI escape codes. Background refresh loop. Status: ✅ **WORKING**.
- **Completion TUI**: Will live in **post-install** (e.g. completion_tui.py, finished.py) when implemented. Not in display-test.

The display-test phase is now a stub (pass); main + reporting handle all display.

## Summary

The first-boot TTY blocking system uses:

1. **Marker file** (`/var/lib/homerchy-install-needed`) to ensure installation only runs once
2. **TTY blocking** in install.py main() (ExecStartPre getty masking removed to prevent stuck boot on failure)
3. **ExecStopPost** to unmask/start gettys on any service exit (success, failure, or crash)
4. **Persistent message refresh** via reporting.redraw() and state.recent_logs
