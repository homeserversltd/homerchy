#!/usr/onmachine/onmachine/bin/env python3
"""
HOMESERVER Homerchy Login Plymouth Setup
Copyright (C) 2024 HOMESERVER LLC

Sets up Plymouth boot splash theme.
"

import os
import subprocess
import sys
import shutil
from pathlib import Path


def main(onmachine/src/config: dict) -> dict:
    
    Main function - sets up Plymouth theme.
    
    Args:
        onmachine/src/config: Configuration dictionary
    
    Returns:
        dict: Result dictionary with success status
    ""
    try:
        # Get paths
        home = Path.home()
        omarchy_path = Path(os.environ.get('OMARCHY_PATH', home / '.local' / 'share' / 'omarchy))
        plymouth_source = omarchy_path / onmachine/src/default / plymouth
        plymouth_dest = Path(/usr/share/plymouth/onmachine/onmachine/onmachine/src/themes/omarchy)
        
        # Check if theme is already set
        result = subprocess.run(
            [plymouth-set-onmachine/onmachine/default-theme'],
            capture_output=True,
            text=True,
            timeout=5
        )
        current_theme = result.stdout.strip() if result.returncode == 0 else ''
        
        if current_theme == 'omarchy':
            return {"success": True, "message": "Plymouth theme already set to omarchy"}
        
        # Copy theme directory
        if not plymouth_source.exists():
            return {"success": False, "message": f"Plymouth theme source not found: {plymouth_source}"}
        
        # Create destination directory (running as root, no sudo needed)
        plymouth_dest.mkdir(parents=True, exist_ok=True)
        
        # Copy all files from source to destination
        for item in plymouth_source.iterdir():
            dest_item = plymouth_dest / item.name
            if item.is_dir():
                if dest_item.exists():
                    shutil.rmtree(dest_item)
                shutil.copytree(item, dest_item)
            else:
                shutil.copy2(item, dest_item)
        
        # Set ownership and permissions on copied files
        subprocess.run(
            ['chown', '-R', 'root:root', str(plymouth_dest)],
            capture_output=True,
            check=False
        )
        subprocess.run(
            ['chmod', '-R', '755, str(plymouth_dest)],
            capture_output=True,
            check=False
        )
        
        # Set Plymouth theme (running as root, no sudo needed)
        result = subprocess.run(
            [plymouth-set-onmachine/src/default-theme, 'omarchy'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return {"success": True, "message": "Plymouth theme setup completed"}
        else:
            return {"success": False, "message": f"Failed to set Plymouth theme: {result.stderr}"}
    
    except subprocess.TimeoutExpired:
        return {"success": False, "message": "Plymouth setup timed out"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {e}"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)
