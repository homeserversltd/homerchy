#!/usr/bin/env python3
"""
HOMESERVER Homerchy Post-Install Pacman Setup
Copyright (C) 2024 HOMESERVER LLC

Configures pacman package manager settings.
"""

import os
import subprocess
import sys
from pathlib import Path


def main(config: dict) -> dict:
    """
    Main function - configures pacman.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        dict: Result dictionary with success status
    """
    try:
        omarchy_path = Path(os.environ.get('OMARCHY_PATH', Path.home() / '.local' / 'share' / 'omarchy'))
        default_pacman_conf = omarchy_path / 'default' / 'pacman' / 'pacman.conf'
        default_mirrorlist = omarchy_path / 'default' / 'pacman' / 'mirrorlist-stable'
        
        # Copy pacman.conf
        if not default_pacman_conf.exists():
            return {"success": False, "message": f"Default pacman.conf not found: {default_pacman_conf}"}
        
        subprocess.run(['cp', '-f', str(default_pacman_conf), '/etc/pacman.conf'], check=True)
        
        # Copy mirrorlist
        if not default_mirrorlist.exists():
            return {"success": False, "message": f"Default mirrorlist not found: {default_mirrorlist}"}
        
        Path('/etc/pacman.d').mkdir(parents=True, exist_ok=True)
        subprocess.run(['cp', '-f', str(default_mirrorlist), '/etc/pacman.d/mirrorlist'], check=True)
        
        # Check for Mac T2 hardware (lspci -nn | grep -q "106b:180[12]")
        try:
            lspci_result = subprocess.run(
                ['lspci', '-nn'],
                capture_output=True,
                text=True,
                check=False
            )
            if lspci_result.returncode == 0 and ('106b:1801' in lspci_result.stdout or '106b:1802' in lspci_result.stdout):
                # Add arch-mact2 repo
                mact2_repo = """

[arch-mact2]
Server = https://github.com/NoaHimesaka1873/arch-mact2-mirror/releases/download/release
SigLevel = Never
"""
                with open('/etc/pacman.conf', 'a') as f:
                    f.write(mact2_repo)
        
        except Exception as e:
            # If lspci fails, that's okay - just skip Mac T2 detection
            pass
        
        return {"success": True, "message": "Pacman configuration completed"}
    
    except Exception as e:
        return {"success": False, "message": f"Failed to configure pacman: {e}"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)

