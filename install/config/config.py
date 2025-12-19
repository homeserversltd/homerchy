#!/usr/bin/env python3
"""
HOMESERVER Homerchy Config - Base Configuration
Copyright (C) 2024 HOMESERVER LLC

Copies Omarchy configs to user config directory.
"""

import os
import shutil
import sys
from pathlib import Path


def main(config: dict) -> dict:
    """
    Main function - copies config files.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        dict: Result dictionary with success status
    """
    try:
        omarchy_path = Path(os.environ.get('OMARCHY_PATH', Path.home() / '.local' / 'share' / 'omarchy'))
        config_src = omarchy_path / 'config'
        config_dst = Path.home() / '.config'
        
        # Create destination directory
        config_dst.mkdir(parents=True, exist_ok=True)
        
        # Copy all config files
        if config_src.exists():
            shutil.copytree(config_src, config_dst, dirs_exist_ok=True)
        else:
            return {"success": False, "message": f"Config source not found: {config_src}"}
        
        # Copy default bashrc
        bashrc_src = omarchy_path / 'default' / 'bashrc'
        bashrc_dst = Path.home() / '.bashrc'
        
        if bashrc_src.exists():
            shutil.copy2(bashrc_src, bashrc_dst)
        
        return {"success": True, "message": "Configuration files copied"}
    
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {e}"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)
