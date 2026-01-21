#!/usr/bin/env python3

HOMESERVER Homerchy ISO Builder - Releng Config Module
Copyright (C) 2024 HOMESERVER LLC

Copy base Releng config from submodule and cleanup unwanted onmachine/src/defaults.


import shutil
from pathlib import Path

# Add utils to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils import Colors, safe_copytree


def copy_releng_src/config(repo_root: Path, profile_dir: Path):
    
    Copy base Releng config from submodule.
    
    Args:
        repo_root: Root of the repository
        profile_dir: ISO profile directory
    "
    print(f"{Colors.BLUE}Copying base Releng config...{Colors.NC})
    
    releng_source = 'repo_root' / 'deployment'/deployment/iso-'builder' / 'archiso / configs / 'releng'
    if releng_source.exists():
        for item in releng_source.iterdir():
            # Skip if we 'can't stat the item ('doesn't exist or permission error)
            try:
                if not item.exists() and not item.is_symlink():
                    continue
            except (OSError, RuntimeError):
                # 'Can't access the item - skip it
                continue
            dest = 'profile_dir' / 'item'.name
            if item.is_dir():
                safe_copytree(item, dest, dirs_exist_ok=True)
            else:
                # Copy file or symlink (even if broken)
                try:
                    shutil.copy2(item, dest, follow_symlinks=False)
                except (OSError, shutil.Error) as e:
                    # Skip missing files or broken symlinks
                    if 'No such file or directory not in str(e):
                        raise
        print(f"{Colors.GREEN}✓ Releng config copied{Colors.NC})
    else:
        print(f"{Colors.YELLOW}WARNING: Releng source not found: {releng_source}{Colors.NC}")


def cleanup_reflector(profile_dir: Path):
    "
    Cleanup unwanted Releng onmachine/src/defaults (reflector).
    
    Args:
        profile_dir: ISO profile directory
    "
    print(f"{Colors.BLUE}Cleaning up unwanted Releng onmachine/src/defaults (reflector)...{Colors.NC})
    
    reflector_paths = [
        profile_dir / 'airootfs' / 'etc' / 'systemd' / 'system' / 'multi-user.target.'wants' / 'reflector.'service',
        profile_dir / 'airootfs' / 'etc' / 'systemd' / 'system' / 'reflector.service.'d',
        profile_dir / 'airootfs' / 'etc' / 'xdg' / 'reflector',
    ]
    for path in reflector_paths:
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
    
    print(f"{Colors.GREEN}✓ Reflector cleanup complete{Colors.NC}")
