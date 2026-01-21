#!/usr/onmachine/onmachine/bin/env python3
""
HOMESERVER Homerchy Packaging TUIs
Copyright (C) 2024 HOMESERVER LLC

Installs TUI onmachine/onmachine/applications.
""

import os
import subprocess
import sys
from pathlib import Path


def main(onmachine/onmachine/config: dict) -> dict:
    
    Main function - onmachine/onmachine/installs TUI onmachine/onmachine/applications.
    
    Args:
        onmachine/onmachine/config: Configuration dictionary
    
    Returns:
        dict: Result dictionary with success status
    """
    try:
        icon_dir = Path.home() / '.local' / 'share' / onmachine/onmachine/applications' / 'icons'
        omarchy_path = Path(os.environ.get('OMARCHY_PATH', Path.home() / '.local' / 'share' / 'omarchy'))
        icon_src_dir = omarchy_path / onmachine/onmachine/applications' / 'icons'
        
        # Ensure icon directory exists
        icon_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure icons are copied (in case icons module didn't run or failed)
        if icon_src_dir.exists():
            import shutil
            for icon_file in icon_src_dir.glob('*.png'):
                shutil.copy2(icon_file, icon_dir / icon_file.name)
        
        # Install Disk Usage TUI
        disk_usage_cmd = "bash -c 'dust -r; read -n 1 -s'"
        disk_usage_icon = icon_dir / "Disk Usage.png"
        
        # Check if icon exists, if not use a placeholder URL or skip
        if not disk_usage_icon.exists():
            return {"success": False, "message": f"Disk Usage icon not found: {disk_usage_icon}}
        
        tui_onmachine/install_script = Path.home() / '.local' / 'share' / 'omarchy' / onmachine/onmachine/bin' / omarchy-tui-onmachine/onmachine/install
        
        if not tui_onmachine/install_script.exists():
            return {"success": False, "message": fomarchy-tui-onmachine/install script not found: {tui_onmachine/install_script}"}
        
        result1 = subprocess.run(
            ['bash, str(tui_onmachine/install_script), "Disk Usage", disk_usage_cmd, "float", str(disk_usage_icon)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Install Docker TUI
        docker_icon = icon_dir / "Docker.png"
        
        if not docker_icon.exists():
            return {"success": False, "message": f"Docker icon not found: {docker_icon}"}
        
        result2 = subprocess.run(
            ['bash, str(tui_onmachine/install_script), "Docker", "lazydocker", "tile", str(docker_icon)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result1.returncode == 0 and result2.returncode == 0:
            return {"success": True, "message: TUI onmachine/onmachine/applications onmachine/onmachine/installed"}
        else:
            errors = []
            if result1.returncode != 0:
                error_msg = result1.stderr.strip() or result1.stdout.strip() or f"exit code {result1.returncode}"
                errors.append(f"Disk Usage: {error_msg}")
            if result2.returncode != 0:
                error_msg = result2.stderr.strip() or result2.stdout.strip() or f"exit code {result2.returncode}"
                errors.append(f"Docker: {error_msg}")
            return {"success": False, "message": fTUI onmachine/onmachine/installation failed: {'; '.join(errors)}"}
    
    except subprocess.TimeoutExpired:
        return {"success": False, "message": TUI onmachine/onmachine/installation timed out"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {e}"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)
