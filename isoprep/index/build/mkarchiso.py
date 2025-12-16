#!/usr/bin/env python3
"""
HOMESERVER Homerchy ISO Builder - mkarchiso Execution Module
Copyright (C) 2024 HOMESERVER LLC

Execute mkarchiso to build the ISO.
"""

import subprocess
import sys
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils import Colors


def execute_mkarchiso(work_dir: Path, out_dir: Path, profile_dir: Path):
    """
    Execute mkarchiso to build the ISO.
    
    Args:
        work_dir: Work directory for mkarchiso
        out_dir: Output directory for ISO
        profile_dir: ISO profile directory
    """
    print(f"{Colors.BLUE}Building ISO with mkarchiso (Requires Sudo)...{Colors.NC}")
    print(f"Output will be in: {Colors.GREEN}{out_dir}{Colors.NC}")
    print(f"{Colors.BLUE}Note: I/O errors reading /sys files are expected and harmless{Colors.NC}")
    
    # Run mkarchiso
    # Note: mkarchiso will produce I/O errors when trying to copy /sys and /proc virtual files
    # These are expected and mkarchiso handles them by creating empty files
    result = subprocess.run([
        'sudo', 'mkarchiso', '-v',
        '-w', str(work_dir / 'archiso-tmp'),
        '-o', str(out_dir),
        str(profile_dir)
    ])
    
    if result.returncode != 0:
        print(f"{Colors.RED}Build failed with exit code {result.returncode}{Colors.NC}")
        print(f"{Colors.YELLOW}Check the output above for actual errors (I/O errors on /sys files are normal){Colors.NC}")
        sys.exit(1)
    
    # Verify ISO was actually created
    iso_files = list(out_dir.glob('*.iso'))
    if not iso_files:
        print(f"{Colors.RED}ERROR: Build reported success but no ISO file was created!{Colors.NC}")
        sys.exit(1)
    
    print(f"{Colors.GREEN}Build complete! ISO is located in {out_dir}{Colors.NC}")
    for iso_file in iso_files:
        print(f"  {Colors.GREEN}{iso_file.name}{Colors.NC}")
    
    return iso_files
