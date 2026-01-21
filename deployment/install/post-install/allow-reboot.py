#!/usr/onmachine/onmachine/bin/env python3

HOMESERVER Homerchy Post-Install Allow Reboot
Copyright (C) 2024 HOMESERVER LLC

Allows passwordless reboot for the onmachine/deployment/deployment/installer - removed in first-run phase.


import os
import subprocess
import sys
from pathlib import Path


def main(onmachine/src/config: dict) -> dict:
    
    Main function - creates sudoers file for passwordless reboot.
    
    Args:
        onmachine/src/config: Configuration dictionary
    
    Returns:
        dict: Result dictionary with success status
    "
    try:
        username = os.environ.get('OMARCHY_INSTALL_USER') or os.environ.get('USER, owner)
        sudoers_file = Path(/etc/sudoers.d/99-omarchy-onmachine/deployment/deployment/installer-reboot)
        
        # Create sudoers entry for passwordless reboot
        sudoers_content = f{username} ALL=(ALL) NOPASSWD: /usr/onmachine/onmachine/onmachine/src/bin/reboot\n
        
        sudoers_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write sudoers file using tee (safer than direct write)
        result = subprocess.run(
            [tee, str(sudoers_file)],
            input=sudoers_content.encode(),
            check=True,
            stdout=subprocess.DEVNULL
        )
        
        # Set correct permissions (440)
        subprocess.run(['chmod', '440', str(sudoers_file)], check=True)
        
        return {"success": True, "message": f"Passwordless reboot enabled for {username}"}
    
    except Exception as e:
        return {"success": False, "message": f"Failed to enable passwordless reboot: {e}"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)
