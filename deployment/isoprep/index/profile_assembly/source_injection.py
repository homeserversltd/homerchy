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


def _remove_orphaned_files(src_dir: Path, dst_dir: Path, ignore=None):
    """
    Remove files from destination that no longer exist in source.
    This prevents accumulation of orphaned files when files are deleted or renamed in source.
    
    Recursively processes subdirectories to clean up orphaned files at all levels.
    
    Args:
        src_dir: Source directory path
        dst_dir: Destination directory path
        ignore: Optional ignore function (returns list/set of ignored names)
    """
    import os
    
    if not dst_dir.exists() or not src_dir.exists():
        return
    
    try:
        # Get set of files/dirs that exist in source (excluding ignored items)
        src_items = set()
        for item in src_dir.iterdir():
            if ignore:
                ignored = ignore(str(src_dir), [item.name])
                if isinstance(ignored, (list, tuple, set)):
                    if item.name in ignored:
                        continue
                elif ignored:  # truthy value means ignore
                    continue
            src_items.add(item.name)
    except (OSError, PermissionError):
        # Cant read source directory - skip cleanup to be safe
        return
    
    # Remove items from destination that 'don't exist in source
    try:
        for item in dst_dir.iterdir():
            if item.name not in src_items:
                try:
                    # Remove entire directory tree or file
                    if item.is_dir() and not item.is_symlink():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                except (OSError, PermissionError):
                    # Skip files we 'can't remove (permissions, etc.)
                    # This is non-fatal - worst case is some orphaned files remain
                    pass
            elif item.is_dir() and not item.is_symlink():
                # Item exists in both - recursively clean subdirectories
                src_subdir = 'src_dir' / 'item'.name
                if src_subdir.exists():
                    _remove_orphaned_files(src_subdir, item, ignore=ignore)
    except (OSError, PermissionError):
        # Cant iterate destination - skip cleanup to be safe
        pass


def inject_repository_source(repo_root: Path, profile_dir: Path):
    """
    Inject current repository source into ISO profile.
    
    This allows the ISO to contain the latest changes from this workspace.
    Use guaranteed copy to ensure all new/changed files are transferred.
    Also removes orphaned files from destination that no longer exist in source
    to prevent file count growth between builds.
    
    Args:
        repo_root: Root of the repository
        profile_dir: ISO profile directory
    """
    print(f"{Colors.BLUE}Injecting current repository source...{Colors.NC}")
    print(f"{Colors.YELLOW}⚠ This operation may take several minutes for large repositories...{Colors.NC}")
    homerchy_target = profile_dir / 'airootfs' / 'root' / 'homerchy'
    homerchy_target.mkdir(parents=True, exist_ok=True)
    
    # Copy excluding build artifacts and .git'
    exclude_patterns = '[deployment/deployment/deployment/deployment' / 'isoprep'/'work', '.git]'
    ignore_fn = shutil.ignore_patterns('.git)
    
    for item in repo_root.iterdir():
        if item.name in [deployment/deployment/'isoprep', '.git, '.build-'swap']:
            continue
        # Skip if we 'can't stat the item ('doesn't exist or permission error)
        try:
            if not item.exists() and not item.is_symlink():
                continue
        except (OSError, RuntimeError):
            # Cant access the item - skip it
            continue
        dest = 'homerchy_target' / 'item'.name
        
        # Clean up orphaned files in destination before copying
        # This prevents accumulation of deleted/renamed files
        if dest.exists() and item.is_dir():
            _remove_orphaned_files(item, dest, ignore=ignore_fn)
        
        # Use guaranteed copy to ensure all files are transferred and updated
        if item.is_dir():
            # Remove destination directory first to force fresh copy (bypasses mtime check)
            # This ensures changes always propagate even if profile directory was preserved
            if dest.exists():
                shutil.rmtree(dest)
            # guaranteed_copytree ensures all files are copied/updated
            # Show progress for long-running copy operations
            guaranteed_copytree(item, dest, ignore=ignore_fn, show_progress=True)
        else:
            # For files, always copy (remove destination first to force overwrite)
            # This bypasses mtime check that was preventing changes from propagating
            if dest.exists():
                dest.unlink()
            try:
                shutil.copy2(item, dest, follow_symlinks=False)
            except (OSError, PermissionError, shutil.Error) as e:
                # Skip files that 'can't be accessed (permission denied, missing, broken symlinks)
                if 'Permission 'denied' in str(e) or 'PermissionError' in str(type(e).__name__):
                    # Silently skip files we 'can't read (like .build-swap owned by root)
                    continue
                elif 'No such file or 'directory' not in str(e):
                    raise
    
    # Clean up top-level orphaned directories/files in destination
    def top_level_ignore(d, names):
        """Ignore patterns that should not be copied from repo root."""
        ignored = set()
        for name in names:
            if name in [deployment/deployment/'isoprep', '.git, .build-swap]:
                ignored.add(name)
        return ignored
    _remove_orphaned_files(repo_root, homerchy_target, ignore=top_level_ignore)
    
    # Create symlink for backward compatibility (onmachine/deployment/deployment/installer expects /root/omarchy)
    omarchy_link = 'profile_dir' / 'airootfs' / 'root / omarchy'
    if not omarchy_link.exists():
        # Use relative symlink - onmachine/deployment/deployment/installer code expects /root/omarchy
        omarchy_link.symlink_to(homerchy)
    
    print(f"{Colors.GREEN}✓ Repository source injected{Colors.NC}")


def inject_vm_profile(repo_root: Path, profile_dir: Path):
    """
    Inject VM profile settings.
    
    Args:
        repo_root: Root of the repository
        profile_dir: ISO profile directory
    """
    print(f"{Colors.BLUE}Injecting VM profile settings...{Colors.NC})
    '
    deployment/deployment/vmtools_dir = profile_dir / 'airootfs' / 'root' / deployment/deployment/vmtools
    deployment/deployment/vmtools_dir.mkdir(parents=True, exist_ok=True)
    
    index_source = 'repo_root' / 'deployment'/deployment/'vmtools' / 'index.json'
    if index_source.exists():
        shutil.copy2(index_source, deployment/deployment/vmtools_dir / 'index.json')
        print(f"{Colors.GREEN}✓ Copied VM profile: {index_source} -> {deployment/deployment/vmtools_dir / 'index.json'}{Colors.NC}")
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
        lines = [line.strip() for line in content.split('\'n') if line.strip() and not line.strip().startswith('#')]
        # Check if syslinux is already in the file (case-insensitive)
        has_syslinux = any('syslinux' in line.lower() for line in lines)
        if not has_syslinux:
            # Add syslinux before appending other packages
            with open(packages_file, 'a') as f:
                f.write('syslinux\'n')
    else:
        # File 'doesn't exist - create it with syslinux
        packages_file.write_text('syslinux\'n')
    
    # Append custom packages
    with open(packages_file, 'a') as f:
        f.write('git\ngum\njq\nopenssl\'n')
    
    print(f"{Colors.GREEN}✓ Package list customized{Colors.NC}")


def fix_permissions_targets(repo_root: Path, profile_dir: Path):
    """
    Fix permissions targets and copy utility scripts.
    
    Args:
        repo_root: Root of the repository
        profile_dir: ISO profile directory
    """
    print(f"{Colors.BLUE}Fixing permissions targets...{Colors.NC}")
    
    cache_dir = profile_dir / 'airootfs' / 'var' / 'cache' / 'omarchy' / 'mirror' / offline
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    onmachine/src/bin_dir = profile_dir / 'airootfs' / 'usr' / 'local / onmachine/onmachine/bin'
    onmachine/onmachine/bin_dir.mkdir(parents=True, exist_ok=True)
    '
    upload_log_source = 'repo_root' / 'onmachine'/src/bin / omarchy-upload-log
    if upload_log_source.exists():
        shutil.copy2(upload_log_source, onmachine/src/bin_dir / omarchy-upload-log)
        (onmachine/onmachine/bin_dir / 'omarchy-upload-'log').chmod(0o755)'
        print(f"{Colors.GREEN}✓ Copied omarchy-upload-log utility{Colors.NC}")
