#!/usr/bin/env python3
"""
HOMESERVER Homerchy Preflight Guard
Copyright (C) 2024 HOMESERVER LLC

Pre-installation guard checks - validates system requirements.
"""

import os
import subprocess
import sys
from pathlib import Path


def abort(message: str) -> None:
    """Abort installation with user confirmation."""
    print(f"\033[31mOmarchy install requires: {message}\033[0m")
    print()
    
    # Use gum confirm if available, otherwise prompt
    try:
        result = subprocess.run(
            ['gum', 'confirm', 'Proceed anyway on your own accord and without assistance?'],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            sys.exit(1)
    except FileNotFoundError:
        # Fallback to Python input if gum not available
        response = input("Proceed anyway? (yes/no): ")
        if response.lower() != 'yes':
            sys.exit(1)


def check_arch_release() -> bool:
    """Check if system is vanilla Arch Linux."""
    if not Path("/etc/arch-release").exists():
        abort("Vanilla Arch")
        return False
    
    # Check for Arch derivatives
    derivative_markers = [
        "/etc/cachyos-release",
        "/etc/eos-release",
        "/etc/garuda-release",
        "/etc/manjaro-release"
    ]
    
    for marker in derivative_markers:
        if Path(marker).exists():
            abort("Vanilla Arch")
            return False
    
    return True


def check_not_root() -> bool:
    """Check that we're not running as root."""
    if os.geteuid() == 0:
        abort("Running as root (not user)")
        return False
    return True


def check_architecture() -> bool:
    """Check CPU architecture is x86_64."""
    import platform
    if platform.machine() != "x86_64":
        abort("x86_64 CPU")
        return False
    return True


def check_secure_boot() -> bool:
    """Check that secure boot is disabled."""
    try:
        result = subprocess.run(
            ['bootctl', 'status'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if 'Secure Boot: enabled' in result.stdout:
            abort("Secure Boot disabled")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        # bootctl not available or timeout - assume OK
        pass
    return True


def check_desktop_environment() -> bool:
    """Check that Gnome or KDE are not already installed."""
    try:
        result1 = subprocess.run(
            ['pacman', '-Qe', 'gnome-shell'],
            capture_output=True,
            timeout=5
        )
        result2 = subprocess.run(
            ['pacman', '-Qe', 'plasma-desktop'],
            capture_output=True,
            timeout=5
        )
        
        if result1.returncode == 0 or result2.returncode == 0:
            abort("Fresh + Vanilla Arch")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        # pacman not available or timeout - assume OK
        pass
    return True


def check_limine() -> bool:
    """Check that Limine bootloader is installed."""
    result = subprocess.run(
        ['command', '-v', 'limine'],
        shell=True,
        capture_output=True
    )
    if result.returncode != 0:
        abort("Limine bootloader")
        return False
    return True


def check_btrfs() -> bool:
    """Check that root filesystem is btrfs."""
    try:
        result = subprocess.run(
            ['findmnt', '-n', '-o', 'FSTYPE', '/'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.stdout.strip() != 'btrfs':
            abort("Btrfs root filesystem")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        # findmnt not available or timeout - assume OK
        pass
    return True


def main(config: dict) -> dict:
    """
    Main guard function - runs all checks.
    
    Args:
        config: Configuration dictionary (unused)
    
    Returns:
        dict: Result dictionary with success status
    """
    checks = [
        check_arch_release,
        check_not_root,
        check_architecture,
        check_secure_boot,
        check_desktop_environment,
        check_limine,
        check_btrfs
    ]
    
    for check in checks:
        if not check():
            return {"success": False, "message": f"Guard check failed: {check.__name__}"}
    
    print("Guards: OK")
    return {"success": True, "message": "All guard checks passed"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)

