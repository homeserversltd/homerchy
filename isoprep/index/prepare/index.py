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
    out_dir = Path(config.get('out_dir', repo_root / 'isoprep' / 'isoout'))
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
    
    archiso_tmp_dir = work_dir / 'archiso-tmp'
    preserve_archiso_tmp = archiso_tmp_dir.exists() and not full_clean
    
    cache_dir = profile_dir / 'airootfs' / 'var' / 'cache' / 'omarchy' / 'mirror' / 'offline'
    preserve_cache = cache_dir.exists() and any(cache_dir.glob('*.pkg.tar.*')) and not full_clean
    
    # Preserve injected source (takes a long time to copy)
    injected_source = profile_dir / 'airootfs' / 'root' / 'homerchy'
    preserve_source = injected_source.exists() and injected_source.is_dir() and not full_clean
    
    if profile_dir.exists():
        print(f"{Colors.BLUE}Cleaning up previous profile directory...{Colors.NC}")
        
        # Preserve package cache
        if preserve_cache:
            print(f"{Colors.BLUE}Preserving offline mirror cache ({len(list(cache_dir.glob('*.pkg.tar.*')))} packages)...{Colors.NC}")
            temp_cache = work_dir / 'offline-mirror-cache-temp'
            if temp_cache.exists():
                shutil.rmtree(temp_cache)
            cache_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(cache_dir), str(temp_cache))
        
        # Preserve injected source
        if preserve_source:
            print(f"{Colors.BLUE}Preserving injected repository source (speeds up rebuild)...{Colors.NC}")
            print(f"{Colors.YELLOW}⚠ Restoring this cache may take a minute...{Colors.NC}")
            temp_source = work_dir / 'injected-source-temp'
            if temp_source.exists():
                shutil.rmtree(temp_source)
            shutil.move(str(injected_source), str(temp_source))
        
        shutil.rmtree(profile_dir)
        profile_dir.mkdir(parents=True, exist_ok=True)
        
        # Restore cache if it was preserved
        if preserve_cache:
            cache_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(temp_cache), str(cache_dir))
            print(f"{Colors.GREEN}✓ Restored offline mirror cache{Colors.NC}")
        
        # Restore injected source if it was preserved
        if preserve_source:
            print(f"{Colors.BLUE}Restoring injected repository source...{Colors.NC}")
            injected_source.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(temp_source), str(injected_source))
            print(f"{Colors.GREEN}✓ Restored injected repository source{Colors.NC}")
    
    # Clean up preserved archiso-tmp to avoid stale state issues
    # We preserve it for package cache, but need to remove stale build artifacts
    # In full clean mode, remove everything
    if full_clean and archiso_tmp_dir.exists():
        print(f"{Colors.BLUE}Full clean mode: Removing archiso-tmp directory...{Colors.NC}")
        try:
            shutil.rmtree(archiso_tmp_dir)
        except PermissionError:
            subprocess.run(['sudo', 'rm', '-rf', str(archiso_tmp_dir)], check=False)
    elif preserve_archiso_tmp:
        print(f"{Colors.BLUE}Preserving mkarchiso work directory for faster rebuild (package cache){Colors.NC}")
        import subprocess
        
        # Remove cached squashfs to force rebuild
        cached_squashfs = archiso_tmp_dir / 'iso' / 'arch' / 'x86_64' / 'airootfs.sfs'
        if cached_squashfs.exists():
            print(f"{Colors.BLUE}Removing cached squashfs to force rebuild...{Colors.NC}")
            try:
                cached_squashfs.unlink()
            except PermissionError:
                subprocess.run(['sudo', 'rm', '-f', str(cached_squashfs)], check=False)
        
        # Remove entire x86_64 directory to avoid initramfs errors
        # mkarchiso uses state files to track progress, and stale state causes issues
        stale_x86_64 = archiso_tmp_dir / 'x86_64'
        if stale_x86_64.exists():
            print(f"{Colors.BLUE}Removing stale x86_64 directory to avoid initramfs errors...{Colors.NC}")
            try:
                shutil.rmtree(stale_x86_64)
            except PermissionError:
                subprocess.run(['sudo', 'rm', '-rf', str(stale_x86_64)], check=False)
        
        # Remove mkarchiso state files that track build progress
        # These cause mkarchiso to skip steps that need to be redone
        state_files = [
            'base._make_packages',
            'base._make_custom_airootfs',
            'base._make_customize_airootfs',
            'base._check_if_initramfs_has_ucode',
        ]
        for state_file in state_files:
            state_path = archiso_tmp_dir / state_file
            if state_path.exists():
                print(f"{Colors.BLUE}Removing stale state file: {state_file}...{Colors.NC}")
                try:
                    state_path.unlink()
                except PermissionError:
                    subprocess.run(['sudo', 'rm', '-f', str(state_path)], check=False)
        
        # Also clean up any stale boot directories in iso/arch
        stale_boot = archiso_tmp_dir / 'iso' / 'arch' / 'boot'
        if stale_boot.exists():
            print(f"{Colors.BLUE}Removing stale boot directory...{Colors.NC}")
            try:
                shutil.rmtree(stale_boot)
            except PermissionError:
                subprocess.run(['sudo', 'rm', '-rf', str(stale_boot)], check=False)
    
    print(f"{Colors.GREEN}✓ Prepare phase complete{Colors.NC}")
    
    return {
        "success": True,
        "preserve_archiso_tmp": preserve_archiso_tmp,
        "preserve_cache": preserve_cache
    }


if __name__ == '__main__':
    import json
    phase_path = Path(__file__).parent
    config_path = phase_path / 'index.json'
    config = json.load(open(config_path)) if config_path.exists() else {}
    result = main(phase_path, config)
    sys.exit(0 if result.get('success') else 1)

