#!/usr/bin/env python3
"""
HOMESERVER Homerchy Installation Entry Point
Copyright (C) 2024 HOMESERVER LLC

Main Python entry point for Homerchy installation system.
Replaces install.sh with Python-based orchestrator.
"""

import os
import sys
from pathlib import Path


def setup_environment():
    """Set up environment variables for installation."""
    # Set OMARCHY_PATH if not already set
    if 'OMARCHY_PATH' not in os.environ:
        omarchy_path = Path.home() / '.local' / 'share' / 'omarchy'
        os.environ['OMARCHY_PATH'] = str(omarchy_path)
    
    # Set OMARCHY_INSTALL
    omarchy_path = Path(os.environ['OMARCHY_PATH'])
    os.environ['OMARCHY_INSTALL'] = str(omarchy_path / 'install')
    
    # Set log file path
    if 'OMARCHY_INSTALL_LOG_FILE' not in os.environ:
        os.environ['OMARCHY_INSTALL_LOG_FILE'] = '/var/log/omarchy-install.log'
    
    # Add OMARCHY bin to PATH
    omarchy_bin = omarchy_path / 'bin'
    if omarchy_bin.exists():
        current_path = os.environ.get('PATH', '')
        os.environ['PATH'] = f"{omarchy_bin}:{current_path}"


def main():
    """Main entry point."""
    # Setup environment
    setup_environment()
    
    # Get install path
    install_path = Path(os.environ.get('OMARCHY_INSTALL', Path(__file__).parent / 'install'))
    
    # Verify install directory exists
    if not install_path.exists():
        print(f"ERROR: Installation directory not found: {install_path}", file=sys.stderr)
        print(f"ERROR: OMARCHY_PATH={os.environ.get('OMARCHY_PATH')}", file=sys.stderr)
        print(f"ERROR: HOME={os.environ.get('HOME')}", file=sys.stderr)
        sys.exit(1)
    
    # Import and run root orchestrator
    sys.path.insert(0, str(install_path))
    
    try:
        from index import Orchestrator, Status
        
        orchestrator = Orchestrator(install_path=install_path, phase="root")
        state = orchestrator.run()
        
        # Exit with appropriate code
        if state.status == Status.COMPLETED:
            sys.exit(0)
        else:
            sys.exit(1)
    
    except Exception as e:
        print(f"ERROR: Failed to run orchestrator: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

