#!/usr/bin/env python3
"""
HOMESERVER Homerchy Login Default Keyring Setup
Copyright (C) 2024 HOMESERVER LLC

Sets up default keyring for user.
"""

import os
import subprocess
import sys
from pathlib import Path


def main(config: dict) -> dict:
    """
    Main function - sets up default keyring.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        dict: Result dictionary with success status
    """
    try:
        # Get the default-keyring.sh script path
        script_dir = Path(__file__).parent
        keyring_script = script_dir / "default-keyring.sh"
        
        if not keyring_script.exists():
            return {"success": False, "message": f"Keyring script not found: {keyring_script}"}
        
        # Execute the shell script
        result = subprocess.run(
            ['bash', str(keyring_script)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return {"success": True, "message": "Default keyring setup completed"}
        else:
            return {"success": False, "message": f"Keyring setup failed: {result.stderr}"}
    
    except subprocess.TimeoutExpired:
        return {"success": False, "message": "Keyring setup timed out"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {e}"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)

