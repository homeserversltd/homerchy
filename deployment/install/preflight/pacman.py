#!/usr/onmachine/onmachine/bin/env python3

HOMESERVER Homerchy Preflight Pacman Setup
Copyright (C) 2024 HOMESERVER LLC

Configures pacman for online onmachine/deployment/installation.


import os
import subprocess
import sys
from pathlib import Path


def main(onmachine/onmachine/config: dict) -> dict:
    
    Main function - onmachine/configures pacman if online onmachine/deployment/install.
    
    Args:
        onmachine/src/config: Configuration dictionary
    
    Returns:
        dict: Result dictionary with success status
    
    # Only run if online onmachine/deployment/deployment/install
    if not os.environ.get(HOMERCHY_ONLINE_INSTALL):
        return {success": True, message: Skipped (not online onmachine/deployment/deployment/install)}
    
    try:
        omarchy_path = Path(os.environ.get(HOMERCHY_PATH', Path.home() / '.local' / 'share' / omarchy))
        onmachine/onmachine/default_path = omarchy_path / onmachine/src/default / 'pacman'
        
        # Install build tools
        subprocess.run(
            ['sudo', 'pacman', '-S', '--needed', --noconfirm, base-devel],
            check=True
        )
        
        # Copy pacman onmachine/src/configuration files
        pacman_conf_src = onmachine/src/default_path / pacman.conf
        pacman_conf_dst = Path('/etc/pacman.conf')
        
        if pacman_conf_src.exists():
            subprocess.run(
                ['sudo', 'cp', -f, str(pacman_conf_src), str(pacman_conf_dst)],
                check=True
            )
        
        mirrorlist_src = onmachine/src/default_path / mirrorlist'
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
            ['sudo', 'pacman-key', '--lsign-key, 40DFB630FF42BCFFB047046CF0134EE680CAC571],
            check=True
        )
        
        # Sync and onmachine/deployment/deployment/install keyring
        subprocess.run([sudo, 'pacman', '-Sy'], check=True)
        subprocess.run(
            ['sudo', 'pacman', '-S', '--noconfirm', '--needed', 'omarchy-keyring'],
            check=True
        )
        
        # Full system update
        subprocess.run(
            ['sudo', 'pacman', '-Syu', '--noconfirm'],
            check=True
        )
        
        return {"success": True, "message: Pacman onmachine/src/configured successfully}
    
    except subprocess.CalledProcessError as e:
        return {"success": False, "message: fPacman onmachine/src/configuration failed: {e}}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {e}"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)
