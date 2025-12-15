# Current Work & Struggles

## What We're Working On

Fixing logging issues in the Homerchy installation system. The installation log file (`/var/log/omarchy-install.log`) is missing logs from packaging, config, and login phases - only post-install logs appear.

## The Problem

After installation completes, `/var/log/omarchy-install.log` only contains:
- Post-install script entries (pacman.sh, prebuild.sh, allow-reboot.sh, ssh.sh)
- Installation completion summary
- **MISSING**: All packaging scripts (base.sh, fonts.sh, etc.)
- **MISSING**: All config scripts
- **MISSING**: All login scripts
- **MISSING**: Preflight scripts (except they run before logging starts)

## What We've Discovered

1. **Two separate log files exist**:
   - Live ISO log: `/var/log/omarchy-install.log` on the live ISO (lost after reboot)
   - Installed system log: `/var/log/omarchy-install.log` inside chroot (`/mnt/var/log/omarchy-install.log` from host)

2. **Execution flow**:
   - `.automated_script.sh` runs on ISO boot, creates log file, runs archinstall
   - Then runs `install_omarchy()` which executes `install.sh` INSIDE a chroot
   - Inside chroot, `install.sh` sources all the phase scripts (preflight, packaging, config, login, post-install)
   - `start_install_log()` is called INSIDE the chroot in `preflight/begin.sh`
   - All scripts use `run_logged()` which should write to the log file

3. **The issue**: During chroot install, logs are either:
   - NOT being written to `/var/log/omarchy-install.log` at all, OR
   - That file is being CLEARED/TRUNCATED before we see the final result

## What We've Tried (That Didn't Work)

1. Removed manual log redirects from `prebuild.sh` and `base.sh` - scripts now output to stdout/stderr
2. Changed `allow-reboot.sh` to use `run_logged()` instead of `source`
3. Fixed `monitor_pid` scope issue in `stop_log_output()` to stop log viewer properly
4. Added SSH enablement for VM environments
5. Fixed `prebuild.sh` to install `jq` if missing instead of failing
6. Restored `finished.sh` from original omarchy repo

## Current Struggles

1. **Can't figure out why base.sh logs are missing**: `base.sh` runs via `run_logged()` which should write to the log file, but nothing appears

2. **Log file truncation mystery**: The log file only shows post-install entries, suggesting earlier logs are being cleared or not written

3. **Two log files confusion**: Understanding which log file is which and when they're written to

4. **Chroot logging**: Need to understand if logs written inside chroot are actually persisting to the installed system's `/var/log/omarchy-install.log`

## Next Steps Needed

1. Trace exactly where the log file is being written during chroot install
2. Check if `start_install_log()` inside chroot is clearing/truncating the file
3. Verify that `run_logged()` is actually writing during packaging/config/login phases
4. Understand the relationship between the live ISO log and the installed system log

## Recent Fixes Applied

1. **Enhanced `start_install_log()`**: Added error handling and directory creation to ensure log file is created properly
2. **Enhanced `run_logged()`**: Added check to ensure log file exists before writing, with automatic creation if missing
3. **Added path verification in `install.sh`**: Added check to ensure installation directory exists before proceeding
4. **Fixed VM disk size**: Increased from 40GB to 100GB to prevent "No space left on device" errors
5. **Updated VM launch script**: Now always deletes and recreates disk file for clean test runs

## Root Cause Found

**The actual problem was disk space, not logging code!**

During testing, we discovered:
- VM disk was only 40GB, which filled up during installation
- This caused "No space left on device" errors when trying to write to `/var/log/omarchy-install.log`
- All the `run_logged()` calls were failing silently because the disk was full
- This is why `base.sh` and other packaging scripts weren't appearing in logs - they were running but couldn't write to the log file

**Evidence:**
- Multiple "ERROR: Failed to write to log file" messages
- "echo: write error: No space left on device" errors in logging.sh
- `grep -i "base.sh"` returned no results because nothing was being written
- Only post-install entries appeared because they ran after the disk filled up

**Solution:**
- Increased VM disk size to 100GB
- Updated launch script to always create fresh disk (ensures clean test environment)
- The logging fixes we made are still valuable for better error handling, but the primary issue was disk space

## SSH Access to VM

### Setup
SSH is automatically enabled during installation if running in a VM environment. The `install/post-install/ssh.sh` script:
- Detects VM environment (checks for `OMARCHY_VM_TEST` env var or `/root/vm-env.sh` file, falls back to `systemd-detect-virt`)
- Enables `sshd` service to start on boot
- Starts SSH service immediately

### Port Forwarding
The VM launch script (`vmtools/launch-iso.sh`) sets up port forwarding:
- Host port `2222` forwards to guest port `22` (SSH)
- Configured via: `-netdev user,id=net0,hostfwd=tcp::2222-:22`

### Connection Details
After installation completes, SSH into the VM from the host machine:

```bash
ssh -p 2222 owner@localhost
```

**Credentials** (from `vmtools/settings.json`):
- Username: `owner`
- Password: `123`

### Notes
- SSH is only enabled in VM environments (not on physical hardware installations)
- The port forwarding is configured in the QEMU launch script, so it's available as soon as the VM boots
- SSH service starts automatically during the post-install phase

## Documentation

- Execution flow documented in: `docs/memories/solved/initialization.md`
