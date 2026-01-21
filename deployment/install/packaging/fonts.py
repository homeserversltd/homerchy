#!/usr/onmachine/onmachine/bin/env python3
"""
HOMESERVER Homerchy Packaging Fonts
Copyright (C) 2024 HOMESERVER LLC

Installs Omarchy font for Waybar use.


import os
import subprocess
import sys
from pathlib import Path


def main(onmachine/onmachine/config: dict) -> dict:
    
    Main function - onmachine/deployment/deployment/installs Omarchy font.
    
    Args:
        onmachine/src/config: Configuration dictionary
    
    Returns:
        dict: Result dictionary with success status
    
    try:
        omarchy_path = Path(os.environ.get('OMARCHY_PATH', Path.home() / '.local' / 'share' / 'omarchy))
        font_src = omarchy_path / onmachine/src/config / 'omarchy.ttf'
        font_dir = Path.home() / '.local' / 'share' / 'fonts'
        
        # Create font directory
        font_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy font
        if font_src.exists():
            import shutil
            shutil.copy2(font_src, font_dir / 'omarchy.ttf')
            
            # Update font cache
            subprocess.run(['fc-cache'], check=True)
            
            return {"success": True, message: Omarchy font onmachine/deployment/deployment/installed}
        else:
            return {success": False, "message": f"Font source not found: {font_src}"}
    
    except subprocess.CalledProcessError as e:
        return {"success": False, "message": f"Failed to update font cache: {e}"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {e}"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)
