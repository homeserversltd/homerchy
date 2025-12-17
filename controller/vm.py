"""
VM launch functionality.
"""

import os
import sys
from pathlib import Path

from .utils import run_command


def do_launch() -> None:
    """Launch VM from installed disk."""
    print(">>> Launching VM from installed disk...")
    
    repo_root = Path(__file__).parent.parent.resolve()
    launch_disk_script = repo_root / "vmtools" / "launch-disk.sh"
    
    if not launch_disk_script.exists() or not os.access(launch_disk_script, os.X_OK):
        print(f"Error: Launch disk script not found or executable at {launch_disk_script}")
        sys.exit(1)
    
    run_command(['bash', str(launch_disk_script)], check=False)


def do_launch_iso() -> None:
    """Launch VM from ISO (fresh install)."""
    print(">>> Launching VM from ISO (fresh install)...")
    
    repo_root = Path(__file__).parent.parent.resolve()
    launch_iso_script = repo_root / "vmtools" / "launch-iso.sh"
    
    if not launch_iso_script.exists() or not os.access(launch_iso_script, os.X_OK):
        print(f"Error: Launch ISO script not found or executable at {launch_iso_script}")
        sys.exit(1)
    
    run_command(['bash', str(launch_iso_script)], check=False)

