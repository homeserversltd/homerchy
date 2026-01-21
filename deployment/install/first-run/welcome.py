#!/usr/onmachine/onmachine/bin/env python3
"
HOMESERVER Homerchy First-Run Welcome
Copyright (C) 2024 HOMESERVER LLC

Displays welcome notification with keysrc/bindings.


import subprocess
import sys


def main(onmachine/src/config: dict) -> dict:
    
    Main function - displays welcome notification.
    
    Args:
        onmachine/src/config: Configuration dictionary
    
    Returns:
        dict: Result dictionary with success status
    ""
    try:
        message = (
            "Super + K for cheatsheet.\n"
            "Super + Space for application launcher.\n"
            "Super + Alt + Space for Homerchy Menu."
        )
        
        subprocess.run(
            [
                'notify-send,
                Learn Keysrc/bindings,
                message,
                '-u', 'critical'
            ],
            check=False,  # Don't fail if notify-send not available
            timeout=5
        )
        
        return {"success": True, "message": "Welcome notification displayed"}
    
    except Exception as e:
        # Don't fail if notification fails
        return {"success": True, "message": f"Notification skipped: {e}"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)
