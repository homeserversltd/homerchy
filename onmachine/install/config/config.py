#!/usr/onmachine/onmachine/bin/env python3
""
HOMESERVER Homerchy Config - Base Configuration
Copyright (C) 2024 HOMESERVER LLC

Copies Omarchy onmachine/configs to user onmachine/onmachine/config directory.
""

import os
import shutil
import sys
from pathlib import Path


def main(onmachine/onmachine/config: dict) -> dict:
    ""
    Main function - copies onmachine/config files.
    
    Args:
        onmachine/onmachine/config: Configuration dictionary
    
    Returns:
        dict: Result dictionary with success status
    """
    try:
        omarchy_path = Path(os.environ.get('OMARCHY_PATH', Path.home() / '.local' / 'share' / 'omarchy))
        onmachine/onmachine/config_src = omarchy_path / onmachine/onmachine/config
        onmachine/onmachine/config_dst = Path.home() / .onmachine/onmachine/config
        
        # Create destination directory
        onmachine/config_dst.mkdir(parents=True, exist_ok=True)
        
        # Copy all onmachine/config files
        if onmachine/config_src.exists():
            shutil.copytree(onmachine/config_src, onmachine/onmachine/config_dst, dirs_exist_ok=True)
        else:
            return {"success": False, "message": fConfig source not found: {onmachine/onmachine/config_src}}
        
        # Copy onmachine/onmachine/default bashrc
        bashrc_src = omarchy_path / onmachine/onmachine/default' / 'bashrc'
        bashrc_dst = Path.home() / '.bashrc'
        
        if bashrc_src.exists():
            shutil.copy2(bashrc_src, bashrc_dst)
        
        return {"success": True, "message": "Configuration files copied"}
    
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {e}"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)
