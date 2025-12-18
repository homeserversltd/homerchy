"""
Build orchestration for ISO creation.
"""

import os
import sys
from pathlib import Path

from .workdir import setup_build_workdir, cleanup_build_workdir
from .utils import run_command


def do_build(full_clean: bool = False, cache_db_only: bool = False) -> int:
    """
    Build ISO.
    
    Args:
        full_clean: If True, do full clean rebuild
        cache_db_only: If True, preserve only database and package files
    
    Returns:
        Exit code (0 for success)
    """
    print(">>> Starting Build...")
    
    # Setup work directory on disk
    work_dir = setup_build_workdir()
    
    # Clean up any stale mounts/processes before building to prevent accumulation
    if Path(work_dir).exists():
        print("Pre-build cleanup: Checking for stale mounts...")
        try:
            from .utils import run_shell_command
            result = run_shell_command(
                f'findmnt -rn -o TARGET -T "{work_dir}" 2>/dev/null | grep "^{work_dir}"',
                check=False,
                capture_output=True
            )
            if result.stdout.strip():
                print("Found stale mounts from previous build, cleaning up...")
                mounts = result.stdout.strip().split('\n')
                for mountpoint in mounts:
                    mountpoint = mountpoint.strip()
                    if mountpoint:
                        run_command(['umount', '-l', mountpoint], check=False, sudo=True)
        except:
            pass
    
    # Get repo root
    repo_root = Path(__file__).parent.parent.resolve()
    build_script = repo_root / "isoprep" / "build.py"
    
    if not build_script.exists():
        print(f"Error: Build script not found at {build_script}")
        # DO NOT cleanup - preserve state for debugging
        return 1
    
    # Set environment variables for work directory location and cleanup modes
    os.environ['HOMERCHY_WORK_DIR'] = work_dir
    os.environ['HOMERCHY_FULL_CLEAN'] = str(full_clean).lower()
    os.environ['HOMERCHY_CACHE_DB_ONLY'] = str(cache_db_only).lower()
    
    # Run build
    try:
        result = run_command([sys.executable, str(build_script)], check=False)
        build_exit = result.returncode
        
        # DO NOT cleanup after build - cleanup only happens on rebuild (pre-build) or eject
        # This allows inspection of profile directory and build artifacts
        
        # Clear the cleanup flags
        os.environ.pop('HOMERCHY_FULL_CLEAN', None)
        os.environ.pop('HOMERCHY_CACHE_DB_ONLY', None)
        
        return build_exit
    except Exception as e:
        print(f"Error running build: {e}", file=sys.stderr)
        # DO NOT cleanup on error either - preserve state for debugging
        return 1




