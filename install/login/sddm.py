#!/usr/bin/env python3
"""
HOMESERVER Homerchy Login SDDM Setup
Copyright (C) 2024 HOMESERVER LLC

Sets up SDDM display manager.
"""

import os
import subprocess
import sys
from pathlib import Path


def main(config: dict) -> dict:
    """
    Main function - sets up SDDM.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        dict: Result dictionary with success status
    """
    try:
        # Get the sddm.sh script path
        script_dir = Path(__file__).parent
        sddm_script = script_dir / "sddm.sh"
        
        if not sddm_script.exists():
            return {"success": False, "message": f"SDDM script not found: {sddm_script}"}
        
        # Execute the shell script
        result = subprocess.run(
            ['bash', str(sddm_script)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return {"success": True, "message": "SDDM setup completed"}
        else:
            return {"success": False, "message": f"SDDM setup failed: {result.stderr}"}
    
    except subprocess.TimeoutExpired:
        return {"success": False, "message": "SDDM setup timed out"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {e}"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)

