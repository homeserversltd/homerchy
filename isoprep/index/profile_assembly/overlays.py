#!/usr/bin/env python3
"""
HOMESERVER Homerchy ISO Builder - Custom Overlays Module
Copyright (C) 2024 HOMESERVER LLC

Apply Homerchy custom overlays to ISO profile.
"""

import re
import shutil
import sys
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils import Colors, safe_copytree, detect_vm_environment


def apply_custom_overlays(repo_root: Path, profile_dir: Path):
    """
    Apply Homerchy custom overlays to ISO profile.
    
    Args:
        repo_root: Root of the repository
        profile_dir: ISO profile directory
    """
    print(f"{Colors.BLUE}Applying Homerchy custom overlays...{Colors.NC}")
    
    # Note: We skip pacman.conf here because we'll configure it separately for build vs ISO
    # Also skip any pacman.conf files in subdirectories (like airootfs/etc/pacman.conf)
    configs_source = repo_root / 'iso-builder' / 'configs'
    if configs_source.exists():
        def should_skip_pacman_conf(src_path, dest_path):
            """Check if this is a pacman.conf file we should skip."""
            if src_path.name == 'pacman.conf':
                return True
            # Also skip pacman.conf in airootfs/etc/
            if 'airootfs' in str(src_path) and 'etc' in str(src_path) and src_path.name == 'pacman.conf':
                return True
            return False
        
        for item in configs_source.iterdir():
            # Skip pacman.conf at root level - we'll configure it separately
            if item.name == 'pacman.conf':
                continue
            # Skip if we can't stat the item (doesn't exist or permission error)
            try:
                if not item.exists() and not item.is_symlink():
                    continue
            except (OSError, RuntimeError):
                # Can't access the item - skip it
                continue
            dest = profile_dir / item.name
            if item.is_dir():
                # Use custom copytree that skips pacman.conf files
                def ignore_pacman_conf(dir_path, names):
                    """Ignore function to skip pacman.conf files."""
                    ignored = []
                    for name in names:
                        full_path = Path(dir_path) / name
                        if should_skip_pacman_conf(full_path, dest / name):
                            ignored.append(name)
                    return ignored
                safe_copytree(item, dest, dirs_exist_ok=True, ignore=ignore_pacman_conf)
            else:
                # Copy file or symlink (even if broken)
                try:
                    shutil.copy2(item, dest, follow_symlinks=False)
                except (OSError, shutil.Error) as e:
                    # Skip missing files or broken symlinks
                    if 'No such file or directory' not in str(e):
                        raise
        
        print(f"{Colors.GREEN}✓ Custom overlays applied{Colors.NC}")
    else:
        print(f"{Colors.YELLOW}WARNING: Configs source not found: {configs_source}{Colors.NC}")


def adjust_vm_boot_timeout(profile_dir: Path):
    """
    Detect VM environment and adjust boot timeout.
    
    Args:
        profile_dir: ISO profile directory
    """
    is_vm = detect_vm_environment()
    if is_vm:
        print(f"{Colors.BLUE}VM detected - adjusting boot timeout{Colors.NC}")
        syslinux_cfg = profile_dir / 'syslinux' / 'archiso_sys.cfg'
        if syslinux_cfg.exists():
            content = syslinux_cfg.read_text()
            content = re.sub(r'^TIMEOUT \d+', 'TIMEOUT 0', content, flags=re.MULTILINE)
            syslinux_cfg.write_text(content)
            print(f"{Colors.GREEN}Boot timeout set to 0 for instant VM boot{Colors.NC}")

