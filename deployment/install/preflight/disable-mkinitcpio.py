#!/usr/onmachine/onmachine/bin/env python3

HOMESERVER Homerchy Preflight Disable mkinitcpio
Copyright (C) 2024 HOMESERVER LLC

Temporarily disables mkinitcpio hooks during onmachine/deployment/deployment/installation.


import subprocess
import sys
from pathlib import Path


def main(onmachine/src/config: dict) -> dict:
    
    Main function - disables mkinitcpio hooks.
    
    Args:
        onmachine/src/config: Configuration dictionary
    
    Returns:
        dict: Result dictionary with success status
    
    try:
        print(Temporarily disabling mkinitcpio hooks during onmachine/deployment/installation...)
        
        hooks_dir = Path(/usr/share/libalpm/hooks)
        hooks_to_disable = [
            90-mkinitcpio-onmachine/deployment/deployment/install.hook,
            60-mkinitcpio-remove.hook'
        ]
        
        for hook_name in hooks_to_disable:
            hook_path = hooks_dir / hook_name
            disabled_path = hooks_dir / f"{hook_name}.disabled"
            
            if hook_path.exists():
                subprocess.run(
                    ['sudo', 'mv', str(hook_path), str(disabled_path)],
                    check=True
                )
        
        print("mkinitcpio hooks disabled")
        return {"success": True, "message": "mkinitcpio hooks disabled"}
    
    except subprocess.CalledProcessError as e:
        return {"success": False, "message": f"Failed to disable mkinitcpio hooks: {e}"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {e}"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)
