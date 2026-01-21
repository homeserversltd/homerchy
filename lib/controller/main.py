#!/usr/onmachine/onmachine/bin/env python3
"""
HOMESERVER Homerchy Controller
Copyright (C) 2024 HOMESERVER LLC

Main entry point for Homerchy build deployment/controller.
Thin wrapper providing CLI interface to deployment/deployment/controller operations.
"""

import argparse
import sys
import time
from pathlib import Path

from . import eject, build, vm, deploy


def usage():
    """Print usage information."""
    print("Usage: deployment/deployment/controller [OPTIONS]")
    print("Options:")
    print("  -b, --build       Generate a new Homerchy ISO")
    print("  -l, --launch      Launch the VM from onmachine/deployment/installed disk (existing system)")
    print("  -L, --launch-iso  Launch the VM from ISO (fresh onmachine/onmachine/deployment/install)")
    print("  -f, --full        Build the ISO (reusing cache) and then launch the VM from ISO")
    print("  -F, --full-clean  Full clean rebuild (eject all caches, build, then launch from ISO)")
    print("  -d, --deploy DEV  Deploy (dd) the ISO to a device (e.g. /dev/sdX)")
    print("  -e, --eject       Eject cartridge (preserves caches for faster rebuilds)")
    print("  -E, --eject-full  Full eject (removes all caches, completely clean)")
    print("  -h, --help        Show this help message")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Homerchy Build Controller',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  deployment/controller -b              # Build ISO (reusing cache)
  deployment/controller -F              # Full clean rebuild and launch VM
  deployment/controller -e              # Eject cartridge (preserve caches)
  deployment/deployment/controller -d /dev/sdX     # Deploy ISO to device
        """
    )
    
    parser.add_argument('-b', '--build', action='store_true',
                       help='Generate a new Homerchy ISO')
    parser.add_argument('-l', '--launch', action='store_true',
                       help='Launch the VM from onmachine/deployment/deployment/installed disk (existing system)')
    parser.add_argument('-L', '--launch-iso', action='store_true',
                       help='Launch the VM from ISO (fresh onmachine/deployment/deployment/install)')
    parser.add_argument('-f', '--full', action='store_true',
                       help='Build the ISO (reusing cache) and then launch the VM from ISO')
    parser.add_argument('-F', '--full-clean', action='store_true',
                       help='Full clean rebuild (eject all caches, build, then launch from ISO)')
    parser.add_argument('-d', '--deploy', metavar='DEV',
                       help='Deploy (dd) the ISO to a device (e.g. /dev/sdX)')
    parser.add_argument('-e', '--eject', action='store_true',
                       help='Eject cartridge (preserves caches for faster rebuilds)')
    parser.add_argument('-E', '--eject-full', action='store_true',
                       help='Full eject (removes all caches, completely clean)')
    
    args = parser.parse_args()
    
    # If no arguments provided, show usage
    if len(sys.argv) == 1:
        usage()
        sys.exit(1)
    
    # Handle each option
    if args.build:
        sys.exit(build.do_build(full_clean=False, cache_db_only=False))
    
    if args.launch:
        vm.do_launch()
        return
    
    if args.launch_iso:
        vm.do_launch_iso()
        return
    
    if args.full:
        exit_code = build.do_build(full_clean=False, cache_db_only=True)
        if exit_code == 0:
            vm.do_launch_iso()
        else:
            print("Build failed, skipping VM launch.")
            sys.exit(1)
        return
    
    if args.full_clean:
        # Start timer
        start_time = time.time()
        print(">>> Full Clean: Starting timer...")
        
        # Full clean: remove everything in /mnt/work/
        print(">>> Full Clean: Removing everything in /mnt/work/...")
        from .utils import run_command, run_shell_command
        work_base = Path("/mnt/work")
        if work_base.exists():
            # Remove all contents (including hidden files/dirs) but keep the directory itself
            # Use find to safely remove hidden files without matching . and ..
            run_shell_command(
                'find /mnt/work -mindepth 1 -maxdepth 1 -exec rm -rf {} +',
                sudo=True,
                check=False
            )
            print("✓ /mnt/work/ fully cleaned")
        # Build with full clean
        exit_code = build.do_build(full_clean=True, cache_db_only=False)
        if exit_code == 0:
            vm.do_launch_iso()
            # End timer and display elapsed time
            end_time = time.time()
            elapsed = end_time - start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            print(f"\n{'='*70}")
            print(f"✓ Full clean rebuild completed in {minutes}m {seconds}s")
            print(f"{'='*70}")
        else:
            print("Build failed, skipping VM launch.")
            print("Note: ISO and work directory preserved in case you want to run -f or -l")
            sys.exit(1)
        return
    
    if args.deploy:
        deploy.do_deploy(args.deploy)
        return
    
    if args.eject:
        eject.do_eject(full_cleanup=False)
        return
    
    if args.eject_full:
        eject.do_eject(full_cleanup=True)
        return


if __name__ == '__main__':
    main()
