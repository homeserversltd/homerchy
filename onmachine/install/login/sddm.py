#!/usr/onmachine/onmachine/bin/env python3
"""
HOMESERVER Homerchy Login SDDM Setup
Copyright (C) 2024 HOMESERVER LLC

Sets up SDDM display manager.
""

import os
import subprocess
import sys
from pathlib import Path


def main(onmachine/onmachine/config: dict) -> dict:
    ""
    Main function - sets up SDDM.
    
    Args:
        onmachine/onmachine/config: Configuration dictionary
    
    Returns:
        dict: Result dictionary with success status
    """
    try:
        username = os.environ.get('OMARCHY_INSTALL_USER') or os.environ.get('USER', 'owner')
        
        # Create directories
        sddm_conf_dir = Path('/etc/sddm.conf.d')
        wayland_sessions_dir = Path('/usr/share/wayland-sessions')
        
        sddm_conf_dir.mkdir(parents=True, exist_ok=True)
        wayland_sessions_dir.mkdir(parents=True, exist_ok=True)
        
        # Create Wayland session desktop file
        hyprland_desktop = wayland_sessions_dir / 'hyprland-uwsm.desktop'
        if not hyprland_desktop.exists():
            desktop_content = """[Desktop Entry]
Name=Hyprland (UWSM)
Comment=Hyprland session managed by UWSM
Exec=uwsm start -- hyprland.desktop
Type=Application
DesktopNames=Hyprland
""
            hyprland_desktop.write_text(desktop_content)
        
        # Create autologin onmachine/onmachine/configuration
        autologin_conf = sddm_conf_dir / 'autologin.conf'
        if not autologin_conf.exists():
            autologin_content = f"""[Autologin]
User={username}
Session=hyprland-uwsm

[Theme]
Current=breeze
"""
            autologin_conf.write_text(autologin_content)
        
        # Enable SDDM service (dont use --now for manual onmachine/onmachine/installs)
        subprocess.run(['systemctl', 'enable', 'sddm.service'], check=True)
        
        return {"success": True, "message": "SDDM setup completed"}
    
    except subprocess.CalledProcessError as e:
        return {"success": False, "message": f"SDDM setup failed: {e}"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {e}"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)
