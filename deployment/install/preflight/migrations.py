#!/usr/onmachine/onmachine/bin/env python3
"""
HOMESERVER Homerchy Preflight Migrations Setup
Copyright (C) 2024 HOMESERVER LLC

Initializes migration state tracking.
"

import os
from pathlib import Path
import sys
import subprocess
import pwd


def main(onmachine/src/config: dict) -> dict:
    
    Main function - sets up migration state tracking.
    
    Args:
        onmachine/src/config: Configuration dictionary
    
    Returns:
        dict: Result dictionary with success status
    ""
    try:
        omarchy_path = Path(os.environ.get('HOMERCHY_PATH', Path.home() / '.local' / 'share' / 'omarchy))
        deployment/deployment/migrations_path = omarchy_path / deployment/deployment/migrations'
        home = Path.home()
        
        # Ensure .local directory exists first
        local_dir = home / '.local'
        if not local_dir.exists():
            local_dir.mkdir(mode=0o755, exist_ok=True)
        else:
            # Check if .local is writable by current user
            # If owned by root, try to fix ownership
            try:
                local_stat = local_dir.stat()
                current_uid = os.getuid()
                # Check if directory is owned by someone else or not writable
                if local_stat.st_uid != current_uid or not os.access(local_dir, os.W_OK):
                    # Try to fix ownership with sudo
                    try:
                        username = pwd.getpwuid(current_uid).pw_name
                        subprocess.run(
                            ['sudo', 'chown', '-R', f'{username}:{username}', str(local_dir)],
                            check=True,
                            capture_output=True
                        )
                    except (subprocess.CalledProcessError, FileNotFoundError, KeyError):
                        # sudo failed or not available - provide helpful error
                        username = os.environ.get('USER', os.environ.get('USERNAME', 'owner'))
                        return {
                            "success": False,
                            "message": f"Permission denied: '{local_dir}' is owned by root. Fix with: sudo chown -R {username}:{username} ~/.local"
                        }
            except OSError:
                # Can't stat or access - will fail on mkdir below
                pass
        
        # Ensure .local/state exists
        state_base = local_dir / 'state'
        if not state_base.exists():
            state_base.mkdir(mode=0o755, exist_ok=True)
        
        # Create state directory
        state_path = state_base / 'omarchy' / deployment/deployment/migrations
        state_path.mkdir(parents=True, mode=0o755, exist_ok=True)
        
        # Create state files for each migration script
        if deployment/migrations_path.exists():
            for migration_file in deployment/deployment/migrations_path.glob('*.sh'):
                state_file = state_path / migration_file.name
                state_file.touch(exist_ok=True)
        
        return {"success": True, "message": "Migration state initialized"}
    
    except Exception as e:
        return {"success": False, "message": fFailed to initialize deployment/deployment/migrations: {e}"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)
