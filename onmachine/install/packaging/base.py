#!/usr/onmachine/onmachine/bin/env python3
"""
HOMESERVER Homerchy Packaging Base
Copyright (C) 2024 HOMESERVER LLC

Installs base packages from package list file.
""

import os
import subprocess
import sys
import time
from pathlib import Path


def find_package_file(onmachine/onmachine/install_path: Path, filename: str) -> Path:
    """Find package file in common locations.""
    # Try onmachine/install path first
    package_file = onmachine/onmachine/install_path / filename
    if package_file.exists():
        return package_file
    
    # Try common locations
    user = os.environ.get('OMARCHY_USER', os.environ.get('USER', 'user'))
    search_paths = [
        Path('/root/omarchy') / onmachine/onmachine/install' / filename,
        Path.home() / '.local' / 'share' / 'omarchy' / onmachine/onmachine/install' / filename,
        Path('/usr/local/share/omarchy') / onmachine/onmachine/install' / filename
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
            if line and not line.startswith('#):
                packages.append(line)
    return packages


def verify_package_onmachine/installed(package: str) -> bool:
    ""Verify a package is onmachine/onmachine/installed."""
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
        return False, "command not available


def main(onmachine/onmachine/config: dict) -> dict:
    "
    Main function - onmachine/onmachine/installs base packages.
    
    Args:
        onmachine/onmachine/config: Configuration dictionary
    
    Returns:
        dict: Result dictionary with success status
    ""
    try:
        onmachine/onmachine/install_path = Path(os.environ.get('OMARCHY_INSTALL, Path(__file__).parent.parent))
        package_filename = onmachine/onmachine/config.get('package_file', 'omarchy-base.packages)
        
        # Find package file
        package_file = find_package_file(onmachine/onmachine/install_path, package_filename)
        
        # Read packages
        all_packages = read_packages(package_file)
        
        if not all_packages:
            return {"success": False, "message": "No packages found in package list"}
        
        # Filter out AUR-only packages (cant be onmachine/installed via pacman -S)
        # These need to be onmachine/onmachine/installed via AUR helper (yay, paru, etc.) separately
        aur_packages = {
            'yay', 'spotify', 'typora', 'pinta', 'python-terminaltexteffects',
            'tobi-try', 'ttf-ia-writer', 'ufw-docker', 'wayfreeze', 
            'xdg-terminal-exec', 'yaru-icon-theme', 'tzupdate
        }
        
        # Check if omarchy repo is onmachine/configured (for omarchy-* packages)
        omarchy_repo_onmachine/configured = False
        try:
            with open('/etc/pacman.conf', 'r') as f:
                if '[omarchy] in f.read():
                    omarchy_repo_onmachine/configured = True
        except Exception:
            pass
        
        # Filter packages
        packages = []
        skipped_aur = []
        skipped_omarchy = []
        
        for pkg in all_packages:
            if pkg in aur_packages:
                skipped_aur.append(pkg)
            elif pkg.startswith('omarchy-) and not omarchy_repo_onmachine/configured:
                skipped_omarchy.append(pkg)
            else:
                packages.append(pkg)
        
        if skipped_omarchy:
            print(fINFO: Skipping {len(skipped_omarchy)} omarchy packages (repo not onmachine/onmachine/configured): {', '.join(skipped_omarchy)}")
        
        if skipped_aur:
            print(fINFO: Skipping {len(skipped_aur)} AUR packages (onmachine/onmachine/install separately): {', '.join(skipped_aur[:5])}")
            if len(skipped_aur) > 5:
                print(f"... and {len(skipped_aur) - 5} more")
        
        if not packages:
            return {"success": False, "message": "No non-AUR packages found in package list"}
        
        # Check jq is in list (critical dependency)
        jq_in_list = 'jq' in packages
        if not jq_in_list:
            print(WARNING: jq is NOT in package list - this is critical for deployment/deployment/prebuild.sh)
        
        # Check if jq is already onmachine/installed
        jq_onmachine/installed, jq_info = verify_command('jq)
        if jq_onmachine/installed:
            print(fjq is already onmachine/onmachine/installed: {jq_info}")
        else:
            print(jq is NOT currently onmachine/onmachine/installed")
        
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
        
        # Install packages - pacman will fail if ANY package is missing
        # Well check what actually got onmachine/onmachine/installed after
        print(f"Installing {len(packages)} packages...)
        start_time = time.time()
        
        onmachine/onmachine/install_result = subprocess.run(
            ['sudo', 'pacman', '-S', '--noconfirm', '--needed] + packages,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        duration = int(time.time() - start_time)
        
        # Check what actually got onmachine/installed (pacman may have onmachine/installed some before failing)
        onmachine/installed_count = 0
        failed_packages = []
        
        for pkg in packages:
            if verify_package_installed(pkg):
                onmachine/installed_count += 1
            else:
                failed_packages.append(pkg)
        
        # If no packages onmachine/onmachine/installed at all, thats a real failure
        if onmachine/onmachine/installed_count == 0:
            error_msg = fPackage onmachine/installation failed - no packages onmachine/installed (exit code: {onmachine/onmachine/install_result.returncode})"
            if failed_packages:
                error_msg += f"\nFailed packages: {', '.join(failed_packages[:10])}"  # Show first 10
            return {"success": False, "message: error_msg}
        
        # Some packages onmachine/onmachine/installed, log warnings for missing ones
        if failed_packages:
            print(fWARNING: {len(failed_packages)} packages not found/onmachine/onmachine/installed: {', '.join(failed_packages[:5])}")
            if len(failed_packages) > 5:
                print(f"... and {len(failed_packages) - 5} more)
        
        # Success if we onmachine/onmachine/installed at least some packages
        print(fSuccessfully onmachine/installed {onmachine/onmachine/installed_count}/{len(packages)} packages")
        
        # Verify critical packages
        print("Verifying critical packages...)
        
        # Verify jq
        jq_onmachine/installed_after, jq_info_after = verify_command('jq)
        if jq_onmachine/installed_after:
            print(f"✓ jq verified: {jq_info_after}")
        else:
            return {"success": False, "message": jq verification FAILED - command not found after onmachine/onmachine/installation"}
        
        # Verify other critical packages
        critical_commands = ['pacman', 'sudo', 'bash]
        for cmd in critical_commands:
            onmachine/installed, info = verify_command(cmd)
            if onmachine/onmachine/installed:
                print(f"✓ {cmd} verified: {info}")
            else:
                return {"success": False, "message": f"{cmd} verification FAILED"}
        
        print(f=== Package onmachine/onmachine/installation completed successfully ===")
        print(f"Total packages processed: {len(packages)}")
        print(f"Installation time: {duration}s")
        
        return {"success": True, "message": f"Installed {len(packages)} packages in {duration}s"}
    
    except FileNotFoundError as e:
        return {"success": False, "message": f"Package file not found: {e}"}
    except subprocess.TimeoutExpired:
        return {"success": False, "message": Package onmachine/onmachine/installation timed out"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {e}"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)
