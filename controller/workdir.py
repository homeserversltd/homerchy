"""
Work directory management for ISO build process.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional

from .utils import run_command, run_shell_command


WORK_DIR_BASE = "/mnt/work/homerchy-isoprep-work"


def setup_build_workdir() -> str:
    """
    Create work directory on disk (not tmpfs, no swap).
    
    Returns:
        Path to work directory
    """
    work_dir = WORK_DIR_BASE
    
    if not Path(work_dir).exists():
        print(f"Creating build work directory at {work_dir}...")
        run_command(['mkdir', '-p', work_dir], sudo=True)
        # Set ownership to current user
        uid = os.getuid()
        gid = os.getgid()
        run_command(['chown', '-R', f'{uid}:{gid}', work_dir], sudo=True)
        print("✓ Build work directory created")
    else:
        print(f"Build work directory already exists at {work_dir}")
    
    # Export work directory location
    os.environ['HOMERCHY_WORK_DIR'] = work_dir
    
    return work_dir


def cleanup_build_workdir(full_clean: bool = False, cache_db_only: bool = False) -> None:
    """
    Clean up work directory, preserving cacheable parts unless full clean.
    
    Args:
        full_clean: If True, remove all caches (full clean mode)
        cache_db_only: If True, preserve only database and package files
    """
    work_dir = WORK_DIR_BASE
    
    if not Path(work_dir).exists():
        return
    
    if full_clean:
        print("Cleaning up build work directory (FULL CLEAN - removing ALL caches)...")
    elif cache_db_only:
        print("Cleaning up build work directory (preserving database and package files, removing everything else)...")
    else:
        print("Cleaning up build work directory (preserving caches)...")
    
    # Kill any processes using the directory
    try:
        result = run_shell_command(
            f'lsof +D "{work_dir}" 2>/dev/null | awk \'NR>1 {{print $2}}\' | sort -u',
            check=False,
            capture_output=True
        )
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            print("Terminating processes using work directory...")
            for pid in pids:
                if pid.strip():
                    try:
                        run_command(['kill', '-TERM', pid.strip()], check=False, sudo=True)
                    except:
                        pass
            # Wait a bit, then force kill
            import time
            time.sleep(2)
            result = run_shell_command(
                f'lsof +D "{work_dir}" 2>/dev/null | awk \'NR>1 {{print $2}}\' | sort -u',
                check=False,
                capture_output=True
            )
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid.strip():
                        try:
                            run_command(['kill', '-KILL', pid.strip()], check=False, sudo=True)
                        except:
                            pass
    except:
        pass
    
    # Unmount any mounts in the directory
    try:
        result = run_shell_command(
            f'findmnt -rn -o TARGET -T "{work_dir}" 2>/dev/null | grep "^{work_dir}" | sort -r',
            check=False,
            capture_output=True
        )
        if result.stdout.strip():
            mounts = result.stdout.strip().split('\n')
            for mountpoint in mounts:
                if mountpoint.strip():
                    try:
                        run_command(['umount', '-l', mountpoint.strip()], check=False, sudo=True)
                    except:
                        pass
    except:
        pass
    
    work_path = Path(work_dir)
    
    if full_clean:
        # Full clean: remove everything except ISO output
        print("Removing work directory and ALL caches (full clean mode)...")
        iso_out_dir = work_path / "isoout"
        
        # Preserve ISO output if it exists
        temp_iso_dir = "/mnt/work/.homerchy-iso-temp"
        if iso_out_dir.exists() and any(iso_out_dir.glob("*.iso")):
            print("  Preserving ISO output directory...")
            temp_iso_path = Path(temp_iso_dir)
            if temp_iso_path.exists():
                run_command(['rm', '-rf', temp_iso_dir], sudo=True)
            run_command(['mv', str(iso_out_dir), temp_iso_dir], sudo=True)
        
        # Remove work directory
        run_command(['rm', '-rf', work_dir], sudo=True)
        
        # Restore ISO output
        if Path(temp_iso_dir).exists():
            run_command(['mkdir', '-p', work_dir], sudo=True)
            run_command(['mv', temp_iso_dir, str(iso_out_dir)], sudo=True)
        
        print("✓ Work directory fully cleaned (all caches removed, ISO output preserved)")
    
    elif cache_db_only:
        # Cache DB only: preserve database files and package files, remove everything else
        print("Preserving repository database and package files (removing everything else)...")
        
        profile_dir = work_path / "profile"
        archiso_tmp = work_path / "archiso-tmp"
        cache_dir = profile_dir / "airootfs/var/cache/omarchy/mirror/offline"
        prepare_temp_cache = work_path / "offline-mirror-cache-temp"
        
        temp_cache_dir = "/mnt/work/.homerchy-cache-temp"
        cache_found = False
        
        # Check final cache location - only preserve if it has package files
        if cache_dir.exists() and any(cache_dir.glob('*.pkg.tar.*')):
            pkg_count = len(list(cache_dir.glob('*.pkg.tar.*')))
            print(f"  Preserving repository database and package files from cache directory ({pkg_count} packages)...")
            cache_found = True
            if Path(temp_cache_dir).exists():
                run_command(['rm', '-rf', temp_cache_dir], sudo=True)
            run_command(['mv', str(cache_dir), temp_cache_dir], sudo=True)
        # Check prepare phase temp location - only preserve if it has package files
        elif prepare_temp_cache.exists() and any(prepare_temp_cache.glob('*.pkg.tar.*')):
            pkg_count = len(list(prepare_temp_cache.glob('*.pkg.tar.*')))
            print(f"  Preserving repository database and package files from prepare temp location ({pkg_count} packages)...")
            cache_found = True
            if Path(temp_cache_dir).exists():
                run_command(['rm', '-rf', temp_cache_dir], sudo=True)
            run_command(['mv', str(prepare_temp_cache), temp_cache_dir], sudo=True)
        
        # Remove archiso-tmp completely
        if archiso_tmp.exists():
            print("  Removing archiso-tmp...")
            run_command(['rm', '-rf', str(archiso_tmp)], sudo=True)
        
        # Remove profile directory completely
        if profile_dir.exists():
            print("  Removing profile directory...")
            run_command(['rm', '-rf', str(profile_dir)], sudo=True)
        
        # Don't restore cache here - leave it in temp location for prepare/download phase to restore
        # This avoids the prepare phase removing a cache that was just restored
        if Path(temp_cache_dir).exists():
            if any(Path(temp_cache_dir).glob('*.pkg.tar.*')):
                pkg_count = len(list(Path(temp_cache_dir).glob('*.pkg.tar.*')))
                print(f"  Cache preserved in temp location ({pkg_count} packages, will be restored by prepare phase)...")
            else:
                # Temp cache exists but is empty, remove it
                print("  Cache directory exists but is empty, removing...")
                run_command(['rm', '-rf', temp_cache_dir], sudo=True)
        
        print("✓ Work directory cleaned (database and package files preserved in temp location)")
    
    else:
        # Preserve cacheable directories
        profile_dir = work_path / "profile"
        archiso_tmp = work_path / "archiso-tmp"
        
        # Remove only the parts that need to be rebuilt
        if archiso_tmp.exists():
            print("Preserving archiso-tmp for package cache...")
            # Remove only the x86_64 build directory, keep package cache
            x86_64_dir = archiso_tmp / "x86_64"
            iso_dir = archiso_tmp / "iso"
            if x86_64_dir.exists():
                run_command(['rm', '-rf', str(x86_64_dir)], sudo=True)
            if iso_dir.exists():
                run_command(['rm', '-rf', str(iso_dir)], sudo=True)
            # Remove state files
            for state_file in archiso_tmp.glob("*.state"):
                run_command(['rm', '-f', str(state_file)], sudo=True)
            for base_file in archiso_tmp.glob("base.*"):
                run_command(['rm', '-f', str(base_file)], sudo=True)
        
        if profile_dir.exists():
            print("Cleaning up profile directory (preserving only caches)...")
            
            cache_dir = profile_dir / "airootfs/var/cache/omarchy/mirror/offline"
            temp_cache = work_path / "offline-mirror-cache-temp"
            
            # Clean up any stale temp directories
            if temp_cache.exists():
                run_command(['rm', '-rf', str(temp_cache)], sudo=True)
            
            # Preserve package cache if it exists and has packages
            if cache_dir.exists():
                pkg_files = list(cache_dir.glob("*.pkg.tar.*"))
                if pkg_files:
                    print("  Preserving package cache...")
                    run_command(['mkdir', '-p', str(temp_cache.parent)], sudo=True)
                    run_command(['mv', str(cache_dir), str(temp_cache)], sudo=True)
            
            # Remove entire profile directory
            print("  Removing profile directory...")
            run_command(['rm', '-rf', str(profile_dir)], sudo=True)
            
            # Restore preserved cache
            if temp_cache.exists():
                print("  Restoring package cache...")
                run_command(['mkdir', '-p', str(cache_dir.parent)], sudo=True)
                run_command(['mv', str(temp_cache), str(cache_dir)], sudo=True)
        
        # Only remove work directory if it's completely empty
        if work_path.exists() and not any(work_path.iterdir()):
            run_command(['rmdir', work_dir], check=False, sudo=True)
        else:
            print("✓ Preserved cacheable directories for faster rebuild")

