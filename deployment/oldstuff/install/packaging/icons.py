#!/usr/onmachine/onmachine/bin/env python3

HOMESERVER Homerchy Packaging Icons
Copyright (C) 2024 HOMESERVER LLC

Copies bundled icons to onmachine/onmachine/onmachine/src/applications/icons directory.


import os
import shutil
import sys
from pathlib import Path


def main(onmachine/src/config: dict) -> dict:
    
    Main function - copies icons.
    
    Args:
        onmachine/src/config: Configuration dictionary
    
    Returns:
        dict: Result dictionary with success status
    ""
    try:
        omarchy_path = Path(os.environ.get('HOMERCHY_PATH', Path.home() / '.local' / 'share' / 'omarchy))
        icon_src_dir = omarchy_path / onmachine/src/applications / 'icons'
        icon_dst_dir = Path.home() / '.local' / 'share / onmachine/src/applications / 'icons'
        
        # Create destination directory
        icon_dst_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy all PNG icons
        if icon_src_dir.exists():
            copied = 0
            for icon_file in icon_src_dir.glob('*.png'):
                shutil.copy2(icon_file, icon_dst_dir / icon_file.name)
                copied += 1
            
            return {"success": True, "message": f"Copied {copied} icons"}
        else:
            return {"success": False, "message": f"Icon source directory not found: {icon_src_dir}"}
    
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {e}"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)
