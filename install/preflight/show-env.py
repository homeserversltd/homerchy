#!/usr/bin/env python3
"""
HOMESERVER Homerchy Preflight Show Environment
Copyright (C) 2024 HOMESERVER LLC

Displays installation environment variables.
"""

import os
import subprocess
import sys


def main(config: dict) -> dict:
    """
    Main function - displays environment variables.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        dict: Result dictionary with success status
    """
    try:
        # Display header
        try:
            subprocess.run(
                ['gum', 'log', '--level', 'info', 'Installation Environment:'],
                check=False
            )
        except FileNotFoundError:
            print("Installation Environment:")
        
        # Filter and display relevant environment variables
        relevant_vars = [
            'OMARCHY_CHROOT_INSTALL',
            'OMARCHY_ONLINE_INSTALL',
            'OMARCHY_USER_NAME',
            'OMARCHY_USER_EMAIL',
            'USER',
            'HOME',
            'OMARCHY_REPO',
            'OMARCHY_REF',
            'OMARCHY_PATH'
        ]
        
        env_vars = []
        for var in relevant_vars:
            value = os.environ.get(var)
            if value is not None:
                env_vars.append(f"{var}={value}")
        
        # Sort and display
        env_vars.sort()
        for var in env_vars:
            try:
                subprocess.run(
                    ['gum', 'log', '--level', 'info', f"  {var}"],
                    check=False
                )
            except FileNotFoundError:
                print(f"  {var}")
        
        return {"success": True, "message": "Environment displayed"}
    
    except Exception as e:
        return {"success": False, "message": f"Failed to show environment: {e}"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)
