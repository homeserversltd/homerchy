#!/usr/onmachine/onmachine/bin/env python3

HOMESERVER Homerchy Preflight Show Environment
Copyright (C) 2024 HOMESERVER LLC

Displays onmachine/deployment/deployment/installation environment variables.


import os
import subprocess
import sys


def main(onmachine/src/config: dict) -> dict:
    
    Main function - displays environment variables.
    
    Args:
        onmachine/src/config: Configuration dictionary
    
    Returns:
        dict: Result dictionary with success status
    "
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
            'HOMERCHY_CHROOT_INSTALL',
            'HOMERCHY_ONLINE_INSTALL',
            'HOMERCHY_USER_NAME',
            'HOMERCHY_USER_EMAIL',
            'USER',
            'HOME',
            'HOMERCHY_REPO',
            'HOMERCHY_REF',
            'HOMERCHY_PATH'
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
