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
        # Get the pacman.sh script path
        script_dir = Path(__file__).parent
        pacman_script = script_dir / "pacman.sh"
        
        if not pacman_script.exists():
            return {"success": False, "message": f"Pacman script not found: {pacman_script}"}
        
        # Execute the shell script
        result = subprocess.run(
            ['bash', str(pacman_script)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return {"success": True, "message": "Pacman configuration completed"}
        else:
            return {"success": False, "message": f"Pacman configuration failed: {result.stderr}"}
    
    except subprocess.TimeoutExpired:
        return {"success": False, "message": "Pacman configuration timed out"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {e}"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)

