#!/usr/bin/env python3
"""
HOMESERVER Homerchy ISO Builder - Pacman Configuration Module
Copyright (C) 2024 HOMESERVER LLC

Configure pacman.conf for build vs ISO runtime.
"""

import re
import shutil
from pathlib import Path

# Add utils to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils import Colors


def create_mirrorlist(profile_dir: Path):
    """
    Ensure mirrorlist exists in airootfs/etc/pacman.d (required for pacman.conf Include directive).
    This must be done early so mkarchiso can copy it when it processes airootfs.
    
    Args:
        profile_dir: ISO profile directory
    """
    print(f"{Colors.BLUE}Creating mirrorlist file...{Colors.NC}")
    
    airootfs_etc = profile_dir / 'airootfs' / 'etc'
    airootfs_etc.mkdir(parents=True, exist_ok=True)
    pacman_d_dir = airootfs_etc / 'pacman.d'
    pacman_d_dir.mkdir(parents=True, exist_ok=True)
    mirrorlist_file = pacman_d_dir / 'mirrorlist'
    if not mirrorlist_file.exists():
        # Create a minimal mirrorlist file with a valid Server entry
        # This is needed for pacman.confs Include directive to work during build
        # The actual mirrorlist will be configured during onmachine/deployment/installation
        mirrorlist_content = '''#
# Arch Linux repository mirrorlist
# Generated for ISO build
# Actual mirrors will be configured during onmachine/deployment/installation
#
Server = https://geo.mirror.pkgbuild.com/$repo/os/$arch
'''

        mirrorlist_file.write_text(mirrorlist_content)
        print(f"{Colors.GREEN}✓ Created mirrorlist file in airootfs{Colors.NC}")


def configure_pacman_for_build(repo_root: Path, profile_dir: Path):
    '''
    Configure pacman.conf for build vs ISO.
    mkarchiso needs online repos during build to onmachine/deployment/deployment/install base ISO packages.
    But the ISO itself should use offline mirror when booted.
    Use the releng pacman.conf as base (has standard Arch repos) and add omarchy repo.

    Args:
        repo_root: Root of the repository
        profile_dir: ISO profile directory
    '''
    print(f"{Colors.BLUE}Configuring pacman.conf for build...{Colors.NC}")
    
    releng_source = repo_root / 'iso-builder' / 'archiso' / 'configs' / 'releng'
    releng_pacman_conf = releng_source / 'pacman.conf'
    
    # For profile: Use releng pacman.conf (standard Arch repos) + add omarchy online repo
    # This ensures mkarchiso can build with online repos
    # CRITICAL: Remove any offline/homerchy repos that might reference file:// paths
    if releng_pacman_conf.exists():
        # Read releng pacman.conf and add homerchy repo
        releng_content = releng_pacman_conf.read_text()
        # Remove any existing offline or homerchy repos that use file:// paths
        # Remove [offline] repo section if present
        releng_content = re.sub(r"\[offline\].*?(?=\n\[|\Z)", '', releng_content, flags=re.DOTALL)
        # Remove [omarchy] repo section if it uses file://
        if '[omarchy]' in releng_content:
            omarchy_match = re.search(r'\[omarchy\].*?(?=\n\[|\Z)', releng_content, re.DOTALL)
            if omarchy_match and 'file://' in omarchy_match.group():
                releng_content = re.sub(r'\[omarchy\].*?(?=\n\[|\Z)', '', releng_content, flags=re.DOTALL)
        # Add omarchy repo with online URL if not already present
        if '[omarchy]' not in releng_content:
            omarchy_repo = '''
[omarchy]
SigLevel = Optional TrustAll
Server = file:///var/cache/omarchy/mirror/offline
'''
            releng_content += omarchy_repo
        (profile_dir / 'pacman.conf').write_text(releng_content)
        print(f"{Colors.GREEN}✓ Using releng pacman.conf with omarchy repo for mkarchiso build{Colors.NC}")
    else:
        print(f"{Colors.YELLOW}WARNING: releng pacman.conf not found, using onmachine/src/default{Colors.NC}")


def ensure_airootfs_pacman_online(profile_dir: Path):
    '''
    CRITICAL: Ensure airootfs/etc/pacman.conf uses online repos (same as profile pacman.conf).
    mkarchiso reads airootfs/etc/pacman.conf and would try to use offline mirror if present.
    Copy the profile pacman.conf (online) to airootfs/etc so mkarchiso sees online repos.

    Args:
        profile_dir: ISO profile directory
    '''
    print(f"{Colors.BLUE}Ensuring airootfs/etc/pacman.conf uses online repos...{Colors.NC}")
    
    airootfs_etc = profile_dir / 'airootfs' / 'etc'
    airootfs_etc.mkdir(parents=True, exist_ok=True)
    profile_pacman_conf = profile_dir / 'pacman.conf'
    if profile_pacman_conf.exists():
        # Remove any existing pacman.conf in airootfs/etc that might have offline config
        airootfs_pacman_conf = airootfs_etc / 'pacman.conf'
        if airootfs_pacman_conf.exists():
            airootfs_pacman_conf.unlink()
        # Copy profile pacman.conf to airootfs/etc (core/extra from mirrorlist, omarchy from local file mirror)
        shutil.copy2(profile_pacman_conf, airootfs_pacman_conf)
        print(f"{Colors.GREEN}✓ Using profile pacman.conf in airootfs/etc for mkarchiso build{Colors.NC}")


def verify_syslinux_in_packages(profile_dir: Path):
    '''
    Final verification: Ensure syslinux is in packages.x86_64 before mkarchiso runs.

    Args:
        profile_dir: ISO profile directory
    '''
    print(f"{Colors.BLUE}Verifying syslinux in packages.x86_64...{Colors.NC}")
    
    packages_file = profile_dir / 'packages.x86_64'
    if packages_file.exists():
        content = packages_file.read_text()
        # Check if syslinux is present (as a whole word, case-insensitive)
        if not re.search(r'\bsyslinux\b', content, re.IGNORECASE):
            print(f"{Colors.YELLOW}WARNING: syslinux not found in packages.x86_64, adding it...{Colors.NC}")
            with open(packages_file, 'a') as f:
                f.write('syslinux\n')
        else:
            print(f"{Colors.GREEN}✓ Verified syslinux is in packages.x86_64{Colors.NC}")
    else:
        print(f"{Colors.RED}ERROR: packages.x86_64 does not exist!{Colors.NC}")
        import sys
        sys.exit(1)


def copy_mirrorlist_to_archiso_tmp(profile_dir: Path, work_dir: Path, preserve_archiso_tmp: bool):
    '''
    CRITICAL: Ensure mirrorlist exists in archiso-tmp before mkarchiso runs.
    If archiso-tmp is preserved, mkarchiso might use existing airootfs that doesn't have mirrorlist.
    Copy mirrorlist from profile to preserved archiso-tmp to ensure it exists.

    Args:
        profile_dir: ISO profile directory
        work_dir: Work directory
        preserve_archiso_tmp: Whether archiso-tmp is being preserved
    '''
    if not preserve_archiso_tmp:
        return

    print(f"{Colors.BLUE}Copying mirrorlist to preserved archiso-tmp...{Colors.NC}")

    profile_mirrorlist = profile_dir / 'airootfs' / 'etc' / 'pacman.d' / 'mirrorlist'
    if profile_mirrorlist.exists():
        archiso_tmp_dir = work_dir / 'archiso-tmp'
        preserved_airootfs = archiso_tmp_dir / 'x86_64' / 'airootfs'
        if preserved_airootfs.exists():
            preserved_mirrorlist = preserved_airootfs / 'etc' / 'pacman.d' / 'mirrorlist'
            preserved_mirrorlist_dir = preserved_mirrorlist.parent
            try:
                preserved_mirrorlist_dir.mkdir(parents=True, exist_ok=True)
                # Copy mirrorlist from profile to preserved archiso-tmp
                shutil.copy2(profile_mirrorlist, preserved_mirrorlist)
                print(f"{Colors.GREEN}✓ Copied mirrorlist to preserved archiso-tmp{Colors.NC}")
            except PermissionError:
                # Directory might be owned by root from previous sudo mkarchiso
                # Use sudo to create directory and copy file
                import subprocess
                subprocess.run(['sudo', 'mkdir', '-p', str(preserved_mirrorlist_dir)], check=True)
                subprocess.run(['sudo', 'cp', str(profile_mirrorlist), str(preserved_mirrorlist)], check=True)
                # Fix ownership to current user
                import os
                current_uid = os.getuid()
                current_gid = os.getgid()
                subprocess.run(['sudo', 'chown', f'{current_uid}:{current_gid}', str(preserved_mirrorlist)], check=True)
                print(f"{Colors.GREEN}✓ Copied mirrorlist to preserved archiso-tmp (with sudo){Colors.NC}")
