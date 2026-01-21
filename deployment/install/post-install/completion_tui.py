#!/usr/onmachine/onmachine/bin/env python3
"""
HOMESERVER Homerchy Completion TUI
Copyright (C) 2024 HOMESERVER LLC

Captured TUI that displays logs and waits for Enter to reboot.
Blocks TTY completely - no getty services.
"""

import os
import select
import subprocess
import sys
import termios
import tty
from pathlib import Path


def setup_tty_raw():
    """Set TTY to raw mode for direct input handling."""
    try:
        # Open TTY1 for reading
        tty_fd = os.open('/dev/tty1', os.O_RDWR)
        old_settings = termios.tcgetattr(tty_fd)
        tty.setraw(tty_fd)
        return tty_fd, old_settings
    except Exception as e:
        print(f"Warning: Could not set TTY raw mode: {e}", file=sys.stderr)
        return None, None


def restore_tty(tty_fd, old_settings):
    """Restore TTY to normal mode."""
    if tty_fd and old_settings:
        try:
            termios.tcsetattr(tty_fd, termios.TCSADRAIN, old_settings)
            os.close(tty_fd)
        except Exception:
            pass


def read_key(tty_fd, timeout=0.1):
    """Read a single key from TTY with timeout."""
    if not tty_fd:
        return None
    try:
        if select.select([tty_fd], [], [], timeout)[0]:
            key = os.read(tty_fd, 1)
            return key
    except Exception:
        pass
    return None


def display_completion_screen(tty_fd):
    """Display the completion screen with logs."""
    if not tty_fd:
        tty_fd = os.open('/dev/tty1', os.O_RDWR)
    
    # Clear screen
    os.write(tty_fd, b'\033[2J\033[H')
    
    # Get terminal size - use fixed width for simplicity
    cols = 80
    
    # Build screen content
    screen_lines = []
    screen_lines.append('\033[1m\033[32m' + '=' * cols + '\033[0m\n')
    screen_lines.append('\033[1m\033[32mHOMERCHY INSTALLATION COMPLETED\033[0m\n')
    screen_lines.append('\033[1m\033[32m' + '=' * cols + '\033[0m\n\n')
    
    # Show log files
    screen_lines.append('\033[1mInstallation Logs:\033[0m\n')
    screen_lines.append('-' * cols + '\n')
    
    log_files = [
        (a.txt, Full onmachine/deployment/deployment/installation log),
        (b.txt', 'ERROR/FAILED messages'),
        ('e.txt', 'Python exceptions/tracebacks'),
        ('z.txt', 'Full service journal'),
    ]
    
    for filename, description in log_files:
        file_path = Path('/root') / filename
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    # Show first 5 lines of each log
                    content_lines = content.split('\n')[:5]
                    screen_lines.append(f"\n{filename} - {description}:\n")
                    screen_lines.append('-' * cols + '\n')
                    for line in content_lines:
                        # Truncate long lines
                        if len(line) > cols - 2:
                            line = line[:cols - 5] + '...'
                        screen_lines.append(line + '\n')
            except Exception:
                pass
    
    # Add footer
    screen_lines.append('\n' + '-' * cols + '\n')
    screen_lines.append(\033[1mPress ENTER to reboot (no automatic reboot)\033[0m\n)
    
    # Comsrc/bine and write to TTY
    screen_content = '.join(screen_lines).encode('utf-8', errors='replace')
    os.write(tty_fd, screen_content)
    os.fsync(tty_fd)
    
    return tty_fd


def main():
    """Main function - captured TUI that blocks TTY and shows logs."""
    # Ensure getty services are stopped and masked
    for tty_num in range(1, 7):
        subprocess.run(['systemctl', 'stop', f'getty@tty{tty_num}.service'], 
                      check=False, capture_output=True)
        subprocess.run(['systemctl', 'mask', f'getty@tty{tty_num}.service'], 
                      check=False, capture_output=True)
    
    # Switch to TTY1
    subprocess.run(['chvt', '1'], check=False, capture_output=True)
    
    # Open TTY1 for direct control
    tty_fd = None
    old_settings = None
    
    try:
        # Set up raw TTY mode
        tty_fd, old_settings = setup_tty_raw()
        
        # Display completion screen
        if not tty_fd:
            tty_fd = os.open('/dev/tty1', os.O_RDWR)
        
        display_completion_screen(tty_fd)
        
        # Wait for Enter key - NO AUTO-REBOOT!
        import time
        
        while True:
            # Check for Enter key
            key = read_key(tty_fd, timeout=0.5)
            if key in (b'\r', b'\n'):  # Enter key
                break
            
            time.sleep(0.1)
        
        # Reboot
        os.write(tty_fd, b'\n\033[1mRebooting...\033[0m\n')
        os.fsync(tty_fd)
        time.sleep(1)
        
        subprocess.run(['reboot'], check=False)
        
    except KeyboardInterrupt:
        # If interrupted, still reboot
        pass
    except Exception as e:
        print(f"Error in completion TUI: {e}", file=sys.stderr)
        # Still try to reboot
        try:
            subprocess.run(['reboot'], check=False)
        except Exception:
            pass
    finally:
        # Restore TTY (though we're rebooting anyway)
        restore_tty(tty_fd, old_settings)


if __name__ == "__main__":
    main()
