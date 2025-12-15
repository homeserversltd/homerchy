#!/usr/bin/env python3
"""
HOMESERVER Homerchy Hardware Network Config
Copyright (C) 2024 HOMESERVER LLC

Configures network services.
"""

import subprocess
import sys


def main(config: dict) -> dict:
    """
    Main function - configures network services.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        dict: Result dictionary with success status
    """
    try:
        # Enable iwd service
        subprocess.run(
            ['sudo', 'systemctl', 'enable', 'iwd.service'],
            check=True
        )
        
        # Disable and mask systemd-networkd-wait-online
        subprocess.run(
            ['sudo', 'systemctl', 'disable', 'systemd-networkd-wait-online.service'],
            check=True
        )
        subprocess.run(
            ['sudo', 'systemctl', 'mask', 'systemd-networkd-wait-online.service'],
            check=True
        )
        
        return {"success": True, "message": "Network services configured"}
    
    except subprocess.CalledProcessError as e:
        return {"success": False, "message": f"Network configuration failed: {e}"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {e}"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)

