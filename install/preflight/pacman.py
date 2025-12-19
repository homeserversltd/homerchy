#!/usr/bin/env python3
"""
HOMESERVER Homerchy Preflight Pacman Setup
Copyright (C) 2024 HOMESERVER LLC

Configures pacman for online installation.
"""

import os
import subprocess
import sys
from pathlib import Path


def main(config: dict) -> dict:
    """
    Main function - configures pacman if online install.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        dict: Result dictionary with success status
    """
    # Only run if online install
    if not os.environ.get('OMARCHY_ONLINE_INSTALL'):
        return {"success": True, "message": "Skipped (not online install)"}
    
    try:
        omarchy_path = Path(os.environ.get('OMARCHY_PATH', Path.home() / '.local' / 'share' / 'omarchy'))
        default_path = omarchy_path / 'default' / 'pacman'
        
        # Install build tools
        subprocess.run(
            ['sudo', 'pacman', '-S', '--needed', '--noconfirm', 'base-devel'],
            check=True
        )
        
        # Copy pacman configuration files
        pacman_conf_src = default_path / 'pacman.conf'
        pacman_conf_dst = Path('/etc/pacman.conf')
        
        if pacman_conf_src.exists():
            subprocess.run(
                ['sudo', 'cp', '-f', str(pacman_conf_src), str(pacman_conf_dst)],
                check=True
            )
        
        mirrorlist_src = default_path / 'mirrorlist'
        mirrorlist_dst = Path('/etc/pacman.d/mirrorlist')
        
        if mirrorlist_src.exists():
            subprocess.run(
                ['sudo', 'cp', '-f', str(mirrorlist_src), str(mirrorlist_dst)],
                check=True
            )
        
        # Import and sign key
        subprocess.run(
            ['sudo', 'pacman-key', '--recv-keys', '40DFB630FF42BCFFB047046CF0134EE680CAC571', '--keyserver', 'keys.openpgp.org'],
            check=True
        )
        subprocess.run(
            ['sudo', 'pacman-key', '--lsign-key', '40DFB630FF42BCFFB047046CF0134EE680CAC571'],
            check=True
        )
        
        # Sync and install keyring
        subprocess.run(['sudo', 'pacman', '-Sy'], check=True)
        subprocess.run(
            ['sudo', 'pacman', '-S', '--noconfirm', '--needed', 'omarchy-keyring'],
            check=True
        )
        
        # Full system update
        subprocess.run(
            ['sudo', 'pacman', '-Syu', '--noconfirm'],
            check=True
        )
        
        return {"success": True, "message": "Pacman configured successfully"}
    
    except subprocess.CalledProcessError as e:
        return {"success": False, "message": f"Pacman configuration failed: {e}"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {e}"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)
