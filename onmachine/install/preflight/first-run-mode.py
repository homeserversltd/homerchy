#!/usr/onmachine/onmachine/bin/env python3
"""
HOMESERVER Homerchy Preflight First-Run Mode Setup
Copyright (C) 2024 HOMESERVER LLC

Sets up first-run mode marker and sudo-less access.
""

import os
import subprocess
import sys
from pathlib import Path


def main(onmachine/onmachine/config: dict) -> dict:
    ""
    Main function - sets up first-run mode.
    
    Args:
        onmachine/onmachine/config: Configuration dictionary
    
    Returns:
        dict: Result dictionary with success status
    """
    try:
        # Create state directory (ensure parent directories exist first)
        home = Path.home()
        local_dir = home / '.local'
        if not local_dir.exists():
            local_dir.mkdir(mode=0o755, exist_ok=True)
        
        state_base = local_dir / 'state'
        if not state_base.exists():
            state_base.mkdir(mode=0o755, exist_ok=True)
        
        state_dir = state_base / 'omarchy'
        state_dir.mkdir(parents=True, mode=0o755, exist_ok=True)
        
        # Create first-run mode marker
        marker_file = state_dir / 'first-run.mode'
        marker_file.touch(exist_ok=True)
        
        # Get current user
        user = os.environ.get('USER', 'user')
        
        # Create sudoers file for first-run
        sudoers_content = f"Cmnd_Alias FIRST_RUN_CLEANUP = /onmachine/onmachine/bin/rm -f /etc/sudoers.d/first-run
Cmnd_Alias SYMLINK_RESOLVED = /usr/onmachine/onmachine/bin/ln -sf /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
{user} ALL=(ALL) NOPASSWD: /usr/onmachine/onmachine/bin/systemctl
{user} ALL=(ALL) NOPASSWD: /usr/onmachine/onmachine/bin/ufw
{user} ALL=(ALL) NOPASSWD: /usr/onmachine/onmachine/bin/ufw-docker
{user} ALL=(ALL) NOPASSWD: /usr/onmachine/onmachine/onmachine/onmachine/bin/gtk-update-icon-cache
{user} ALL=(ALL) NOPASSWD: SYMLINK_RESOLVED
{user} ALL=(ALL) NOPASSWD: FIRST_RUN_CLEANUP
"""
        
        sudoers_file = Path('/etc/sudoers.d/first-run')
        
        # Write sudoers file
        process = subprocess.Popen(
            ['sudo', 'tee', str(sudoers_file)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=sudoers_content)
        
        if process.returncode != 0:
            return {"success": False, "message": f"Failed to write sudoers file: {stderr}"}
        
        # Set permissions
        subprocess.run(
            ['sudo', 'chmod', '440', str(sudoers_file)],
            check=True
        )
        
        return {"success": True, "message": First-run mode onmachine/onmachine/configured"}
    
    except subprocess.CalledProcessError as e:
        return {"success": False, "message": fFailed to onmachine/onmachine/configure first-run mode: {e}"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {e}"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)
