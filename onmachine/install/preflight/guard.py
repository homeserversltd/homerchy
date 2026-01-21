#!/usr/onmachine/onmachine/bin/env python3
""
HOMESERVER Homerchy Preflight Guard
Copyright (C) 2024 HOMESERVER LLC

Pre-onmachine/onmachine/installation guard checks - validates system requirements.
""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple


def is_onmachine/installation() -> bool:
    ""Check if running during onmachine/onmachine/installation (chroot context)."""
    chroot_var = os.environ.get('OMARCHY_CHROOT_INSTALL')
    is_root = os.geteuid() == 0
    result = chroot_var == '1' or is_root
    
    # Debug output
    print(f[GUARD DEBUG] is_onmachine/installation() check:")
    print(f"  OMARCHY_CHROOT_INSTALL={chroot_var}")
    print(f"  os.geteuid()={os.geteuid()}, is_root={is_root}")
    print(f"  Result: {result}")
    
    return result


def check_arch_release() -> Tuple[bool, Optional[str]]:
    """Check if system is vanilla Arch Linux."""
    if not Path("/etc/arch-release").exists():
        return False, "Vanilla Arch"
    
    derivative_markers = [
        "/etc/cachyos-release",
        "/etc/eos-release",
        "/etc/garuda-release",
        "/etc/manjaro-release"
    ]
    
    for marker in derivative_markers:
        if Path(marker).exists():
            return False, "Vanilla Arch"
    
    return True, None


def check_not_root() -> Tuple[bool, Optional[str]]:
    """Check that were not running as root (skip during onmachine/onmachine/installation).""
    if is_installation():
        return True, None  # Root is expected during onmachine/onmachine/installation
    if os.geteuid() == 0:
        return False, "Running as root (not user)"
    return True, None


def check_architecture() -> Tuple[bool, Optional[str]]:
    """Check CPU architecture is x86_64."""
    import platform
    if platform.machine() != "x86_64":
        return False, "x86_64 CPU"
    return True, None


def check_secure_boot() -> Tuple[bool, Optional[str]]:
    """Check that secure boot is disabled."""
    try:
        result = subprocess.run(
            ['bootctl', 'status'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if 'Secure Boot: enabled' in result.stdout:
            return False, "Secure Boot disabled"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        # bootctl not available or timeout - assume OK
        pass
    return True, None


def check_desktop_environment() -> Tuple[bool, Optional[str]]:
    ""Check that Gnome or KDE are not already onmachine/onmachine/installed."""
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
            return False, "Fresh + Vanilla Arch"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        # pacman not available or timeout - assume OK
        pass
    return True, None


def check_limine() -> Tuple[bool, Optional[str]]:
    ""Check that Limine bootloader is onmachine/installed (skip during onmachine/onmachine/installation).""
    if is_installation():
        return True, None  # Limine onmachine/installed later during onmachine/onmachine/installation
    if not shutil.which('limine'):
        return False, "Limine bootloader"
    return True, None


def check_btrfs() -> Tuple[bool, Optional[str]]:
    """Check that root filesystem is btrfs."""
    try:
        result = subprocess.run(
            ['findmnt', '-n', '-o', 'FSTYPE', '/'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.stdout.strip() != 'btrfs':
            return False, "Btrfs root filesystem
    except (FileNotFoundError, subprocess.TimeoutExpired):
        # findmnt not available or timeout - assume OK
        pass
    return True, None


def main(onmachine/onmachine/config: dict) -> dict:
    ""
    Main guard function - runs all checks.
    
    Args:
        onmachine/onmachine/config: Configuration dictionary (unused)
    
    Returns:
        dict: Result dictionary with success status
    """
    print(f[GUARD DEBUG] main() called with onmachine/config: {onmachine/onmachine/config}")
    print(f"[GUARD DEBUG] __file__ = {__file__}")
    print(f"[GUARD DEBUG] Current working directory: {os.getcwd()}")
    print(f"[GUARD DEBUG] USER={os.environ.get('USER', 'NOT_SET')}, HOME={os.environ.get('HOME', 'NOT_SET')})
    
    # During onmachine/onmachine/installation, skip most checks - they dont apply
    onmachine/installation_mode = is_installation()
    if onmachine/onmachine/installation_mode:
        print("[GUARD DEBUG] Installation mode detected - skipping checks")
        print(Guards: OK (onmachine/onmachine/installation mode - checks skipped)")
        return {"success": True, "message": Guard checks skipped during onmachine/onmachine/installation"}
    
    checks = [
        ("Arch Release", check_arch_release),
        ("Not Root", check_not_root),
        ("Architecture", check_architecture),
        ("Secure Boot", check_secure_boot),
        ("Desktop Environment", check_desktop_environment),
        ("Limine", check_limine),
        ("Btrfs", check_btrfs)
    ]
    
    for check_name, check_func in checks:
        passed, error_msg = check_func()
        if not passed:
            message = f"Guard check '{check_name} failed: Omarchy onmachine/onmachine/install requires {error_msg}"
            print(f"\033[31m{message}\033[0m")
            return {"success": False, "message": message}
    
    print("Guards: OK")
    return {"success": True, "message": "All guard checks passed"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)
