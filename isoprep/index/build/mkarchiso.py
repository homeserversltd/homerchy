#!/usr/bin/env python3
"""
HOMESERVER Homerchy ISO Builder - mkarchiso Execution Module
Copyright (C) 2024 HOMESERVER LLC

Execute mkarchiso to build the ISO.
"""

import subprocess
import sys
from datetime import datetime
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
    print(f"{Colors.BLUE}=== Build Phase ==={Colors.NC}")
    print(f"{Colors.BLUE}Building ISO with mkarchiso (Requires Sudo)...{Colors.NC}")
    print()
    print(f"{Colors.CYAN}INPUT FILES:{Colors.NC}")
    print(f"  Profile directory: {Colors.GREEN}{profile_dir.resolve()}{Colors.NC}")
    print(f"  Work directory: {Colors.GREEN}{work_dir.resolve()}{Colors.NC}")
    print(f"  Archiso work dir: {Colors.GREEN}{(work_dir / 'archiso-tmp').resolve()}{Colors.NC}")
    print()
    print(f"{Colors.CYAN}OUTPUT LOCATION:{Colors.NC}")
    print(f"  ISO output directory: {Colors.GREEN}{out_dir.resolve()}{Colors.NC}")
    print()
    print(f"{Colors.BLUE}Note: I/O errors reading /sys files are expected and harmless{Colors.NC}")
    print()
    print(f"{Colors.YELLOW}⚠ The 'Copying custom airootfs files...' step may take several minutes{Colors.NC}")
    print(f"{Colors.YELLOW}   This happens every build as mkarchiso needs to ensure the airootfs structure is correct{Colors.NC}")
    print(f"{Colors.YELLOW}   (We already cache the injected source, but mkarchiso still copies the entire airootfs structure){Colors.NC}")
    print()
    
    # Run mkarchiso
    # Note: mkarchiso will produce I/O errors when trying to copy /sys and /proc virtual files
    # These are expected and mkarchiso handles them by creating empty files
    mkarchiso_cmd = [
        'sudo', 'mkarchiso', '-v',
        '-w', str(work_dir / 'archiso-tmp'),
        '-o', str(out_dir),
        str(profile_dir)
    ]
    print(f"{Colors.CYAN}EXECUTING:{Colors.NC} {' '.join(mkarchiso_cmd)}")
    print()
    result = subprocess.run(mkarchiso_cmd)
    
    if result.returncode != 0:
        print()
        print(f"{Colors.RED}Build failed with exit code {result.returncode}{Colors.NC}")
        print(f"{Colors.YELLOW}Check the output above for actual errors (I/O errors on /sys files are normal){Colors.NC}")
        sys.exit(1)
    
    # Verify ISO was actually created
    iso_files = list(out_dir.glob('*.iso'))
    if not iso_files:
        print()
        print(f"{Colors.RED}ERROR: Build reported success but no ISO file was created!{Colors.NC}")
        print(f"{Colors.RED}  Checked in: {out_dir.resolve()}{Colors.NC}")
        sys.exit(1)
    
    print()
    print(f"{Colors.GREEN}✓ Build complete!{Colors.NC}")
    print(f"{Colors.CYAN}ISO OUTPUT FILES:{Colors.NC}")
    for iso_file in iso_files:
        # Get file size and modification time
        stat = iso_file.stat()
        size_gb = stat.st_size / (1024**3)
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        print(f"  {Colors.GREEN}{iso_file.resolve()}{Colors.NC}")
        print(f"    Size: {size_gb:.2f} GB")
        print(f"    Modified: {mtime}")
    
    return iso_files