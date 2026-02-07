#!/usr/bin/env python3
"""
HOMESERVER Homerchy Preflight Guard
Copyright (C) 2024 HOMESERVER LLC

Pre-installation guard checks - validates system requirements.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple


def is_installation() -> bool:
    """Check if running during installation (chroot context)."""
    chroot_var = os.environ.get('HOMERCHY_CHROOT_INSTALL')
    is_root = os.geteuid() == 0
    result = chroot_var == '1' or is_root
    print(f"[GUARD DEBUG] is_installation() check:")
    print(f"  HOMERCHY_CHROOT_INSTALL={chroot_var}")
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
    """Check that we're not running as root (skip during installation)."""
    if is_installation():
        return True, None
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
        if result.returncode == 0 and 'Secure Boot: enabled' in result.stdout:
            return False, "Secure Boot disabled"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return True, None


def check_desktop_environment() -> Tuple[bool, Optional[str]]:
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
            return False, "Fresh + Vanilla Arch"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return True, None


def check_limine() -> Tuple[bool, Optional[str]]:
    """Check that Limine bootloader is installed (skip during installation)."""
    if is_installation():
        return True, None
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
        if result.returncode == 0 and result.stdout.strip() != 'btrfs':
            return False, "Btrfs root filesystem"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return True, None


def main(config: dict) -> dict:
    """
    Main guard function - runs all checks.

    Args:
        config: Configuration dictionary (unused)

    Returns:
        dict: Result dictionary with success status
    """
    print("[GUARD DEBUG] main() called with config:", config)
    print("[GUARD DEBUG] __file__ =", __file__)
    print("[GUARD DEBUG] Current working directory:", os.getcwd())
    print("[GUARD DEBUG] USER=%s, HOME=%s" % (os.environ.get('USER', 'NOT_SET'), os.environ.get('HOME', 'NOT_SET')))

    installation_mode = is_installation()
    if installation_mode:
        print("[GUARD DEBUG] Installation mode detected - skipping checks")
        print("Guards: OK (installation mode - checks skipped)")
        return {"success": True, "message": "Guard checks skipped during installation"}

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
            message = "Guard check %s failed: Homerchy install requires %s" % (check_name, error_msg)
            print("\033[31m%s\033[0m" % message)
            return {"success": False, "message": message}

    print("Guards: OK")
    return {"success": True, "message": "All guard checks passed"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)
