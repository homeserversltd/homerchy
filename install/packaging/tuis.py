#!/usr/bin/env python3
"""
HOMESERVER Homerchy Packaging TUIs
Copyright (C) 2024 HOMESERVER LLC

Installs TUI applications.
"""

import os
import subprocess
import sys
from pathlib import Path


def main(config: dict) -> dict:
    """
    Main function - installs TUI applications.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        dict: Result dictionary with success status
    """
    try:
        icon_dir = Path.home() / '.local' / 'share' / 'applications' / 'icons'
        
        # Install Disk Usage TUI
        disk_usage_cmd = "bash -c 'dust -r; read -n 1 -s'"
        disk_usage_icon = str(icon_dir / "Disk Usage.png")
        
        result1 = subprocess.run(
            ['bash', '-c', f'source ~/.local/share/omarchy/bin/omarchy-tui-install 2>/dev/null || omarchy-tui-install "Disk Usage" "{disk_usage_cmd}" float "{disk_usage_icon}"'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Install Docker TUI
        docker_icon = str(icon_dir / "Docker.png")
        
        result2 = subprocess.run(
            ['bash', '-c', f'source ~/.local/share/omarchy/bin/omarchy-tui-install 2>/dev/null || omarchy-tui-install "Docker" "lazydocker" tile "{docker_icon}"'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result1.returncode == 0 and result2.returncode == 0:
            return {"success": True, "message": "TUI applications installed"}
        else:
            errors = []
            if result1.returncode != 0:
                errors.append(f"Disk Usage: {result1.stderr}")
            if result2.returncode != 0:
                errors.append(f"Docker: {result2.stderr}")
            return {"success": False, "message": f"TUI installation failed: {'; '.join(errors)}"}
    
    except subprocess.TimeoutExpired:
        return {"success": False, "message": "TUI installation timed out"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {e}"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)

