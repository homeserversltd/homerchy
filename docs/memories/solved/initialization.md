# Installation Flow and Logging

## Execution Flow

### Phase 1: ISO Boot (Live System)
1. **`.automated_script.sh`** runs on `/dev/tty1` (line 234)
   - Creates `/var/log/omarchy-install.log` on **LIVE ISO system** (line 236)
   - Writes initial header: "=== Omarchy Installation Started" (line 241)
   - Sets `OMARCHY_INSTALL_LOG_FILE="/var/log/omarchy-install.log"` (line 249)
   - Calls `start_install_log()` which writes header **AGAIN** (line 257)
   - Runs `install_arch()` - archinstall base system (line 271)
   - Runs `install_omarchy()` which does:
     ```bash
     chroot_bash -lc "source /home/$OMARCHY_USER/.local/share/omarchy/install.sh || bash"
     ```
     - This runs `install.sh` **INSIDE THE CHROOT** (line 82)

### Phase 2: Inside Chroot (Installed System)
2. **`install.sh`** runs inside chroot (sourced from `.automated_script.sh` line 82)
   - Sets `OMARCHY_INSTALL_LOG_FILE="/var/log/omarchy-install.log"` (line 9)
   - **CRITICAL**: Inside chroot, `/var/log/omarchy-install.log` = `/mnt/var/log/omarchy-install.log` from host
   - Sources `helpers/all.sh` (loads logging functions)
   - Sources `preflight/all.sh`:
     - Sources `preflight/begin.sh` which calls `start_install_log()` **AGAIN** (line 4)
     - This writes to `/var/log/omarchy-install.log` **INSIDE CHROOT**
   - Sources `packaging/all.sh`:
     - Calls `run_logged $OMARCHY_INSTALL/packaging/base.sh`
     - `run_logged()` writes "Starting: ..." and script output to log file
   - Sources `config/all.sh` (all scripts via `run_logged()`)
   - Sources `login/all.sh` (all scripts via `run_logged()`)
   - Sources `post-install/all.sh` (all scripts via `run_logged()`)

## Logging Problem

**THE ISSUE**: During chroot install, logs are either:
1. **NOT being written to `/var/log/omarchy-install.log` at all**, OR
2. **That file is being CLEARED/TRUNCATED** before we see the final result

**What happens**:
1. `.automated_script.sh` creates `/var/log/omarchy-install.log` on LIVE ISO (line 236)
2. `.automated_script.sh` runs `install_omarchy()` which does:
   ```bash
   chroot_bash -lc "source /home/$OMARCHY_USER/.local/share/omarchy/install.sh || bash"
   ```
   - When `OMARCHY_DEBUG` is NOT set (normal case), output is **NOT redirected** to log file (line 84)
   - Output goes to stdout/stderr, not captured
3. Inside chroot, `install.sh` runs:
   - Calls `start_install_log()` in `preflight/begin.sh` (line 4)
   - `start_install_log()` does `sudo touch "$OMARCHY_INSTALL_LOG_FILE"` (line 66)
   - This creates/updates `/var/log/omarchy-install.log` **INSIDE THE CHROOT**
   - This is `/mnt/var/log/omarchy-install.log` from host perspective
   - **This is a DIFFERENT FILE** than the live ISO log

**Why base.sh logs are missing**:
- `base.sh` runs via `run_logged()` which writes to `$OMARCHY_INSTALL_LOG_FILE`
- But `run_logged()` writes INSIDE the chroot to `/var/log/omarchy-install.log`
- The file shown after installation only has post-install entries
- **This means either**:
  - Logs during packaging/config/login phases aren't being written
  - The log file is being cleared/truncated somewhere between those phases and post-install
  - The log file path is wrong or not accessible during those phases

## Key Functions

- `start_install_log()`: Creates log file, writes header, starts log viewer background process
- `run_logged(script)`: Writes "Starting: script", runs script with output redirected to log, writes "Completed/Failed: script"
- `stop_install_log()`: Stops log viewer, writes completion summary

## Critical Path

```
ISO Boot
  → .automated_script.sh (writes to LIVE ISO log)
    → install_arch() (archinstall)
    → install_omarchy()
      → chroot_bash runs install.sh INSIDE CHROOT
        → install.sh (writes to INSTALLED SYSTEM log)
          → preflight/all.sh → start_install_log() called AGAIN
          → packaging/all.sh → base.sh via run_logged()
          → config/all.sh → scripts via run_logged()
          → login/all.sh → scripts via run_logged()
          → post-install/all.sh → scripts via run_logged()
```

## Log File Locations

**Two separate log files are now used:**

1. **`/var/log/omarchy-preinstall.log`**:
   - Created by `.automated_script.sh` on live ISO (line 236)
   - Used during: preflight, packaging, config, login phases
   - Written to inside chroot (accessible at `/mnt/var/log/omarchy-preinstall.log` from host)
   - Contains: base.sh, all packaging/config/login scripts

2. **`/var/log/omarchy-postinstall.log`**:
   - Created by `start_postinstall_log()` at start of `post-install/all.sh`
   - Used during: post-install phase only
   - Contains: pacman.sh, prebuild.sh, ssh.sh, allow-reboot.sh logs
   - Contains: Installation time summary combining both phases

**After installation**: Both log files exist on the installed system at:
- `/var/log/omarchy-preinstall.log`
- `/var/log/omarchy-postinstall.log`
