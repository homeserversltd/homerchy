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

# Register this module in sys.modules so index.py can find it
sys.modules['install'] = sys.modules[__name__]


def block_tty_and_display_message():
    "Block TTY login and display persistent installation message."
    try:
        # Stop and mask all getty services
        for tty_num in range(1, 7):
            subprocess.run(['systemctl', 'stop', f'getty@tty{tty_num}.service'], 
                         check=False, capture_output=True)
            subprocess.run(['systemctl', 'mask', f'getty@tty{tty_num}.service'], 
                         check=False, capture_output=True)
            # Also disable the service to prevent auto-start
            subprocess.run(['systemctl', 'disable', f'getty@tty{tty_num}.service'], 
                         check=False, capture_output=True)
        
        # Switch to TTY1
        subprocess.run(['chvt', '1'], check=False, capture_output=True)
        time.sleep(0.2)
        
        # Display persistent message
        display_persistent_message()
        
        print("[INSTALL] TTY login blocked and persistent message displayed", file=sys.stderr)
    except Exception as e:
        print(f"WARNING: Failed to block TTY: {e}", file=sys.stderr)


# Global status for persistent message
_current_status = "Starting installation..."
_run_counter = 0  # Will be set by get_or_increment_run_counter()
_orchestrator_instance = None  # Global reference to orchestrator for state access

def get_or_increment_run_counter() -> int:
    """Get or increment the run counter from /tmp/work/homerchy.pid.
    This counter increments each run and resets on reboot (since /tmp is cleared).
    Returns the current counter value."""
    pid_file = Path('/tmp/work/homerchy.pid')
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        if pid_file.exists():
            counter = int(pid_file.read_text().strip())
            counter += 1
        else:
            counter = 1
        
        pid_file.write_text(str(counter))
        return counter
    except Exception as e:
        print(f"[INSTALL] WARNING: Failed to read/increment run counter: {e}", file=sys.stderr)
        return 1  # Default to 1 if we can't read/write

def update_status(status: str):
    """Update the current installation status."""
    global _current_status
    _current_status = status
    print(f"[STATUS UPDATE] Setting status to: {status}", file=sys.stderr)
    display_persistent_message()

def _get_recent_logs(log_file: str, lines: int = 8) -> list:
    """Get recent lines from log file."""
    try:
        if not Path(log_file).exists():
            return ["[Log file not created yet]"]
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            # Return last N non-empty lines, stripping newlines
            recent = [line.rstrip() for line in all_lines[-lines:] if line.strip()]
            return recent if recent else ["[Log file is empty]"]
    except Exception as e:
        return [f"[Error reading log: {e}]"]

def _get_orchestrator_info() -> tuple:
    """Get current step and error info from orchestrator if available."""
    global _orchestrator_instance
    current_step = "unknown"
    error_count = 0
    child_info = []
    
    try:
        if _orchestrator_instance and hasattr(_orchestrator_instance, 'state'):
            state = _orchestrator_instance.state
            current_step = state.current_step or "none"
            error_count = len(state.errors) if hasattr(state, 'errors') else 0
            # Get list of executed children
            if hasattr(state, 'children') and state.children:
                child_info = list(state.children.keys())
    except Exception:
        pass  # Silently fail if orchestrator state isn't available
    
    return current_step, error_count, child_info

def display_persistent_message():
    """Display the persistent installation message on TTY1 with useful debugging info."""
    global _current_status, _run_counter
    
    # Color rotation based on run counter (mod 6 for 6 colors)
    colors = [
        "\033[1m\033[31m",  # Bold red
        "\033[1m\033[32m",  # Bold green
        "\033[1m\033[33m",  # Bold yellow
        "\033[1m\033[34m",  # Bold blue
        "\033[1m\033[35m",  # Bold magenta
        "\033[1m\033[36m",  # Bold cyan
    ]
    header_color = colors[_run_counter % len(colors)]
    
    # Get log file path
    log_file = os.environ.get('HOMERCHY_INSTALL_LOG_FILE', '/var/log/homerchy-install.log')
    
    # Get recent logs
    recent_logs = _get_recent_logs(log_file, lines=8)
    
    # Get orchestrator info
    current_step, error_count, child_info = _get_orchestrator_info()
    
    try:
        message = "\033[2J\033[H"  # Clear screen and home cursor
        message += header_color
        message += "="*70 + "\n"
        message += "HOMERCHY INSTALLATION IN PROGRESS\n"
        message += "="*70 + "\n"
        message += "\033[31m"  # Red
        message += "DEBUG v2.0 - Enhanced status display\n"  # Version marker to verify new code is running
        message += "\033[0m"  # Reset
        message += "\033[0m\n"  # Reset
        
        # Status section
        message += "\033[33m"  # Yellow for status
        message += f"Status: {_current_status}\n"
        message += "\033[0m"  # Reset
        
        # Current step
        message += "\033[36m"  # Cyan
        message += f"Current Step: {current_step}\n"
        message += "\033[0m"  # Reset
        
        # Run counter and errors
        message += "\033[36m"  # Cyan
        message += f"Run #: {_run_counter} | Errors: {error_count}\n"
        message += "\033[0m"  # Reset
        
        # Show executed children if any
        if child_info:
            message += "\033[35m"  # Magenta
            message += f"Executed: {', '.join(child_info[-5:])}\n"  # Last 5 children
            message += "\033[0m"  # Reset
        
        message += "\n"
        
        # Recent logs section
        message += "\033[32m"  # Green
        message += "Recent Logs:\n"
        message += "\033[0m"  # Reset
        message += "-" * 70 + "\n"
        # Show last 6 log lines (leave room for header)
        for log_line in recent_logs[-6:]:
            # Truncate long lines to fit terminal width
            if len(log_line) > 68:
                log_line = log_line[:65] + "..."
            message += log_line + "\n"
        message += "-" * 70 + "\n"
        
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
            time.sleep(2)  # Refresh every 2 seconds for more responsive updates
        except Exception:
            break  # Exit thread on error


def setup_environment():
    """Set up environment variables for installation."""
    # Set HOMERCHY_PATH if not already set - try multiple possible locations
    if 'HOMERCHY_PATH' not in os.environ:
        homerchy_path = None
        
        # Try user's home directory first (normal installation)
        candidate = Path.home() / '.local' / 'share' / 'homerchy'
        if (candidate / 'deployment' / 'install').exists():
            homerchy_path = candidate
        # Try /root/homerchy (ISO location)
        elif (Path('/root/homerchy') / 'deployment' / 'install').exists():
            homerchy_path = Path('/root/homerchy')
        # Try script's parent directory (if run from repo)
        else:
            script_dir = Path(__file__).parent
            if (script_dir / 'install').exists():
                homerchy_path = script_dir.parent
        
        if homerchy_path is None:
            # Will be caught by verification below
            homerchy_path = Path.home() / '.local' / 'share' / 'homerchy'
        
        os.environ['HOMERCHY_PATH'] = str(homerchy_path)
    
    # Set HOMERCHY_INSTALL
    homerchy_path = Path(os.environ['HOMERCHY_PATH'])
    os.environ['HOMERCHY_INSTALL'] = str(homerchy_path / 'deployment' / 'install')
    
    # Set log file path
    if 'HOMERCHY_INSTALL_LOG_FILE' not in os.environ:
        os.environ['HOMERCHY_INSTALL_LOG_FILE'] = '/var/log/homerchy-install.log'
    
    # Add HOMERCHY bin to PATH
    homerchy_bin = homerchy_path / 'src' / 'bin'
    if homerchy_bin.exists():
        current_path = os.environ.get('PATH', '')
        os.environ['PATH'] = f"{homerchy_bin}:{current_path}"


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
        username = os.environ.get('HOMERCHY_INSTALL_USER') or os.environ.get('USER', 'owner')
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
        marker_file = Path('/var/lib/homerchy-install-needed')
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
        username = os.environ.get('HOMERCHY_INSTALL_USER') or os.environ.get('USER', 'owner')
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
            marker_file = Path('/var/lib/homerchy-install-needed')
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
        # CRITICAL: Remove marker file to prevent reboot loop
        marker_file = Path('/var/lib/homerchy-install-needed')
        if marker_file.exists():
            marker_file.unlink()
            print("[INSTALL] Marker file cleared in cleanup", file=sys.stderr)
    except Exception as e:
        print(f"[INSTALL] WARNING: Failed to clear marker in cleanup: {e}", file=sys.stderr)


def signal_handler(signum, frame):
    """Handle signals to ensure cleanup."""
    cleanup_on_exit()
    sys.exit(1)


def main():
    """Main entry point."""
    global _run_counter
    
    # Register cleanup handlers
    atexit.register(cleanup_on_exit)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Increment run counter (must happen before display)
    _run_counter = get_or_increment_run_counter()
    print(f"[INSTALL] Run counter: {_run_counter}", file=sys.stderr)
    
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
        username = os.environ.get('HOMERCHY_INSTALL_USER') or os.environ.get('USER', 'owner')
        subprocess.run(['passwd', '-u', username], 
                      check=False, capture_output=True)
    except Exception:
        pass  # Ignore errors - account might not exist yet or might not be locked
    
    # Get install path
    install_path = Path(os.environ.get('HOMERCHY_INSTALL', Path(__file__).parent / 'install'))
    
    # Verify install directory exists
    if not install_path.exists():
        print("ERROR: Installation directory not found!", file=sys.stderr)
        print("ERROR: Tried:", file=sys.stderr)
        print(f"ERROR:   {Path.home() / '.local' / 'share' / 'homerchy' / 'deployment' / 'install'}", file=sys.stderr)
        print(f"ERROR:   {Path('/root/homerchy/deployment/install')}", file=sys.stderr)
        print(f"ERROR:   {Path(__file__).parent / 'install'}", file=sys.stderr)
        print(f"ERROR: HOMERCHY_PATH={os.environ.get('HOMERCHY_PATH')}", file=sys.stderr)
        print(f"ERROR: HOME={os.environ.get('HOME')}", file=sys.stderr)
        lockout_and_reboot()
        sys.exit(1)
    
    # Import and run root orchestrator
    sys.path.insert(0, str(install_path))
    
    try:
        from index import Orchestrator, Status  # type: ignore[import-untyped]
        
        # Update status before starting
        update_status("Initializing orchestrator...")
        
        orchestrator = Orchestrator(install_path=install_path, phase="root")
        
        # Store global reference for status display
        global _orchestrator_instance
        _orchestrator_instance = orchestrator
        
        # Update status during execution
        update_status("Running installation phases...")
        
        state = orchestrator.run()
        
        # Update status based on result
        if state.status == Status.COMPLETED:
            update_status("Installation completed successfully!")
        else:
            update_status(f"Installation failed: {state.status}")
        
        # Exit with appropriate code
        if state.status == Status.COMPLETED:
            # Installation succeeded - unlock account
            # TTY unblocking handled by finished.py completion TUI
            unlock_account()
            # Don't unblock TTY here - let completion_tui handle it
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
