#!/usr/bin/env python3
"""
HOMESERVER Homerchy ISO Builder - Source Injection Module
Copyright (C) 2024 HOMESERVER LLC

Inject current repository source into ISO profile.
"""

import shutil
from pathlib import Path

# Add utils to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils import Colors, guaranteed_copytree


def inject_repository_source(repo_root: Path, profile_dir: Path):
    """
    Inject current repository source into ISO profile.
    
    This allows the ISO to contain the latest changes from this workspace.
    Use guaranteed copy to ensure all new/changed files are transferred.
    
    Args:
        repo_root: Root of the repository
        profile_dir: ISO profile directory
    """
    print(f"{Colors.BLUE}Injecting current repository source...{Colors.NC}")
    homerchy_target = profile_dir / 'airootfs' / 'root' / 'homerchy'
    homerchy_target.mkdir(parents=True, exist_ok=True)
    
    # Copy excluding build artifacts and .git
    exclude_patterns = ['isoprep/work', 'isoprep/isoout', '.git']
    
    for item in repo_root.iterdir():
        if item.name in ['isoprep', '.git', '.build-swap']:
            continue
        # Skip if we can't stat the item (doesn't exist or permission error)
        try:
            if not item.exists() and not item.is_symlink():
                continue
        except (OSError, RuntimeError):
            # Can't access the item - skip it
            continue
        dest = homerchy_target / item.name
        
        # Use guaranteed copy to ensure all files are transferred and updated
        if item.is_dir():
            # guaranteed_copytree ensures all files are copied/updated
            guaranteed_copytree(item, dest, ignore=shutil.ignore_patterns('.git'))
        else:
            # For files, copy if source is newer or destination doesn't exist
            if not dest.exists() or item.stat().st_mtime > dest.stat().st_mtime:
                try:
                    shutil.copy2(item, dest, follow_symlinks=False)
                except (OSError, PermissionError, shutil.Error) as e:
                    # Skip files that can't be accessed (permission denied, missing, broken symlinks)
                    if 'Permission denied' in str(e) or 'PermissionError' in str(type(e).__name__):
                        # Silently skip files we can't read (like .build-swap owned by root)
                        continue
                    elif 'No such file or directory' not in str(e):
                        raise
    
    # Create symlink for backward compatibility (installer expects /root/omarchy)
    omarchy_link = profile_dir / 'airootfs' / 'root' / 'omarchy'
    if not omarchy_link.exists():
        # Use relative symlink - installer code expects /root/omarchy
        omarchy_link.symlink_to('homerchy')
    
    print(f"{Colors.GREEN}✓ Repository source injected{Colors.NC}")


def inject_vm_profile(repo_root: Path, profile_dir: Path):
    """
    Inject VM profile settings.
    
    Args:
        repo_root: Root of the repository
        profile_dir: ISO profile directory
    """
    print(f"{Colors.BLUE}Injecting VM profile settings...{Colors.NC}")
    
    vmtools_dir = profile_dir / 'airootfs' / 'root' / 'vmtools'
    vmtools_dir.mkdir(parents=True, exist_ok=True)
    
    index_source = repo_root / 'vmtools' / 'index.json'
    if index_source.exists():
        shutil.copy2(index_source, vmtools_dir / 'index.json')
        print(f"{Colors.GREEN}✓ Copied VM profile: {index_source} -> {vmtools_dir / 'index.json'}{Colors.NC}")
    else:
        print(f"{Colors.YELLOW}⚠ VM profile not found: {index_source}{Colors.NC}")


def customize_package_list(profile_dir: Path):
    """
    Customize package list, ensuring syslinux is included.
    
    Args:
        profile_dir: ISO profile directory
    """
    print(f"{Colors.BLUE}Customizing package list...{Colors.NC}")
    
    packages_file = profile_dir / 'packages.x86_64'
    # Ensure syslinux is in the package list (required for BIOS boot)
    # Read existing content, add syslinux if missing, then append custom packages
    if packages_file.exists():
        content = packages_file.read_text()
        lines = [line.strip() for line in content.split('\n') if line.strip() and not line.strip().startswith('#')]
        # Check if syslinux is already in the file (case-insensitive)
        has_syslinux = any('syslinux' in line.lower() for line in lines)
        if not has_syslinux:
            # Add syslinux before appending other packages
            with open(packages_file, 'a') as f:
                f.write('syslinux\n')
    else:
        # File doesn't exist - create it with syslinux
        packages_file.write_text('syslinux\n')
    
    # Append custom packages
    with open(packages_file, 'a') as f:
        f.write('git\ngum\njq\nopenssl\n')
    
    print(f"{Colors.GREEN}✓ Package list customized{Colors.NC}")


def fix_permissions_targets(repo_root: Path, profile_dir: Path):
    """
    Fix permissions targets and copy utility scripts.
    
    Args:
        repo_root: Root of the repository
        profile_dir: ISO profile directory
    """
    print(f"{Colors.BLUE}Fixing permissions targets...{Colors.NC}")
    
    cache_dir = profile_dir / 'airootfs' / 'var' / 'cache' / 'omarchy' / 'mirror' / 'offline'
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    bin_dir = profile_dir / 'airootfs' / 'usr' / 'local' / 'bin'
    bin_dir.mkdir(parents=True, exist_ok=True)
    
    upload_log_source = repo_root / 'bin' / 'omarchy-upload-log'
    if upload_log_source.exists():
        shutil.copy2(upload_log_source, bin_dir / 'omarchy-upload-log')
        (bin_dir / 'omarchy-upload-log').chmod(0o755)
        print(f"{Colors.GREEN}✓ Copied omarchy-upload-log utility{Colors.NC}")

