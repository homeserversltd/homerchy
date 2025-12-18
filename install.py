#!/usr/bin/env python3
"""
HOMESERVER Homerchy Installation Entry Point
Copyright (C) 2024 HOMESERVER LLC

Main Python entry point for Homerchy installation system.
Replaces install.sh with Python-based orchestrator.
"""

import os
import sys
import subprocess
import signal
import atexit
import threading
import time
from pathlib import Path


def block_tty_and_display_message():
    """Block TTY login and display persistent installation message."""
    try:
        # Stop and mask all getty services
        for tty_num in range(1, 7):
            subprocess.run(['systemctl', 'stop', f'getty@tty{tty_num}.service'], 
                         check=False, capture_output=True)
            subprocess.run(['systemctl', 'mask', f'getty@tty{tty_num}.service'], 
                         check=False, capture_output=True)
        
        # Switch to TTY1
        subprocess.run(['chvt', '1'], check=False, capture_output=True)
        time.sleep(0.2)
        
        # Display persistent message
        display_persistent_message()
        
        print("[INSTALL] TTY login blocked and persistent message displayed", file=sys.stderr)
    except Exception as e:
        print(f"WARNING: Failed to block TTY: {e}", file=sys.stderr)


def display_persistent_message():
    """Display the persistent installation message on TTY1."""
    try:
        message = "\033[2J\033[H"  # Clear screen and home cursor
        message += "\033[1m\033[31m"  # Bold red
        message += "="*70 + "\n"
        message += "HOMERCHY INSTALLATION IN PROGRESS\n"
        message += "DO NOT LOG IN - SYSTEM IS CONFIGURING\n"
        message += "="*70 + "\n"
        message += "\033[0m\n"  # Reset
        
        with open('/dev/tty1', 'w') as tty:
            tty.write(message)
            tty.flush()
        
        # Also write to console
        with open('/dev/console', 'w') as console:
            console.write(message)
            console.flush()
    except Exception as e:
        print(f"WARNING: Failed to display message: {e}", file=sys.stderr)


def persistent_message_loop():
    """Background thread that continuously refreshes the installation message."""
    while True:
        try:
            display_persistent_message()
            time.sleep(5)  # Refresh every 5 seconds
        except Exception:
            break  # Exit thread on error


def setup_environment():
    """Set up environment variables for installation."""
    # Set OMARCHY_PATH if not already set - try multiple possible locations
    if 'OMARCHY_PATH' not in os.environ:
        omarchy_path = None
        
        # Try user's home directory first (normal installation)
        candidate = Path.home() / '.local' / 'share' / 'omarchy'
        if (candidate / 'install').exists():
            omarchy_path = candidate
        # Try /root/omarchy (ISO location)
        elif (Path('/root/omarchy') / 'install').exists():
            omarchy_path = Path('/root/omarchy')
        # Try script's parent directory (if run from repo)
        else:
            script_dir = Path(__file__).parent
            if (script_dir / 'install').exists():
                omarchy_path = script_dir
        
        if omarchy_path is None:
            # Will be caught by verification below
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


def unblock_tty_login():
    """Unblock TTY login on successful installation."""
    try:
        # Unmask all getty services
        for tty_num in range(1, 7):
            subprocess.run(['systemctl', 'unmask', f'getty@tty{tty_num}.service'], 
                         check=False, capture_output=True)
        # Start TTY1 getty
        subprocess.run(['systemctl', 'start', 'getty@tty1.service'], 
                      check=False, capture_output=True)
        print("[INSTALL] TTY login unblocked", file=sys.stderr)
    except Exception as e:
        print(f"WARNING: Failed to unblock TTY: {e}", file=sys.stderr)


def unlock_account():
    """Unlock user account on successful installation."""
    try:
        username = os.environ.get('OMARCHY_INSTALL_USER') or os.environ.get('USER', 'owner')
        subprocess.run(['passwd', '-u', username], 
                      check=False, capture_output=True)
    except Exception as e:
        print(f"WARNING: Failed to unlock account: {e}", file=sys.stderr)


def lockout_and_reboot():
    """Lock out login and force reboot on installation failure."""
    print("INSTALLATION FAILED - Locking out login and rebooting...", file=sys.stderr)
    
    try:
        # Remove marker file FIRST to prevent reboot loop
        # This prevents the service from running again on next boot
        marker_file = Path('/var/lib/omarchy-install-needed')
        if marker_file.exists():
            try:
                marker_file.unlink()
            except Exception:
                pass  # Ignore errors removing marker
        
        # Disable SDDM (login manager) to prevent login
        subprocess.run(['systemctl', 'disable', 'sddm.service'], 
                      check=False, capture_output=True)
        subprocess.run(['systemctl', 'stop', 'sddm.service'], 
                      check=False, capture_output=True)
        
        # Lock the user account
        username = os.environ.get('OMARCHY_INSTALL_USER') or os.environ.get('USER', 'owner')
        subprocess.run(['passwd', '-l', username], 
                      check=False, capture_output=True)
        
        print("Login locked. Rebooting in 5 seconds...", file=sys.stderr)
        print("NOTE: Account is locked. Boot from ISO to recover.", file=sys.stderr)
        
        # Force reboot after short delay
        subprocess.run(['sleep', '5'], check=False)
        subprocess.run(['reboot', '-f'], check=False)
        
    except Exception as e:
        print(f"WARNING: Failed to lock out login: {e}", file=sys.stderr)
        # Still try to remove marker and reboot even if lockout fails
        try:
            marker_file = Path('/var/lib/omarchy-install-needed')
            if marker_file.exists():
                marker_file.unlink()
            subprocess.run(['reboot', '-f'], check=False)
        except Exception:
            pass


def cleanup_on_exit():
    """Ensure cleanup happens even on unexpected exit."""
    try:
        # DO NOT unblock TTY here - only unblock on explicit success/failure
        # This prevents TTY from being restored prematurely
        # Remove marker file to prevent reboot loop
        marker_file = Path('/var/lib/omarchy-install-needed')
        if marker_file.exists():
            marker_file.unlink()
    except Exception:
        pass  # Best effort cleanup


def signal_handler(signum, frame):
    """Handle signals to ensure cleanup."""
    cleanup_on_exit()
    sys.exit(1)


def main():
    """Main entry point."""
    # Register cleanup handlers
    atexit.register(cleanup_on_exit)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Setup environment
    setup_environment()
    
    # Block TTY login and display persistent message BEFORE anything else
    block_tty_and_display_message()
    
    # Start background thread to continuously refresh message
    message_thread = threading.Thread(target=persistent_message_loop, daemon=True)
    message_thread.start()
    
    # Ensure account is unlocked at start (in case it was locked from previous failed attempt)
    # This allows installation to proceed even if account was locked before
    try:
        username = os.environ.get('OMARCHY_INSTALL_USER') or os.environ.get('USER', 'owner')
        subprocess.run(['passwd', '-u', username], 
                      check=False, capture_output=True)
    except Exception:
        pass  # Ignore errors - account might not exist yet or might not be locked
    
    # Get install path
    install_path = Path(os.environ.get('OMARCHY_INSTALL', Path(__file__).parent / 'install'))
    
    # Verify install directory exists
    if not install_path.exists():
        print("ERROR: Installation directory not found!", file=sys.stderr)
        print("ERROR: Tried:", file=sys.stderr)
        print(f"ERROR:   {Path.home() / '.local' / 'share' / 'omarchy' / 'install'}", file=sys.stderr)
        print(f"ERROR:   {Path('/root/omarchy/install')}", file=sys.stderr)
        print(f"ERROR:   {Path(__file__).parent / 'install'}", file=sys.stderr)
        print(f"ERROR: OMARCHY_PATH={os.environ.get('OMARCHY_PATH')}", file=sys.stderr)
        print(f"ERROR: HOME={os.environ.get('HOME')}", file=sys.stderr)
        lockout_and_reboot()
        sys.exit(1)
    
    # Import and run root orchestrator
    sys.path.insert(0, str(install_path))
    
    try:
        from index import Orchestrator, Status
        
        orchestrator = Orchestrator(install_path=install_path, phase="root")
        state = orchestrator.run()
        
        # Exit with appropriate code
        if state.status == Status.COMPLETED:
            # Installation succeeded - unlock account and unblock TTY
            unlock_account()
            unblock_tty_login()
            sys.exit(0)
        else:
            # Installation failed - lockout (TTY stays blocked for lockout)
            lockout_and_reboot()
            sys.exit(1)
    
    except Exception as e:
        print(f"ERROR: Failed to run orchestrator: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        lockout_and_reboot()
        sys.exit(1)


if __name__ == "__main__":
    main()

