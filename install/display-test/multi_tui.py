#!/usr/bin/env python3
"""
HOMESERVER Homerchy Multi-Method TUI
Copyright (C) 2024 HOMESERVER LLC

Tries every possible TUI method sequentially until one works.
ALWAYS clears marker file to prevent reboot loops.
"""

import os
import select
import subprocess
import sys
import termios
import tty
import time
from pathlib import Path


def clear_marker_file():
    """ALWAYS clear marker file - critical to prevent reboot loops."""
    marker_file = Path('/var/lib/omarchy-install-needed')
    if marker_file.exists():
        try:
            marker_file.unlink()
            print("[MULTI-TUI] Marker file cleared", file=sys.stderr)
        except Exception as e:
            print(f"[MULTI-TUI] WARNING: Failed to clear marker: {e}", file=sys.stderr)


def method1_direct_tty_write():
    """Method 1: Direct write to /dev/tty1 with simple input() - most successful method.
    
    ✅ TESTED AND WORKING - Screenshot evidence shows this method successfully displayed
    "SUCCESS! Method Direct TTY Write + input() worked!" and waited for Enter to reboot.
    This is the working method for VM environment.
    """
    try:
        # Display message
        message = "\033[2J\033[H"  # Clear screen
        message += "\033[1m\033[33m" + "="*70 + "\n"
        message += "TUI METHOD 1: Direct TTY Write + input()\n"
        message += "="*70 + "\n\033[0m\n"
        message += "\033[1m\033[32m"  # Bold green
        message += "HOMERCHY INSTALLATION COMPLETED!\n"
        message += "\033[0m\n"
        message += "Logs dumped to /root/\n\n"
        message += "Press ENTER to reboot (no automatic reboot)\n"
        message += "="*70 + "\n"
        
        with open('/dev/tty1', 'w') as tty1:
            tty1.write(message)
            tty1.flush()
        
        # Try simple input() - redirect stdin to /dev/tty1
        try:
            # Open /dev/tty1 for reading
            tty1_read = open('/dev/tty1', 'r')
            old_stdin = sys.stdin
            sys.stdin = tty1_read
            
            # Wait for Enter
            input()
            
            sys.stdin = old_stdin
            tty1_read.close()
            return True
        except Exception:
            sys.stdin = old_stdin if 'old_stdin' in locals() else sys.stdin
            return False
    except Exception as e:
        print(f"[MULTI-TUI] Method 1 failed: {e}", file=sys.stderr)
        return False


def method2_termios_raw():
    """Method 2: Termios raw mode on /dev/tty1."""
    try:
        tty_fd = os.open('/dev/tty1', os.O_RDWR)
        old_settings = termios.tcgetattr(tty_fd)
        tty.setraw(tty_fd)
        
        # Display message
        message = "\033[2J\033[H"
        message += "\033[1m\033[33m" + "="*70 + "\n"
        message += "TUI METHOD 2: Termios Raw Mode\n"
        message += "="*70 + "\n\033[0m\n"
        message += "\033[1m\033[32m"
        message += "HOMERCHY INSTALLATION COMPLETED!\n"
        message += "\033[0m\n"
        message += "Press ENTER to reboot\n"
        os.write(tty_fd, message.encode('utf-8'))
        os.fsync(tty_fd)
        
        # Wait for Enter
        while True:
            if select.select([tty_fd], [], [], 0.5)[0]:
                key = os.read(tty_fd, 1)
                if key in (b'\r', b'\n'):
                    break
        
        termios.tcsetattr(tty_fd, termios.TCSADRAIN, old_settings)
        os.close(tty_fd)
        return True
    except Exception as e:
        print(f"[MULTI-TUI] Method 2 failed: {e}", file=sys.stderr)
        return False


def method3_read_from_console():
    """Method 3: Read from /dev/console."""
    try:
        # Display message
        message = "\033[2J\033[H"
        message += "\033[1m\033[33m" + "="*70 + "\n"
        message += "TUI METHOD 3: Read from Console\n"
        message += "="*70 + "\n\033[0m\n"
        message += "\033[1m\033[32m"
        message += "HOMERCHY INSTALLATION COMPLETED!\n"
        message += "\033[0m\n"
        message += "Press ENTER to reboot\n"
        
        with open('/dev/console', 'w') as console:
            console.write(message)
            console.flush()
        
        # Try reading from console
        console_fd = os.open('/dev/console', os.O_RDWR)
        old_settings = termios.tcgetattr(console_fd)
        tty.setraw(console_fd)
        
        while True:
            if select.select([console_fd], [], [], 0.5)[0]:
                key = os.read(console_fd, 1)
                if key in (b'\r', b'\n'):
                    break
        
        termios.tcsetattr(console_fd, termios.TCSADRAIN, old_settings)
        os.close(console_fd)
        return True
    except Exception as e:
        print(f"[MULTI-TUI] Method 3 failed: {e}", file=sys.stderr)
        return False


def method4_stty_raw():
    """Method 4: Use stty to set raw mode, then read."""
    try:
        # Display message
        message = "\033[2J\033[H"
        message += "\033[1m\033[33m" + "="*70 + "\n"
        message += "TUI METHOD 4: stty Raw Mode\n"
        message += "="*70 + "\n\033[0m\n"
        message += "\033[1m\033[32m"
        message += "HOMERCHY INSTALLATION COMPLETED!\n"
        message += "\033[0m\n"
        message += "Press ENTER to reboot\n"
        
        with open('/dev/tty1', 'w') as tty1:
            tty1.write(message)
            tty1.flush()
        
        # Use stty to set raw mode
        subprocess.run(['stty', 'raw', '-echo'], stdin=open('/dev/tty1', 'r'), check=False)
        
        # Read from /dev/tty1
        tty1_fd = os.open('/dev/tty1', os.O_RDWR)
        while True:
            if select.select([tty1_fd], [], [], 0.5)[0]:
                key = os.read(tty1_fd, 1)
                if key in (b'\r', b'\n'):
                    break
        
        subprocess.run(['stty', 'sane'], stdin=open('/dev/tty1', 'r'), check=False)
        os.close(tty1_fd)
        return True
    except Exception as e:
        print(f"[MULTI-TUI] Method 4 failed: {e}", file=sys.stderr)
        return False


def method5_bash_read():
    """Method 5: Use bash read command."""
    try:
        # Display message
        message = "\033[2J\033[H"
        message += "\033[1m\033[33m" + "="*70 + "\n"
        message += "TUI METHOD 5: Bash Read\n"
        message += "="*70 + "\n\033[0m\n"
        message += "\033[1m\033[32m"
        message += "HOMERCHY INSTALLATION COMPLETED!\n"
        message += "\033[0m\n"
        message += "Press ENTER to reboot\n"
        
        with open('/dev/tty1', 'w') as tty1:
            tty1.write(message)
            tty1.flush()
        
        # Use bash read
        subprocess.run(['bash', '-c', 'read -n 1 < /dev/tty1'], check=False)
        return True
    except Exception as e:
        print(f"[MULTI-TUI] Method 5 failed: {e}", file=sys.stderr)
        return False


def method6_python_getch():
    """Method 6: Python getch-style reading."""
    try:
        # Display message
        message = "\033[2J\033[H"
        message += "\033[1m\033[33m" + "="*70 + "\n"
        message += "TUI METHOD 6: Python Getch\n"
        message += "="*70 + "\n\033[0m\n"
        message += "\033[1m\033[32m"
        message += "HOMERCHY INSTALLATION COMPLETED!\n"
        message += "\033[0m\n"
        message += "Press ENTER to reboot\n"
        
        with open('/dev/tty1', 'w') as tty1:
            tty1.write(message)
            tty1.flush()
        
        # Getch-style
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        tty.setraw(fd)
        
        try:
            ch = sys.stdin.read(1)
            if ch in ('\r', '\n'):
                return True
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        
        return False
    except Exception as e:
        print(f"[MULTI-TUI] Method 6 failed: {e}", file=sys.stderr)
        return False


def method7_file_descriptor():
    """Method 7: Direct file descriptor operations."""
    try:
        # Display message
        message = "\033[2J\033[H"
        message += "\033[1m\033[33m" + "="*70 + "\n"
        message += "TUI METHOD 7: File Descriptor\n"
        message += "="*70 + "\n\033[0m\n"
        message += "\033[1m\033[32m"
        message += "HOMERCHY INSTALLATION COMPLETED!\n"
        message += "\033[0m\n"
        message += "Press ENTER to reboot\n"
        
        tty_fd = os.open('/dev/tty1', os.O_RDWR)
        os.write(tty_fd, message.encode('utf-8'))
        os.fsync(tty_fd)
        
        # Set raw mode
        old_settings = termios.tcgetattr(tty_fd)
        tty.setraw(tty_fd)
        
        # Read
        while True:
            if select.select([tty_fd], [], [], 0.5)[0]:
                key = os.read(tty_fd, 1)
                if key in (b'\r', b'\n'):
                    break
        
        termios.tcsetattr(tty_fd, termios.TCSADRAIN, old_settings)
        os.close(tty_fd)
        return True
    except Exception as e:
        print(f"[MULTI-TUI] Method 7 failed: {e}", file=sys.stderr)
        return False


def method8_simple_wait():
    """Method 8: Just display message and wait with time.sleep - user can press Enter in background."""
    try:
        message = "\033[2J\033[H"
        message += "\033[1m\033[33m" + "="*70 + "\n"
        message += "TUI METHOD 8: Simple Wait\n"
        message += "="*70 + "\n\033[0m\n"
        message += "\033[1m\033[32m"
        message += "HOMERCHY INSTALLATION COMPLETED!\n"
        message += "\033[0m\n"
        message += "Logs in /root/\n"
        message += "Press ENTER to reboot\n"
        
        with open('/dev/tty1', 'w') as tty1:
            tty1.write(message)
            tty1.flush()
        
        # Try to read in background while waiting
        tty_fd = None
        try:
            tty_fd = os.open('/dev/tty1', os.O_RDWR)
            old_settings = termios.tcgetattr(tty_fd)
            tty.setraw(tty_fd)
            
            # Check periodically
            for _ in range(600):  # 5 minutes max
                if select.select([tty_fd], [], [], 0.5)[0]:
                    key = os.read(tty_fd, 1)
                    if key in (b'\r', b'\n'):
                        if tty_fd:
                            termios.tcsetattr(tty_fd, termios.TCSADRAIN, old_settings)
                            os.close(tty_fd)
                        return True
        except Exception:
            if tty_fd:
                try:
                    termios.tcsetattr(tty_fd, termios.TCSADRAIN, old_settings)
                    os.close(tty_fd)
                except Exception:
                    pass
        
        return False
    except Exception as e:
        print(f"[MULTI-TUI] Method 8 failed: {e}", file=sys.stderr)
        return False


def method9_direct_stdin():
    """Method 9: Try reading from stdin directly."""
    try:
        message = "\033[2J\033[H"
        message += "\033[1m\033[33m" + "="*70 + "\n"
        message += "TUI METHOD 9: Direct Stdin\n"
        message += "="*70 + "\n\033[0m\n"
        message += "\033[1m\033[32m"
        message += "HOMERCHY INSTALLATION COMPLETED!\n"
        message += "\033[0m\n"
        message += "Press ENTER to reboot\n"
        
        with open('/dev/tty1', 'w') as tty1:
            tty1.write(message)
            tty1.flush()
        
        # Try stdin
        if sys.stdin.isatty():
            old_settings = termios.tcgetattr(sys.stdin.fileno())
            tty.setraw(sys.stdin.fileno())
            try:
                ch = sys.stdin.read(1)
                if ch in ('\r', '\n'):
                    return True
            finally:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_settings)
        
        return False
    except Exception as e:
        print(f"[MULTI-TUI] Method 9 failed: {e}", file=sys.stderr)
        return False


def method10_chvt_and_wait():
    """Method 10: Switch to TTY1, display, and use simplest possible input."""
    try:
        subprocess.run(['chvt', '1'], check=False, capture_output=True)
        time.sleep(0.5)
        
        message = "\033[2J\033[H"
        message += "\033[1m\033[33m" + "="*70 + "\n"
        message += "TUI METHOD 10: chvt and Wait\n"
        message += "="*70 + "\n\033[0m\n"
        message += "\033[1m\033[32m"
        message += "HOMERCHY INSTALLATION COMPLETED!\n"
        message += "\033[0m\n"
        message += "Press ENTER to reboot\n"
        
        with open('/dev/tty1', 'w') as tty1:
            tty1.write(message)
            tty1.flush()
        
        # Simplest possible - just try input() with redirected stdin
        try:
            # Redirect stdin to /dev/tty1
            tty1_file = open('/dev/tty1', 'r')
            old_stdin = sys.stdin
            sys.stdin = tty1_file
            
            # This might work if we're on the right TTY
            try:
                input()
                return True
            except (EOFError, OSError):
                return False
            finally:
                sys.stdin = old_stdin
                tty1_file.close()
        except Exception:
            return False
    except Exception as e:
        print(f"[MULTI-TUI] Method 10 failed: {e}", file=sys.stderr)
        return False


def wait_for_any_key_to_continue(tty_fd=None):
    """Wait for any key press to continue to next method - NO AUTO TIMEOUT."""
    if not tty_fd:
        try:
            tty_fd = os.open('/dev/tty1', os.O_RDWR)
        except Exception:
            return
    
    try:
        old_settings = termios.tcgetattr(tty_fd)
        tty.setraw(tty_fd)
        
        # Display "Press any key to try next method"
        prompt = "\n\033[1mPress ANY KEY to try this method...\033[0m\n"
        os.write(tty_fd, prompt.encode('utf-8'))
        os.fsync(tty_fd)
        
        # Wait for any key - NO TIMEOUT, wait indefinitely
        while True:
            if select.select([tty_fd], [], [], 0.5)[0]:
                os.read(tty_fd, 1)  # Read and discard the key
                break
        
        termios.tcsetattr(tty_fd, termios.TCSADRAIN, old_settings)
    except Exception:
        pass
    finally:
        if tty_fd:
            try:
                os.close(tty_fd)
            except Exception:
                pass


def log_to_tty1(message: str):
    """Log a message to TTY1 so it's visible during installation."""
    try:
        # Append to TTY1 without clearing screen (write to line 6+)
        log_msg = f"\033[6;1H\033[K{message}\033[K\n"
        with open('/dev/tty1', 'w') as tty:
            tty.write(log_msg)
            tty.flush()
    except Exception:
        pass  # Silently fail - logging is non-critical

def main():
    """Try all TUI methods sequentially - user presses any key to advance through each.
    
    TESTING RESULTS (from VM screenshots):
    - Method 1 (Direct TTY Write + input()): ✅ WORKING - Successfully displayed completion
      screen and waited for Enter to reboot. This is the working method.
    - Methods 2-10: Not yet tested or failed (need more screenshots to verify)
    """
    log_to_tty1("[MULTI-TUI] Starting multi-TUI testing...")
    
    # CRITICAL: Always clear marker file, even if everything fails
    import atexit
    atexit.register(clear_marker_file)
    
    # Also clear immediately at start (safety)
    clear_marker_file()
    log_to_tty1("[MULTI-TUI] Marker file cleared")
    
    # Ensure TTY is blocked
    log_to_tty1("[MULTI-TUI] Blocking TTY services...")
    for tty_num in range(1, 7):
        subprocess.run(['systemctl', 'stop', f'getty@tty{tty_num}.service'], 
                      check=False, capture_output=True)
        subprocess.run(['systemctl', 'mask', f'getty@tty{tty_num}.service'], 
                      check=False, capture_output=True)
    
    log_to_tty1("[MULTI-TUI] Switching to TTY1...")
    subprocess.run(['chvt', '1'], check=False, capture_output=True)
    time.sleep(0.3)
    
    # Try all methods sequentially - user presses any key to advance
    methods = [
        ("Direct TTY Write + input()", method1_direct_tty_write),
        ("Termios Raw Mode", method2_termios_raw),
        ("Read from Console", method3_read_from_console),
        ("stty Raw Mode", method4_stty_raw),
        ("Bash Read", method5_bash_read),
        ("Python Getch", method6_python_getch),
        ("File Descriptor", method7_file_descriptor),
        ("Simple Wait", method8_simple_wait),
        ("Direct Stdin", method9_direct_stdin),
        ("chvt and Wait", method10_chvt_and_wait),
    ]
    
    for method_num, (method_name, method_func) in enumerate(methods, 1):
        log_to_tty1(f"[MULTI-TUI] Preparing method {method_num}/{len(methods)}: {method_name}")
        
        # Display which method we're trying
        try:
            tty_fd = os.open('/dev/tty1', os.O_RDWR)
            method_msg = "\033[2J\033[H"  # Clear screen
            method_msg += "\033[1m\033[33m"  # Bold yellow
            method_msg += "="*70 + "\n"
            method_msg += f"TUI METHOD {method_num}/{len(methods)}: {method_name}\n"
            method_msg += "="*70 + "\n"
            method_msg += "\033[0m\n"
            method_msg += "\033[1mHOMERCHY INSTALLATION COMPLETED!\033[0m\n\n"
            method_msg += "Logs dumped to /root/\n\n"
            method_msg += f"Trying method: \033[1m{method_name}\033[0m\n\n"
            method_msg += "Press ANY KEY to try this method\n"
            method_msg += "="*70 + "\n"
            
            os.write(tty_fd, method_msg.encode('utf-8'))
            os.fsync(tty_fd)
            
            log_to_tty1(f"[MULTI-TUI] Waiting for key press to try method {method_num}...")
            
            # Wait for any key to try this method
            wait_for_any_key_to_continue(tty_fd)
            os.close(tty_fd)
        except Exception as e:
            log_to_tty1(f"[MULTI-TUI] ERROR: Failed to display method prompt: {e}")
            print(f"[MULTI-TUI] Failed to display method prompt: {e}", file=sys.stderr)
        
        log_to_tty1(f"[MULTI-TUI] Executing method {method_num}: {method_name}")
        print(f"[MULTI-TUI] Trying method {method_num}: {method_name}", file=sys.stderr)
        
        try:
            log_to_tty1(f"[MULTI-TUI] Method {method_num} returned, checking result...")
            if method_func():
                log_to_tty1(f"[MULTI-TUI] Method {method_name} SUCCEEDED!")
                print(f"[MULTI-TUI] Method {method_name} succeeded!", file=sys.stderr)
                # Show success message
                try:
                    tty_fd = os.open('/dev/tty1', os.O_RDWR)
                    success_msg = "\033[2J\033[H\033[1m\033[32m" + "="*70 + "\n"
                    success_msg += f"SUCCESS! Method {method_name} worked!\n"
                    success_msg += "="*70 + "\n\033[0m\n"
                    success_msg += "Press ENTER to reboot\n"
                    os.write(tty_fd, success_msg.encode('utf-8'))
                    os.fsync(tty_fd)
                    
                    # Wait for Enter to reboot
                    old_settings = termios.tcgetattr(tty_fd)
                    tty.setraw(tty_fd)
                    while True:
                        if select.select([tty_fd], [], [], 0.5)[0]:
                            key = os.read(tty_fd, 1)
                            if key in (b'\r', b'\n'):
                                break
                    termios.tcsetattr(tty_fd, termios.TCSADRAIN, old_settings)
                    os.close(tty_fd)
                except Exception:
                    pass
                
                # Method succeeded - exit cleanly, NO AUTO-REBOOT
                # User must manually reboot when ready
                print("\n[MULTI-TUI] Method succeeded. Exiting - no automatic reboot.", file=sys.stderr)
                print("[MULTI-TUI] User must manually reboot when ready.", file=sys.stderr)
                return
            else:
                log_to_tty1(f"[MULTI-TUI] Method {method_name} did not work (returned False)")
                print(f"[MULTI-TUI] Method {method_name} did not work", file=sys.stderr)
        except Exception as e:
            log_to_tty1(f"[MULTI-TUI] Method {method_name} CRASHED: {e}")
            print(f"[MULTI-TUI] Method {method_name} crashed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
    
    # If all methods failed, at least clear marker and show message
    print("[MULTI-TUI] All methods failed - clearing marker and showing final message", file=sys.stderr)
    clear_marker_file()
    
    try:
        tty_fd = os.open('/dev/tty1', os.O_RDWR)
        message = "\033[2J\033[H\033[1m\033[31m" + "="*70 + "\n"
        message += "ALL TUI METHODS FAILED\n"
        message += "="*70 + "\n\033[0m\n"
        message += "Logs in /root/\n"
        message += "Marker file cleared - will not run again on reboot\n"
        message += "You can manually reboot when ready\n"
        
        os.write(tty_fd, message.encode('utf-8'))
        os.fsync(tty_fd)
        os.close(tty_fd)
    except Exception:
        pass


if __name__ == "__main__":
    main()
