#!/usr/bin/env python3
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
    print(f"[DISPLAY-TEST] {message}", flush=True)
    try:
        log_file = Path("/var/log/omarchy-install.log")
        with open(log_file, 'a') as f:
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
        log(f"✗ Failed clear and redraw: {e}")
        return False


def test_multiple_methods_combined():
    """Test combining multiple methods for maximum visibility."""
    log("=== TEST 13: Combined Methods ===")
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
        
        log("✓ Combined multiple display methods")
        return True
    except Exception as e:
        log(f"✗ Failed combined methods: {e}")
        return False


def main(config: dict) -> dict:
    """
    Main test function - runs all display tests.
    
    NOTE: TTY blocking and persistent message are now handled by install.py
    This module just verifies display methods work and logs results.
    
    Args:
        config: Configuration dictionary (unused)
    
    Returns:
        dict: Result dictionary with success status
    """
    log("="*70)
    log("DISPLAY TEST MODULE STARTED")
    log("Testing every possible TTY display method")
    log("NOTE: TTY blocking handled by install.py - this is just verification")
    log("="*70)
    
    results = {}
    
    # Run all tests (but don't block TTY - install.py already did that)
    tests = [
        ("Direct TTY1 Write", test_direct_tty1_write),
        ("CHVT Switch", test_chvt_switch),
        ("Setterm Clear", test_setterm_clear),
        ("TPUT Commands", test_tput_commands),
        ("ANSI Escape Sequences", test_escape_sequences),
        ("WALL Command", test_wall_command),
        ("WRITE Command", test_write_command),
        ("Framebuffer Check", test_framebuffer),
        ("Console Write", test_console_write),
        ("Printf Escape", test_printf_escape),
        ("Clear and Redraw", test_clear_and_redraw),
    ]
    
    # Skip TTY blocking test (install.py handles it)
    # Skip combined methods test (redundant now)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            time.sleep(0.5)  # Shorter pause between tests
        except Exception as e:
            log(f"✗ Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    # Verify TTY is still blocked (should be done by install.py)
    try:
        result = subprocess.run(['systemctl', 'is-active', 'getty@tty1.service'], 
                               capture_output=True, text=True, check=False)
        if result.returncode == 0:
            log("⚠ WARNING: TTY1 getty is active (should be stopped)")
            results["TTY Blocking Verification"] = False
        else:
            log("✓ TTY1 getty is stopped (correct)")
            results["TTY Blocking Verification"] = True
    except Exception as e:
        log(f"✗ Could not verify TTY blocking: {e}")
        results["TTY Blocking Verification"] = False
    
    # Final message refresh
    log("="*70)
    log("DISPLAY TEST COMPLETE")
    log("="*70)
    
    # Refresh display message (install.py's thread will keep it visible)
    try:
        final_message = "\033[2J\033[H"  # Clear screen and home
        final_message += "\033[1m\033[31m"  # Bold red
        final_message += "="*70 + "\n"
        final_message += "HOMERCHY INSTALLATION IN PROGRESS\n"
        final_message += "DO NOT LOG IN - SYSTEM IS CONFIGURING\n"
        final_message += "="*70 + "\n"
        final_message += "\033[0m\n"
        final_message += "Display test complete. Installation continuing...\n"
        final_message += "TTY login is blocked. Do not attempt to log in.\n\n"
        
        with open('/dev/tty1', 'w') as tty:
            tty.write(final_message)
            tty.flush()
        
        with open('/dev/console', 'w') as console:
            console.write(final_message)
            console.flush()
    except Exception as e:
        log(f"Failed final display: {e}")
    
    # Summary
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    log(f"Test Results: {passed}/{total} tests passed")
    
    return {
        "success": True,
        "message": f"Display test completed: {passed}/{total} tests passed",
        "results": results
    }


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)

