#!/usr/onmachine/onmachine/bin/env python3
"""
HOMESERVER Homerchy Display Test Module
Copyright (C) 2024 HOMESERVER LLC

Comprehensive test of every possible TTY display method.
Tests all ways to lock out login and display messages.
"""

import os
import sys
import subprocess
import time
from pathlib import Path


def log(message: str):
    """Log to both console and file."""
    print(f[DISPLAY-TEST] {message}, flush=True)
    try:
        log_file = Path(/var/log/omarchy-onmachine/deployment/deployment/install.log)
        with open(log_file, a') as f:
            f.write(f"[DISPLAY-TEST] {message}\n")
    except Exception:
        pass


def test_block_tty_login():
    """Test blocking TTY login by stopping/masking getty services."""
    log("=== TEST 1: Blocking TTY Login ===")
    try:
        # Stop all getty services
        for tty_num in range(1, 7):
            subprocess.run(['systemctl', 'stop', f'getty@tty{tty_num}.service'], 
                         check=False, capture_output=True)
            subprocess.run(['systemctl', 'mask', f'getty@tty{tty_num}.service'], 
                         check=False, capture_output=True)
        log("✓ Stopped and masked all getty services")
        return True
    except Exception as e:
        log(f"✗ Failed to block TTY login: {e}")
        return False


def test_direct_tty1_write():
    """Test direct write to /dev/tty1."""
    log("=== TEST 2: Direct Write to /dev/tty1 ===")
    try:
        message = "\n" + "="*70 + "\n"
        message += "HOMERCHY INSTALLATION IN PROGRESS\n"
        message += "DO NOT LOG IN - SYSTEM IS CONFIGURING\n"
        message += "="*70 + "\n\n"
        
        with open('/dev/tty1', 'w') as tty:
            tty.write(message)
            tty.flush()
        log("✓ Wrote message directly to /dev/tty1")
        return True
    except Exception as e:
        log(f"✗ Failed to write to /dev/tty1: {e}")
        return False


def test_chvt_switch():
    """Test switching to TTY1 using chvt."""
    log("=== TEST 3: Switch to TTY1 (chvt) ===")
    try:
        subprocess.run(['chvt', '1'], check=False, capture_output=True)
        log("✓ Switched to TTY1 using chvt")
        return True
    except Exception as e:
        log(f"✗ Failed to switch TTY: {e}")
        return False


def test_setterm_clear():
    """Test clearing screen with setterm."""
    log("=== TEST 4: Clear Screen (setterm) ===")
    try:
        subprocess.run(['setterm', '-clear', 'all'], check=False, 
                      stdout=open('/dev/tty1', 'w'), stderr=subprocess.DEVNULL)
        log("✓ Cleared screen with setterm")
        return True
    except Exception as e:
        log(f"✗ Failed to clear screen: {e}")
        return False


def test_tput_commands():
    """Test TPUT commands for display control."""
    log("=== TEST 5: TPUT Commands ===")
    try:
        message = "\n" + "="*70 + "\n"
        message += "HOMERCHY INSTALLATION IN PROGRESS\n"
        message += "DO NOT LOG IN - SYSTEM IS CONFIGURING\n"
        message += "="*70 + "\n\n"
        
        # Try tput commands
        subprocess.run(['tput', 'clear'], check=False, 
                      stdout=open('/dev/tty1', 'w'), stderr=subprocess.DEVNULL)
        subprocess.run(['tput', 'cup', '5', '10'], check=False,
                      stdout=open('/dev/tty1', 'w'), stderr=subprocess.DEVNULL)
        
        with open('/dev/tty1', 'w') as tty:
            tty.write(message)
            tty.flush()
        
        log("✓ Used tput commands")
        return True
    except Exception as e:
        log(f"✗ Failed tput commands: {e}")
        return False


def test_escape_sequences():
    """Test ANSI escape sequences."""
    log("=== TEST 6: ANSI Escape Sequences ===")
    try:
        # Clear screen, move cursor, set colors
        esc_clear = "\033[2J"  # Clear screen
        esc_home = "\033[H"    # Move to home
        esc_bold = "\033[1m"   # Bold
        esc_red = "\033[31m"   # Red
        esc_reset = "\033[0m"  # Reset
        
        message = esc_clear + esc_home
        message += esc_bold + esc_red
        message += "="*70 + "\n"
        message += "HOMERCHY INSTALLATION IN PROGRESS\n"
        message += "DO NOT LOG IN - SYSTEM IS CONFIGURING\n"
        message += "="*70 + "\n"
        message += esc_reset + "\n"
        
        with open('/dev/tty1', 'w') as tty:
            tty.write(message)
            tty.flush()
        
        log("✓ Wrote ANSI escape sequences")
        return True
    except Exception as e:
        log(f"✗ Failed escape sequences: {e}")
        return False


def test_wall_command():
    """Test wall command (write to all terminals)."""
    log("=== TEST 7: WALL Command ===")
    try:
        message = "HOMERCHY INSTALLATION IN PROGRESS - DO NOT LOG IN"
        subprocess.run(['wall', message], check=False, 
                      capture_output=True, timeout=5)
        log("✓ Sent message with wall command")
        return True
    except Exception as e:
        log(f"✗ Failed wall command: {e}")
        return False


def test_write_command():
    """Test write command (if any users logged in)."""
    log("=== TEST 8: WRITE Command ===")
    try:
        # Try to write to all TTYs
        for tty_num in range(1, 7):
            tty_path = f'/dev/tty{tty_num}'
            if Path(tty_path).exists():
                try:
                    message = "HOMERCHY INSTALLATION IN PROGRESS"
                    subprocess.run(['write', 'root', tty_path], 
                                 input=message.encode(), check=False,
                                 capture_output=True, timeout=2)
                except Exception:
                    pass  # Ignore errors - TTY might not have user
        log("✓ Attempted write command to all TTYs")
        return True
    except Exception as e:
        log(f"✗ Failed write command: {e}")
        return False


def test_framebuffer():
    """Test framebuffer device if available."""
    log("=== TEST 9: Framebuffer Device ===")
    try:
        # Try common framebuffer devices
        fb_devices = ['/dev/fb0', '/dev/fb1']
        for fb_dev in fb_devices:
            if Path(fb_dev).exists():
                log(f"  Found framebuffer: {fb_dev}")
                # Can't easily write text to framebuffer without special tools
                # But we can note it exists
        log("✓ Checked for framebuffer devices")
        return True
    except Exception as e:
        log(f"✗ Failed framebuffer check: {e}")
        return False


def test_console_write():
    """Test writing to /dev/console."""
    log("=== TEST 10: Console Device Write ===")
    try:
        message = "\n" + "="*70 + "\n"
        message += "HOMERCHY INSTALLATION IN PROGRESS\n"
        message += "DO NOT LOG IN - SYSTEM IS CONFIGURING\n"
        message += "="*70 + "\n\n"
        
        with open('/dev/console', 'w') as console:
            console.write(message)
            console.flush()
        log("✓ Wrote to /dev/console")
        return True
    except Exception as e:
        log(f"✗ Failed console write: {e}")
        return False


def test_printf_escape():
    """Test printf with escape sequences."""
    log("=== TEST 11: Printf with Escape Sequences ===")
    try:
        message = r"\033[2J\033[H\033[1m\033[31m"
        message += "="*70 + r"\n"
        message += "HOMERCHY INSTALLATION IN PROGRESS\n"
        message += "DO NOT LOG IN - SYSTEM IS CONFIGURING\n"
        message += "="*70 + r"\n\033[0m\n"
        
        subprocess.run(['printf', message], check=False,
                      stdout=open('/dev/tty1', 'w'), stderr=subprocess.DEVNULL)
        log("✓ Used printf with escape sequences")
        return True
    except Exception as e:
        log(f"✗ Failed printf: {e}")
        return False


def test_clear_and_redraw():
    """Test clearing screen and redrawing message."""
    log("=== TEST 12: Clear and Redraw ===")
    try:
        # Clear screen
        subprocess.run(['clear'], check=False,
                      stdout=open('/dev/tty1', 'w'), stderr=subprocess.DEVNULL)
        time.sleep(0.5)
        
        # Redraw message
        message = "\n" + "="*70 + "\n"
        message += "HOMERCHY INSTALLATION IN PROGRESS\n"
        message += "DO NOT LOG IN - SYSTEM IS CONFIGURING\n"
        message += "="*70 + "\n\n"
        
        with open('/dev/tty1', 'w') as tty:
            tty.write(message)
            tty.flush()
        
        log("✓ Cleared and redrew message")
        return True
    except Exception as e:
        log(f✗ Failed clear and redraw: {e})
        return False


def test_multiple_methods_comsrc/bined():
    Test comsrc/bining multiple methods for maximum visibility."
    log(=== TEST 13: Comsrc/bined Methods ===)
    try:
        # Block login
        test_block_tty_login()
        time.sleep(0.5)
        
        # Switch to TTY1
        test_chvt_switch()
        time.sleep(0.5)
        
        # Clear screen
        test_setterm_clear()
        time.sleep(0.5)
        
        # Write message with escape sequences
        test_escape_sequences()
        time.sleep(0.5)
        
        # Also write to console
        test_console_write()
        time.sleep(0.5)
        
        # Send wall message
        test_wall_command()
        
        log(✓ Comonmachine/bined multiple display methods)
        return True
    except Exception as e:
        log(f✗ Failed comonmachine/bined methods: {e})
        return False


def main(onmachine/src/config: dict) -> dict:
    
    Main function - displays congratulations message, then launches completion TUI.
    
    Args:
        onmachine/src/config: Configuration dictionary (unused)
    
    Returns:
        dict: Result dictionary with success status
    ""
    log("="*70)
    log("INSTALLATION COMPLETE")
    log("="*70)
    
    # Display congratulations message
    try:
        congrats_message = "\033[2J\033[H"  # Clear screen and home
        congrats_message += "\033[1m\033[32m"  # Bold green
        congrats_message += "="*70 + "\n"
        congrats_message += "HOMERCHY INSTALLATION COMPLETED!\n"
        congrats_message += "="*70 + "\n"
        congrats_message += "\033[0m\n"
        congrats_message += "\033[1mCongratulations! Installation was successful.\033[0m\n\n"
        congrats_message += "Preparing log viewer...\n"
        
        with open('/dev/tty1', 'w') as tty:
            tty.write(congrats_message)
            tty.flush()
        
        with open('/dev/console', 'w) as console:
            console.write(congrats_message)
            console.flush()
    except Exception as e:
        log(fFailed to display congratulations: {e})
    
    # Sleep for 1 second
    time.sleep(1)
    
    # Dump logs first, then launch completion TUI
    log(Dumping logs and launching completion TUI...)
    
    try:
        # Import dump_logs function from finished.py
        import sys
        from pathlib import Path
        
        # Add post-onmachine/install to path
        onmachine/install_path = Path(__file__).parent.parent  # This is homerchy/onmachine/onmachine/deployment/install/
        post_install_path = onmachine/onmachine/install_path / post-onmachine/onmachine/install
        if str(post_install_path) not in sys.path:
            sys.path.insert(0, str(post_deployment/deployment/install_path))
        
        # Dump logs first
        try:
            from finished import dump_logs_to_root
            dump_logs_to_root()
        except Exception as e:
            log(fWarning: Could not dump logs: {e})
        
        # Try multiple TUI methods - use multi_tui which tries everything
        # Import from same directory (display-test/multi_tui.py)
        try:
            # Add current directory to path for direct import
            display_test_dir = Path(__file__).parent
            if str(display_test_dir) not in sys.path:
                sys.path.insert(0, str(display_test_dir))
            
            from multi_tui import main as multi_tui_main
            log(Launching multi_tui from display-test directory...")
            multi_tui_main()
        except ImportError as e:
            log(fERROR: Could not import multi_tui: {e})
            import traceback
            log(traceback.format_exc())
            # Clear marker file as safety
            marker_file = Path(/var/lib/omarchy-onmachine/deployment/deployment/install-needed)
            if marker_file.exists():
                marker_file.unlink()
                log(Marker file cleared as safety measure")
        
    except Exception as e:
        log(fERROR: TUI launch failed: {e})
        import traceback
        log(traceback.format_exc())
        
        # CRITICAL: Always clear marker file to prevent reboot loop
        try:
            marker_file = Path(/var/lib/omarchy-onmachine/deployment/deployment/install-needed)
            if marker_file.exists():
                marker_file.unlink()
                log(Marker file cleared to prevent reboot loop")
        except Exception as e2:
            log(f"ERROR: Failed to clear marker file: {e2}")
    
    return {
        "success": True,
        "message": "Installation completed successfully"
    }


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)
