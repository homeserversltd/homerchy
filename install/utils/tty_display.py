#!/usr/bin/env python3
"""
HOMESERVER Homerchy Installation TTY Display Utility
Copyright (C) 2024 HOMESERVER LLC

Utility module for updating TTY1 display during installation.
Allows installation modules to show progress on TTY1.
"""

import os
import sys
import subprocess
from pathlib import Path


def update_tty_display(message: str, phase: str = ""):
    """
    Update TTY1 display with installation progress.
    
    Args:
        message: Message to display
        phase: Optional phase name to show
    """
    if os.environ.get('OMARCHY_TTY_CONTROLLER') != 'active':
        return  # TTY control not active, skip
    
    try:
        tty_device = '/dev/tty1'
        
        # Build display text
        if phase:
            display_text = f'Phase: {phase} - {message}'
        else:
            display_text = message
        
        # Write to TTY1 (move to line 3 to avoid overwriting header)
        try:
            with open(tty_device, 'w') as tty1:
                # Move cursor to line 3, column 1, clear line, write message
                tty1.write(f'\033[3;1H\033[K{display_text}\033[K')
                tty1.flush()
        except (PermissionError, FileNotFoundError):
            # Fallback: use subprocess with shell redirection
            subprocess.run(
                ['bash', '-c', f'echo -ne "\\033[3;1H\\033[K{display_text}\\033[K" > {tty_device}'],
                check=False,
                stderr=subprocess.DEVNULL
            )
    except Exception:
        # Silently fail - TTY updates are non-critical
        pass


def show_tty_message(message: str, clear_first: bool = False):
    """
    Show a message on TTY1.
    
    Args:
        message: Message to display
        clear_first: Whether to clear screen first
    """
    if os.environ.get('OMARCHY_TTY_CONTROLLER') != 'active':
        return  # TTY control not active, skip
    
    try:
        tty_device = '/dev/tty1'
        
        try:
            with open(tty_device, 'w') as tty1:
                if clear_first:
                    tty1.write('\033[2J\033[H')  # Clear screen and move to top
                tty1.write(f'{message}\n')
                tty1.flush()
        except (PermissionError, FileNotFoundError):
            # Fallback: use subprocess
            if clear_first:
                subprocess.run(
                    ['bash', '-c', f'echo -ne "\\033[2J\\033[H{message}\\n" > {tty_device}'],
                    check=False,
                    stderr=subprocess.DEVNULL
                )
            else:
                subprocess.run(
                    ['bash', '-c', f'echo "{message}" > {tty_device}'],
                    check=False,
                    stderr=subprocess.DEVNULL
                )
    except Exception:
        # Silently fail - TTY updates are non-critical
        pass







