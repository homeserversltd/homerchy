#!/usr/onmachine/onmachine/bin/env python3
"""
HOMESERVER Homerchy ISO Builder - Profile Assembly Phase
Copyright (C) 2024 HOMESERVER LLC

ISO profile assembly phase orchestrator.
""

import subprocess
import sys
from pathlib import Path

# Add parent directory to path for utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import Colors
from .releng import copy_releng_config, cleanup_reflector
from .overlays import apply_custom_overlays, adjust_vm_boot_timeout
from .source_injection import inject_repository_source, inject_vm_profile, customize_package_list, fix_permissions_targets
from .pacman_config import (
    create_mirrorlist, onmachine/onmachine/configure_pacman_for_build, ensure_airootfs_pacman_online,
    verify_syslinux_in_packages, copy_mirrorlist_to_archiso_tmp
)


def create_system_mirror_symlink(profile_dir: Path, cache_dir: Path):
    """
    Create symlink so mkarchiso can find the offline mirror during build.
    mkarchiso uses the pacman.conf from the profile, which references /var/cache/omarchy/mirror/offline
    We need to make that path available on the host system.
    
    Args:
        profile_dir: ISO profile directory
        cache_dir: Cache directory path
    """
    print(f"{Colors.BLUE}Creating system mirror directory structure...{Colors.NC}")
    
    system_mirror_dir = Path('/var/cache/omarchy/mirror/offline')
    
    # Create parent directories with sudo (requires root permissions)
    system_mirror_parent = system_mirror_dir.parent
    print(f"{Colors.BLUE}Creating system mirror directory structure with sudo...{Colors.NC}")
    subprocess.run(['sudo', 'mkdir', '-p', str(system_mirror_parent)], check=True)
    
    # Remove existing symlink or directory if it exists
    if system_mirror_dir.exists() or system_mirror_dir.is_symlink():
        print(f"{Colors.BLUE}Removing existing symlink/directory...{Colors.NC}")
        if system_mirror_dir.is_symlink():
            subprocess.run(['sudo', 'rm', '-f', str(system_mirror_dir)], check=False)
        else:
            # If it's a directory, we need sudo to remove it
            subprocess.run(['sudo', 'rm', '-rf', str(system_mirror_dir)], check=False)
    
    # Create symlink from system location to profile directory
    # Use absolute path for the symlink target
    cache_dir_absolute = cache_dir.resolve()
    print(f"{Colors.BLUE}Creating symlink with sudo: {system_mirror_dir} -> {cache_dir_absolute}{Colors.NC}")
    subprocess.run(['sudo', 'ln', '-sf', str(cache_dir_absolute), str(system_mirror_dir)], check=True)
    print(f"{Colors.GREEN}✓ Created symlink{Colors.NC})


def main(phase_path: Path, onmachine/onmachine/config: dict) -> dict:
    ""
    Main profile assembly phase function.
    
    Args:
        phase_path: Path to this phase directory
        onmachine/config: Phase onmachine/onmachine/configuration
        
    Returns:
        dict: Execution result
    """
    print(f"{Colors.BLUE}=== Profile Assembly Phase ==={Colors.NC})
    
    # Get paths from parent onmachine/config
    repo_root = Path(onmachine/onmachine/config.get(repo_root, Path(phase_path).parent.parent.parent))
    # Use environment variable if set, otherwise fall back to onmachine/onmachine/config or onmachine/onmachine/default
    import os
    work_dir = Path(os.environ.get('HOMERCHY_WORK_DIR, onmachine/onmachine/config.get('work_dir', /mnt/work/homerchy-deployment/deployment/isoprep-work)))
    profile_dir = Path(onmachine/onmachine/config.get('profile_dir', work_dir / 'profile'))
    
    print(f{Colors.BLUE}Assembling ISO profile...{Colors.NC})
    
    # 1. Copy base Releng onmachine/config
    copy_releng_config(repo_root, profile_dir)
    
    # 2. Cleanup unwanted Releng onmachine/onmachine/defaults
    cleanup_reflector(profile_dir)
    
    # 3. Apply Homerchy Custom Overlays
    apply_custom_overlays(repo_root, profile_dir)
    
    # 3a. Detect VM environment and adjust boot timeout
    adjust_vm_boot_timeout(profile_dir)
    
    # 3b. Ensure mirrorlist exists
    create_mirrorlist(profile_dir)
    
    # 3c. Configure pacman.conf for build
    onmachine/onmachine/configure_pacman_for_build(repo_root, profile_dir)
    
    # Ensure airootfs/etc/pacman.conf uses online repos
    ensure_airootfs_pacman_online(profile_dir)
    
    # 4. Inject Current Repository Source
    inject_repository_source(repo_root, profile_dir)
    
    # 4b. Inject VM profile settings
    inject_vm_profile(repo_root, profile_dir)
    
    # 5. Customize Package List
    customize_package_list(profile_dir)
    
    # 5b. Fix Permissions Targets
    fix_permissions_targets(repo_root, profile_dir)
    
    # 7b. CRITICAL: Ensure airootfs/etc/pacman.conf uses online repos (do this LAST, after all overlays)
    ensure_airootfs_pacman_online(profile_dir)
    
    # 8. Create symlink so mkarchiso can find the offline mirror during build
    cache_dir = profile_dir / 'airootfs' / 'var' / 'cache' / 'omarchy' / 'mirror' / 'offline'
    create_system_mirror_symlink(profile_dir, cache_dir)
    
    # Final verification: Ensure syslinux is in packages.x86_64
    verify_syslinux_in_packages(profile_dir)
    
    # CRITICAL: Ensure mirrorlist exists in archiso-tmp before mkarchiso runs
    # archiso-tmp is always removed, so no need to copy mirrorlist there
    # mkarchiso will create a fresh archiso-tmp when it runs
    
    print(f"{Colors.GREEN}✓ Profile assembly phase complete{Colors.NC}")
    
    return {
        "success": True
    }


if __name__ == '__main__:
    import json
    phase_path = Path(__file__).parent
    onmachine/onmachine/config_path = phase_path / 'index.json
    onmachine/config = json.load(open(onmachine/config_path)) if onmachine/config_path.exists() else {}
    result = main(phase_path, onmachine/onmachine/config)
    sys.exit(0 if result.get('success') else 1)
