#!/usr/bin/env python3
"""
HOMESERVER Homerchy Packaging Base
Copyright (C) 2024 HOMESERVER LLC

Installs base packages from package list file.
"""

import os
import subprocess
import sys
import time
from pathlib import Path


def find_package_file(install_path: Path, filename: str) -> Path:
    """Find package file in common locations."""
    # Try install path first
    package_file = install_path / filename
    if package_file.exists():
        return package_file
    
    # Try common locations
    user = os.environ.get('OMARCHY_USER', os.environ.get('USER', 'user'))
    search_paths = [
        Path('/root/omarchy') / 'install' / filename,
        Path.home() / '.local' / 'share' / 'omarchy' / 'install' / filename,
        Path('/usr/local/share/omarchy') / 'install' / filename
    ]
    
    for path in search_paths:
        if path.exists():
            return path
    
    raise FileNotFoundError(f"Package file not found: {filename}")


def read_packages(package_file: Path) -> list:
    """Read package list from file, excluding comments and empty lines."""
    packages = []
    with open(package_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if line and not line.startswith('#'):
                packages.append(line)
    return packages


def verify_package_installed(package: str) -> bool:
    """Verify a package is installed."""
    try:
        result = subprocess.run(
            ['pacman', '-Qi', package],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def verify_command(command: str) -> tuple[bool, str]:
    """Verify a command is available."""
    try:
        result = subprocess.run(
            ['command', '-v', command],
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            path = result.stdout.strip()
            # Get version if possible
            try:
                version_result = subprocess.run(
                    [command, '--version'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                version = version_result.stdout.strip().split('\n')[0] if version_result.returncode == 0 else "unknown"
            except:
                version = "unknown"
            return True, f"{path} (version: {version})"
        return False, "not found"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, "command not available"


def main(config: dict) -> dict:
    """
    Main function - installs base packages.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        dict: Result dictionary with success status
    """
    try:
        install_path = Path(os.environ.get('OMARCHY_INSTALL', Path(__file__).parent.parent))
        package_filename = config.get('package_file', 'omarchy-base.packages')
        
        # Find package file
        package_file = find_package_file(install_path, package_filename)
        
        # Read packages
        packages = read_packages(package_file)
        
        if not packages:
            return {"success": False, "message": "No packages found in package list"}
        
        # Check jq is in list (critical dependency)
        jq_in_list = 'jq' in packages
        if not jq_in_list:
            print("WARNING: jq is NOT in package list - this is critical for prebuild.sh")
        
        # Check if jq is already installed
        jq_installed, jq_info = verify_command('jq')
        if jq_installed:
            print(f"jq is already installed: {jq_info}")
        else:
            print("jq is NOT currently installed")
        
        # Sync pacman database
        print("Syncing pacman database...")
        sync_result = subprocess.run(
            ['sudo', 'pacman', '-Sy'],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if sync_result.returncode != 0:
            return {"success": False, "message": f"Failed to sync pacman database: {sync_result.stderr}"}
        
        # Install packages
        print(f"Installing {len(packages)} packages...")
        start_time = time.time()
        
        install_result = subprocess.run(
            ['sudo', 'pacman', '-S', '--noconfirm', '--needed'] + packages,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        duration = int(time.time() - start_time)
        
        if install_result.returncode != 0:
            # Check which packages failed
            failed_packages = []
            for pkg in packages:
                if not verify_package_installed(pkg):
                    failed_packages.append(pkg)
            
            error_msg = f"Package installation failed (exit code: {install_result.returncode})"
            if failed_packages:
                error_msg += f"\nFailed packages: {', '.join(failed_packages)}"
            
            return {"success": False, "message": error_msg}
        
        # Verify critical packages
        print("Verifying critical packages...")
        
        # Verify jq
        jq_installed_after, jq_info_after = verify_command('jq')
        if jq_installed_after:
            print(f"✓ jq verified: {jq_info_after}")
        else:
            return {"success": False, "message": "jq verification FAILED - command not found after installation"}
        
        # Verify other critical packages
        critical_commands = ['pacman', 'sudo', 'bash']
        for cmd in critical_commands:
            installed, info = verify_command(cmd)
            if installed:
                print(f"✓ {cmd} verified: {info}")
            else:
                return {"success": False, "message": f"{cmd} verification FAILED"}
        
        print(f"=== Package installation completed successfully ===")
        print(f"Total packages processed: {len(packages)}")
        print(f"Installation time: {duration}s")
        
        return {"success": True, "message": f"Installed {len(packages)} packages in {duration}s"}
    
    except FileNotFoundError as e:
        return {"success": False, "message": f"Package file not found: {e}"}
    except subprocess.TimeoutExpired:
        return {"success": False, "message": "Package installation timed out"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {e}"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)

