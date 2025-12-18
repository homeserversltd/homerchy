#!/usr/bin/env python3
"""
HOMESERVER Homerchy ISO Builder - Prepare Phase
Copyright (C) 2024 HOMESERVER LLC

Setup and validation phase for ISO build process.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Add parent directory to path for utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import Colors, check_dependencies


def main(phase_path: Path, config: dict) -> dict:
    """
    Main prepare phase function.
    
    Args:
        phase_path: Path to this phase directory
        config: Phase configuration
        
    Returns:
        dict: Execution result
    """
    print(f"{Colors.BLUE}=== Prepare Phase: Setup and Validation ==={Colors.NC}")
    
    # Get paths from parent config
    repo_root = Path(config.get('repo_root', Path(phase_path).parent.parent.parent))
    # Use environment variable if set, otherwise fall back to config or default
    work_dir = Path(os.environ.get('HOMERCHY_WORK_DIR', config.get('work_dir', '/mnt/work/homerchy-isoprep-work')))
    out_dir = Path(config.get('out_dir', work_dir / 'isoout'))
    profile_dir = Path(config.get('profile_dir', work_dir / 'profile'))
    
    # Check dependencies
    print(f"{Colors.BLUE}Checking dependencies...{Colors.NC}")
    check_dependencies()
    print(f"{Colors.GREEN}✓ Dependencies satisfied{Colors.NC}")
    
    # Ensure output directory exists
    print(f"{Colors.BLUE}Ensuring output directory exists...{Colors.NC}")
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"{Colors.GREEN}✓ Output directory ready: {out_dir}{Colors.NC}")
    
    # Ensure work directory exists (in dedicated tmpfs for build isolation)
    print(f"{Colors.BLUE}Ensuring work directory exists (in dedicated build tmpfs)...{Colors.NC}")
    work_dir.mkdir(parents=True, exist_ok=True)
    print(f"{Colors.GREEN}✓ Work directory ready: {work_dir}{Colors.NC}")
    
    # Clean up profile directory (but preserve caches unless full clean)
    print(f"{Colors.BLUE}Preparing profile directory...{Colors.NC}")
    
    # Check for full clean mode
    full_clean = os.environ.get('HOMERCHY_FULL_CLEAN', 'false').lower() == 'true'
    
    # ONLY preserve downloaded packages - NEVER preserve archiso-tmp or any other build state
    archiso_tmp_dir = work_dir / 'archiso-tmp'
    
    cache_dir = profile_dir / 'airootfs' / 'var' / 'cache' / 'omarchy' / 'mirror' / 'offline'
    # Also check system temp location (from cache_db_only cleanup)
    system_temp_cache = Path("/mnt/work/.homerchy-cache-temp")
    preserve_cache = (
        (cache_dir.exists() and any(cache_dir.glob('*.pkg.tar.*'))) or
        (system_temp_cache.exists() and any(system_temp_cache.glob('*.pkg.tar.*')))
    ) and not full_clean
    
    # Handle cache preservation even if profile_dir doesn't exist (cache in system temp from cleanup)
    if preserve_cache and not profile_dir.exists() and system_temp_cache.exists() and any(system_temp_cache.glob('*.pkg.tar.*')):
        print(f"{Colors.BLUE}Restoring cache from system temp location (profile directory doesn't exist yet)...{Colors.NC}")
        cache_dir.parent.mkdir(parents=True, exist_ok=True)
        pkg_count = len(list(system_temp_cache.glob('*.pkg.tar.*')))
        print(f"{Colors.BLUE}Restoring {pkg_count} packages from system temp cache...{Colors.NC}")
        try:
            shutil.move(str(system_temp_cache), str(cache_dir))
        except PermissionError:
            subprocess.run(['sudo', 'mv', str(system_temp_cache), str(cache_dir)], check=True)
        # Fix ownership
        current_uid = os.getuid()
        current_gid = os.getgid()
        subprocess.run(['sudo', 'chown', '-R', f'{current_uid}:{current_gid}', str(cache_dir)], check=True)
        print(f"{Colors.GREEN}✓ Restored cache from system temp location{Colors.NC}")
    
    if profile_dir.exists():
        print(f"{Colors.BLUE}Cleaning up previous profile directory...{Colors.NC}")
        
        # Preserve package cache
        if preserve_cache:
            temp_cache = work_dir / 'offline-mirror-cache-temp'
            if temp_cache.exists():
                try:
                    shutil.rmtree(temp_cache)
                except PermissionError:
                    subprocess.run(['sudo', 'rm', '-rf', str(temp_cache)], check=False)
            
            # Check system temp location first (from cache_db_only cleanup)
            if system_temp_cache.exists() and any(system_temp_cache.glob('*.pkg.tar.*')):
                pkg_count = len(list(system_temp_cache.glob('*.pkg.tar.*')))
                print(f"{Colors.BLUE}Preserving offline mirror cache from system temp ({pkg_count} packages)...{Colors.NC}")
                try:
                    shutil.move(str(system_temp_cache), str(temp_cache))
                except PermissionError:
                    subprocess.run(['sudo', 'mv', str(system_temp_cache), str(temp_cache)], check=True)
            # Otherwise check normal location
            elif cache_dir.exists() and any(cache_dir.glob('*.pkg.tar.*')):
                pkg_count = len(list(cache_dir.glob('*.pkg.tar.*')))
                print(f"{Colors.BLUE}Preserving offline mirror cache ({pkg_count} packages)...{Colors.NC}")
                cache_dir.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.move(str(cache_dir), str(temp_cache))
                except PermissionError:
                    # Use sudo to move if permission denied
                    subprocess.run(['sudo', 'mv', str(cache_dir), str(temp_cache)], check=True)
        
        try:
            shutil.rmtree(profile_dir)
        except PermissionError:
            subprocess.run(['sudo', 'rm', '-rf', str(profile_dir)], check=True)
        profile_dir.mkdir(parents=True, exist_ok=True)
        
        # Restore cache if it was preserved
        if preserve_cache:
            cache_dir.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.move(str(temp_cache), str(cache_dir))
            except PermissionError:
                # Use sudo to move if permission denied
                subprocess.run(['sudo', 'mv', str(temp_cache), str(cache_dir)], check=True)
            # Fix ownership of restored cache (may be owned by root if moved with sudo)
            # This ensures the package check can read the files
            current_uid = os.getuid()
            current_gid = os.getgid()
            subprocess.run(['sudo', 'chown', '-R', f'{current_uid}:{current_gid}', str(cache_dir)], check=True)
            print(f"{Colors.GREEN}✓ Restored offline mirror cache{Colors.NC}")
    
    # ALWAYS remove archiso-tmp - we ONLY cache downloaded packages, not build state
    # mkarchiso's build state causes it to skip ISO creation when it shouldn't
    if archiso_tmp_dir.exists():
        print(f"{Colors.BLUE}Removing archiso-tmp directory (only package cache is preserved)...{Colors.NC}")
        try:
            shutil.rmtree(archiso_tmp_dir)
        except PermissionError:
            subprocess.run(['sudo', 'rm', '-rf', str(archiso_tmp_dir)], check=False)
    
    print(f"{Colors.GREEN}✓ Prepare phase complete{Colors.NC}")
    
    return {
        "success": True,
        "preserve_cache": preserve_cache
    }


if __name__ == '__main__':
    import json
    phase_path = Path(__file__).parent
    config_path = phase_path / 'index.json'
    config = json.load(open(config_path)) if config_path.exists() else {}
    result = main(phase_path, config)
    sys.exit(0 if result.get('success') else 1)

