"""
ISO deployment to physical device.
"""

import os
import sys
from pathlib import Path

from .utils import run_command

WORK_DIR_BASE = "/mnt/work/homerchy-isoprep-work"


def do_deploy(target_dev: str) -> None:
    """
    Deploy ISO to a device.
    
    Args:
        target_dev: Target device path (e.g., /dev/sdX)
    """
    if not target_dev:
        print("Error: No target device specified for deploy.")
        sys.exit(1)
    
    # ISO is now in work directory
    work_dir = os.environ.get('HOMERCHY_WORK_DIR', WORK_DIR_BASE)
    iso_dir = Path(work_dir) / "isoout"
    
    # Find latest ISO
    iso_files = sorted(iso_dir.glob("omarchy-*.iso"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not iso_files:
        print(f"Error: No ISO found to deploy in {iso_dir}")
        sys.exit(1)
    
    iso_file = iso_files[0]
    
    print(f"WARNING: This will overwrite ALL data on {target_dev}")
    print(f"Target ISO: {iso_file}")
    response = input("Are you sure? [y/N] ")
    
    if response.lower() in ('y', 'yes'):
        print(f"Writing to {target_dev}...")
        # dd uses special syntax where options are passed as if=file, of=file, etc.
        run_command([
            'dd', f'if={iso_file}', f'of={target_dev}',
            'bs=4M', 'status=progress', 'oflag=sync'
        ], sudo=True)
        print("Deploy complete.")
    else:
        print("Deploy cancelled.")
