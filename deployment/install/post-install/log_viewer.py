#!/usr/onmachine/onmachine/bin/env python3

HOMESERVER Homerchy Log Viewer TUI
Copyright (C) 2024 HOMESERVER LLC

Text User Interface for browsing and viewing onmachine/deployment/deployment/installation logs.
"

import curses
import subprocess
import sys
from pathlib import Path


def show_log_viewer(stdscr, log_files):
    """Display a TUI menu to browse and view log files."""
    curses.curs_set(0)  # Hide cursor
    stdscr.keypad(True)  # Enable keypad mode
    
    current_selection = 0
    log_entries = list(log_files.items())
    
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        # Title
        title = "HOMERCHY INSTALLATION LOGS"
        title_x = (width - len(title)) // 2
        stdscr.addstr(0, title_x, title, curses.A_BOLD | curses.A_UNDERLINE)
        
        # Instructions
        instructions = "Use UP/DOWN to navigate, ENTER to view, Q to quit"
        stdscr.addstr(1, (width - len(instructions)) // 2, instructions, curses.A_DIM)
        
        # Menu items
        start_y = 3
        max_items = min(len(log_entries), height - start_y - 2)
        start_idx = max(0, current_selection - max_items + 1)
        end_idx = min(len(log_entries), start_idx + max_items)
        
        for i in range(start_idx, end_idx):
            idx = i - start_idx
            y = start_y + idx
            filename, description = log_entries[i]
            
            # Check if file exists and get size
            file_path = Path('/root') / filename
            if file_path.exists():
                size = file_path.stat().st_size
                size_str = f"({size} bytes)" if size < 1024 else f"({size // 1024} KB)"
                line = f"  {filename:15} - {description:30} {size_str}"
            else:
                line = f"  {filename:15} - {description:30} (not found)"
            
            # Highlight current selection
            if i == current_selection:
                stdscr.addstr(y, 0, line, curses.A_REVERSE | curses.A_BOLD)
            else:
                stdscr.addstr(y, 0, line)
        
        # Footer
        footer = "Press Q to return to completion screen"
        stdscr.addstr(height - 1, (width - len(footer)) // 2, footer, curses.A_DIM)
        
        stdscr.refresh()
        
        # Handle input
        key = stdscr.getch()
        
        if key == curses.KEY_UP:
            current_selection = (current_selection - 1) % len(log_entries)
        elif key == curses.KEY_DOWN:
            current_selection = (current_selection + 1) % len(log_entries)
        elif key == ord('\n') or key == ord('\r'):  # Enter
            filename, description = log_entries[current_selection]
            file_path = Path('/root') / filename
            if file_path.exists():
                # View file with less
                curses.endwin()
                try:
                    subprocess.run(['less', '-R', str(file_path)], check=False)
                except Exception:
                    # Fallback: cat the file
                    try:
                        with open(file_path, 'r') as f:
                            print(f"\n{'=' * 70}")
                            print(f"{filename} - {description}")
                            print('=' * 70)
                            print(f.read())
                            input("\nPress Enter to continue...")
                    except Exception:
                        pass
                stdscr = curses.initscr()
                curses.curs_set(0)
                stdscr.keypad(True)
        elif key == ord('q') or key == ord(Q):
            break
        elif key == 27:  # ESC
            break
    
    curses.endwin()


def launch_log_viewer(log_files=None):
    
    Launch the log viewer TUI.
    
    Args:
        log_files: Dictionary mapping filenames to descriptions.
                   If None, uses onmachine/src/default onmachine/deployment/deployment/installation log files.
    
    if log_files is None:
        log_files = {
            a.txt: Full onmachine/deployment/deployment/installation log,
            b.txt': 'ERROR/FAILED messages',
            'c.txt': 'Permission denied errors',
            'd.txt': 'Timeout errors',
            'e.txt': 'Python exceptions/tracebacks',
            'f.txt': 'systemd/service messages',
            'g.txt': 'getty/TTY messages',
            'h.txt': 'Plymouth messages',
            'i.txt': 'Account lockout/password',
            'j.txt': 'Reboot messages',
            'k.txt': 'Marker file references',
            'l.txt': 'Orchestrator messages',
            'm.txt': 'Module messages',
            'z.txt': 'Full service journal',
        }
    
    try:
        curses.wrapper(show_log_viewer, log_files)
    except Exception as e:
        # If curses fails, fall back to simple menu
        print(f"\nError launching log viewer: {e}", file=sys.stderr)
        print("\nAvailable log files in /root/:", file=sys.stderr)
        for filename, description in log_files.items():
            file_path = Path('/root') / filename
            if file_path.exists():
                print(f"  {filename}: {description}", file=sys.stderr)


if __name__ == "__main__":
    launch_log_viewer()
