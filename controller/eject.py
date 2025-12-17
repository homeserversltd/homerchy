"""
Cartridge ejection logic for cleaning up build workspace.
"""

import subprocess
from pathlib import Path
from typing import List

from .utils import run_command, run_shell_command


WORK_DIR_BASE = "/mnt/work/homerchy-isoprep-work"
WORK_DIR_OLD = "/tmp/homerchy-isoprep-work"


def do_eject(full_cleanup: bool = False) -> None:
    """
    Eject cartridge (clean up work directory).
    
    Args:
        full_cleanup: If True, remove all caches (full eject)
    """
    if full_cleanup:
        print(">>> Full Eject Cartridge (Removing ALL caches)...")
    else:
        print(">>> Ejecting Cartridge (Preserving caches for faster rebuilds)...")
    
    # Determine work directory location
    work_dir = WORK_DIR_BASE
    if not Path(work_dir).exists() and Path(WORK_DIR_OLD).exists():
        work_dir = WORK_DIR_OLD
    
    if not Path(work_dir).exists():
        print("Nothing to eject (Work dir not found).")
        return
    
    print(f"Safely cleaning up mount points in {work_dir}...")
    
    # Step 1: Kill any processes using the work directory
    print("Checking for processes using work directory...")
    try:
        result = run_shell_command(
            f'lsof +D "{work_dir}" 2>/dev/null | awk \'NR>1 {{print $2}}\' | sort -u',
            check=False,
            capture_output=True
        )
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            print("Found processes using work directory, terminating...")
            for pid in pids:
                pid = pid.strip()
                if pid:
                    # Check if process exists
                    try:
                        result = run_shell_command(f'kill -0 {pid} 2>/dev/null', check=False)
                        if result.returncode == 0:
                            print(f"  Killing PID {pid}")
                            run_command(['kill', '-TERM', pid], check=False, sudo=True)
                    except:
                        pass
            
            import time
            time.sleep(2)
            
            # Force kill any remaining processes
            result = run_shell_command(
                f'lsof +D "{work_dir}" 2>/dev/null | awk \'NR>1 {{print $2}}\' | sort -u',
                check=False,
                capture_output=True
            )
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    pid = pid.strip()
                    if pid:
                        try:
                            result = run_shell_command(f'kill -0 {pid} 2>/dev/null', check=False)
                            if result.returncode == 0:
                                print(f"  Force killing PID {pid}")
                                run_command(['kill', '-KILL', pid], check=False, sudo=True)
                        except:
                            pass
                time.sleep(1)
    except:
        pass
    
    # Step 2: Use findmnt to find ALL mounts recursively
    print("Finding all mount points in work directory...")
    try:
        result = run_shell_command(
            f'findmnt -rn -o TARGET -T "{work_dir}" 2>/dev/null | grep "^{work_dir}" | sort -r',
            check=False,
            capture_output=True
        )
        if result.stdout.strip():
            mounts = result.stdout.strip().split('\n')
            for mountpoint in mounts:
                mountpoint = mountpoint.strip()
                if mountpoint:
                    print(f"Unmounting: {mountpoint}")
                    # Try normal unmount first
                    try:
                        run_command(['umount', mountpoint], check=False, sudo=True)
                    except:
                        # If that fails, try lazy unmount
                        print("  Normal unmount failed, trying lazy unmount...")
                        run_command(['umount', '-l', mountpoint], check=False, sudo=True)
    except:
        pass
    
    # Step 3: Fallback - find any remaining mountpoints with find
    print("Checking for any remaining mount points...")
    try:
        result = run_shell_command(
            f'find "{work_dir}" -type d -mountpoint 2>/dev/null | sort -r',
            check=False,
            capture_output=True
        )
        if result.stdout.strip():
            mountpoints = result.stdout.strip().split('\n')
            for mountpoint in mountpoints:
                mountpoint = mountpoint.strip()
                if mountpoint:
                    print(f"Unmounting (fallback): {mountpoint}")
                    run_command(['umount', '-l', mountpoint], check=False, sudo=True)
    except:
        pass
    
    # Step 4: Targeted unmount of known mkarchiso locations
    print("Unmounting known mkarchiso locations...")
    known_mounts = [
        f"{work_dir}/archiso-tmp/x86_64/airootfs/proc",
        f"{work_dir}/archiso-tmp/x86_64/airootfs/sys",
        f"{work_dir}/archiso-tmp/x86_64/airootfs/dev",
        f"{work_dir}/archiso-tmp/x86_64/airootfs/dev/pts",
        f"{work_dir}/archiso-tmp/x86_64/airootfs/run",
        f"{work_dir}/archiso-tmp/x86_64/airootfs/tmp",
    ]
    for mountpoint in known_mounts:
        try:
            result = run_shell_command(f'mountpoint -q "{mountpoint}" 2>/dev/null', check=False)
            if result.returncode == 0:
                print(f"  Unmounting: {mountpoint}")
                run_command(['umount', mountpoint], check=False, sudo=True)
                run_command(['umount', '-l', mountpoint], check=False, sudo=True)
        except:
            pass
    
    # Step 5: Clean up system-wide symlink created during build
    print("Cleaning up system-wide symlink...")
    system_mirror_link = "/var/cache/omarchy/mirror/offline"
    if Path(system_mirror_link).is_symlink():
        print(f"  Removing symlink: {system_mirror_link}")
        run_command(['rm', '-f', system_mirror_link], check=False, sudo=True)
    
    # Step 6: Final check - ensure no mounts remain
    import time
    time.sleep(1)
    try:
        result = run_shell_command(
            f'findmnt -rn -o TARGET -T "{work_dir}" 2>/dev/null | grep "^{work_dir}"',
            check=False,
            capture_output=True
        )
        if result.stdout.strip():
            print("WARNING: Some mounts may still be active:")
            print(result.stdout)
            print("Attempting lazy unmount of remaining mounts...")
            mounts = result.stdout.strip().split('\n')
            for mountpoint in mounts:
                mountpoint = mountpoint.strip()
                if mountpoint:
                    run_command(['umount', '-l', mountpoint], check=False, sudo=True)
    except:
        pass
    
    # Step 7: Remove work directory (with cache preservation logic)
    if work_dir in (WORK_DIR_BASE, WORK_DIR_OLD):
        if full_cleanup:
            # Full cleanup: remove everything including caches
            print("Removing work directory and ALL caches...")
            try:
                result = run_shell_command(
                    f'lsof +D "{work_dir}" 2>/dev/null | awk \'NR>1 {{print $2}}\' | sort -u',
                    check=False,
                    capture_output=True
                )
                if result.stdout.strip():
                    print("WARNING: Processes still using work directory, forcing removal...")
            except:
                pass
            run_command(['rm', '-rf', work_dir], sudo=True)
            print("✓ Cartridge fully ejected (all caches removed)")
        else:
            # Normal cleanup: preserve caches
            print("Removing work directory (preserving caches)...")
            
            profile_dir = Path(work_dir) / "profile"
            archiso_tmp = Path(work_dir) / "archiso-tmp"
            preserve_dir = "/mnt/work/.homerchy-cache-preserve"
            
            if profile_dir.exists() or archiso_tmp.exists():
                print("Preserving caches for faster rebuilds...")
                run_command(['mkdir', '-p', preserve_dir], sudo=True)
                
                # Preserve profile (injected source + package cache)
                if profile_dir.exists():
                    print("  Preserving profile directory...")
                    run_command(['mv', str(profile_dir), f"{preserve_dir}/profile"], check=False, sudo=True)
                
                # Preserve archiso-tmp package cache (but remove build artifacts first)
                if archiso_tmp.exists():
                    print("  Cleaning archiso-tmp before preserving (removing build artifacts)...")
                    # Remove huge build directories before preserving
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
                    
                    # Only preserve if there's actually something left (package cache)
                    if any(archiso_tmp.iterdir()):
                        print("  Preserving archiso-tmp package cache...")
                        run_command(['mv', str(archiso_tmp), f"{preserve_dir}/archiso-tmp"], check=False, sudo=True)
                    else:
                        print("  No package cache to preserve in archiso-tmp")
                        run_command(['rmdir', str(archiso_tmp)], check=False, sudo=True)
            
            # Remove work directory
            try:
                result = run_shell_command(
                    f'lsof +D "{work_dir}" 2>/dev/null | awk \'NR>1 {{print $2}}\' | sort -u',
                    check=False,
                    capture_output=True
                )
                if result.stdout.strip():
                    print("WARNING: Processes still using work directory, forcing removal...")
            except:
                pass
            run_command(['rm', '-rf', work_dir], sudo=True)
            
            # Restore preserved caches
            preserve_path = Path(preserve_dir)
            if preserve_path.exists():
                print("Restoring preserved caches...")
                if (preserve_path / "profile").exists():
                    run_command(['mkdir', '-p', work_dir], sudo=True)
                    run_command(['mv', f"{preserve_dir}/profile", f"{work_dir}/profile"], check=False, sudo=True)
                if (preserve_path / "archiso-tmp").exists():
                    run_command(['mkdir', '-p', work_dir], sudo=True)
                    run_command(['mv', f"{preserve_dir}/archiso-tmp", f"{work_dir}/archiso-tmp"], check=False, sudo=True)
                run_command(['rmdir', preserve_dir], check=False, sudo=True)
            
            print("✓ Cartridge ejected (caches preserved for faster rebuilds)")
    else:
        print(f"Safety check failed: WORK_DIR path looks suspicious ({work_dir}). Skipping rm -rf.")

