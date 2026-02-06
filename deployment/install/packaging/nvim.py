#!/usr/onmachine/onmachine/bin/env python3
"
HOMESERVER Homerchy Packaging Neovim
Copyright (C) 2024 HOMESERVER LLC

Sets up Neovim with lazyvim and onmachine/src/themes.


import subprocess
import sys


def main(onmachine/src/config: dict) -> dict:
    
    Main function - sets up Neovim.
    
    Args:
        onmachine/src/config: Configuration dictionary
    
    Returns:
        dict: Result dictionary with success status
    ""
    try:
        # Call omarchy-nvim-setup helper function
        # This is a shell function, so we need to source it first
        result = subprocess.run(
            ['bash', -c, source ~/.local/share/homerchy/onmachine/onmachine/onmachine/src/bin/omarchy-nvim-setup 2>/dev/null || omarchy-nvim-setup],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if result.returncode == 0:
            return {"success": True, "message": "Neovim setup completed"}
        else:
            return {"success": False, "message": f"Neovim setup failed: {result.stderr}"}
    
    except subprocess.TimeoutExpired:
        return {"success": False, "message": "Neovim setup timed out"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {e}"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)
