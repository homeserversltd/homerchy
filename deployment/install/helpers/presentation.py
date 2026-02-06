"""
Presentation helpers for Homerchy installation.
"""

import os
import subprocess
from pathlib import Path


def init_environment():
    """
    Initialize presentation environment variables.

    Sets up terminal size, logo dimensions, padding, and gum configuration.
    """
    # Get terminal size from /dev/tty
    try:
        result = subprocess.run(
            ['stty', 'size'],
            input=None,
            capture_output=True,
            text=True,
            stdin=open('/dev/tty', 'r')
        )
        if result.returncode == 0 and result.stdout.strip():
            height, width = result.stdout.strip().split()
            term_height = int(height)
            term_width = int(width)
        else:
            term_width = 80
            term_height = 24
    except (subprocess.SubprocessError, ValueError, FileNotFoundError):
        term_width = 80
        term_height = 24

    os.environ['TERM_WIDTH'] = str(term_width)
    os.environ['TERM_HEIGHT'] = str(term_height)

    # Set logo path and dimensions
    omarchy_path = os.environ.get('OMARCHY_PATH', '/root/omarchy')
    logo_path = Path(omarchy_path) / 'icon.txt'
    os.environ['LOGO_PATH'] = str(logo_path)

    # Calculate logo dimensions
    try:
        if logo_path.exists():
            lines = logo_path.read_text().splitlines()
            logo_width = max(len(line) for line in lines) if lines else 0
            logo_height = len(lines)
        else:
            logo_width = 0
            logo_height = 0
    except Exception:
        logo_width = 0
        logo_height = 0

    os.environ['LOGO_WIDTH'] = str(logo_width)
    os.environ['LOGO_HEIGHT'] = str(logo_height)

    # Calculate padding
    padding_left = (term_width - logo_width) // 2
    os.environ['PADDING_LEFT'] = str(padding_left)
    os.environ['PADDING_LEFT_SPACES'] = ' ' * padding_left

    # Set gum configuration (Tokyo Night theme)
    os.environ['GUM_CONFIRM_PROMPT_FOREGROUND'] = '6'     # Cyan for prompt
    os.environ['GUM_CONFIRM_SELECTED_FOREGROUND'] = '0'   # Black text on selected
    os.environ['GUM_CONFIRM_SELECTED_BACKGROUND'] = '2'   # Green background for selected
    os.environ['GUM_CONFIRM_UNSELECTED_FOREGROUND'] = '7' # White for unselected
    os.environ['GUM_CONFIRM_UNSELECTED_BACKGROUND'] = '0' # Black background for unselected
    os.environ['PADDING'] = f'0 0 0 {padding_left}'       # Gum Style
    os.environ['GUM_CHOOSE_PADDING'] = os.environ['PADDING']
    os.environ['GUM_FILTER_PADDING'] = os.environ['PADDING']
    os.environ['GUM_INPUT_PADDING'] = os.environ['PADDING']
    os.environ['GUM_SPIN_PADDING'] = os.environ['PADDING']
    os.environ['GUM_TABLE_PADDING'] = os.environ['PADDING']
    os.environ['GUM_CONFIRM_PADDING'] = os.environ['PADDING']


def clear_logo():
    """
    Clear the screen and display the Homerchy logo.
    """
    # Determine output destination
    tty_output = '/dev/tty'
    if not os.access(tty_output, os.W_OK):
        tty_output = '/dev/stdout'

    # Clear screen and move cursor to top-left
    clear_seq = '\033[H\033[2J'
    try:
        with open(tty_output, 'w') as f:
            f.write(clear_seq)
    except Exception:
        print(clear_seq, end='', flush=True)

    # Display logo
    logo_path = os.environ.get('LOGO_PATH')
    padding_left = os.environ.get('PADDING_LEFT', '0')

    if logo_path and Path(logo_path).exists():
        try:
            logo_content = Path(logo_path).read_text()
            subprocess.run([
                'gum', 'style',
                '--foreground', '2',
                '--padding', f'1 0 0 {padding_left}',
                logo_content
            ], stdout=open(tty_output, 'w'), check=False)
        except Exception:
            # Fallback if gum fails
            try:
                with open(tty_output, 'w') as f:
                    f.write(logo_content)
            except Exception:
                print(logo_content, flush=True)


def gum_style(message, foreground=3):
    """
    Style a message using gum.

    Args:
        message: The message to style
        foreground: Foreground color (default: 3/yellow)
    """
    padding_left = os.environ.get('PADDING_LEFT', '0')
    try:
        subprocess.run([
            'gum', 'style',
            '--foreground', str(foreground),
            '--padding', f'1 0 0 {padding_left}',
            message
        ], check=False)
    except Exception:
        # Fallback if gum fails
        print(message, flush=True)