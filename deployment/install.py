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

# Global status for persistent message
_current_status = "Starting installation..."
_run_counter = 0  # Set by get_or_increment_run_counter()
_orchestrator_instance = None  # Global reference for state access


def get_or_increment_run_counter() -> int:
    """Get or increment the run counter from /tmp/work/homerchy.pid.
    Resets on reboot (tmp cleared). Returns current counter value."""
    pid_file = Path('/tmp/work/homerchy.pid')
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        if pid_file.exists():
            counter = int(pid_file.read_text().strip()) + 1
        else:
            counter = 1
        pid_file.write_text(str(counter))
        return counter
    except Exception as e:
        print(f"[INSTALL] WARNING: Failed to read/increment run counter: {e}", file=sys.stderr)
        return 1


def _get_recent_logs(log_file: str, lines: int = 8) -> list:
    """Return last N lines from log file."""
    try:
        if not Path(log_file).exists():
            return ["[Log file not created yet]"]
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
        recent = [line.rstrip() for line in all_lines[-lines:] if line.strip()]
        return recent if recent else ["[Log file is empty]"]
    except Exception as e:
        return [f"[Error reading log: {e}]"]


def _get_orchestrator_info() -> tuple:
    """Current step, error count, and executed children from orchestrator if available."""
    global _orchestrator_instance
    current_step = "unknown"
    error_count = 0
    child_info = []
    try:
        if _orchestrator_instance and hasattr(_orchestrator_instance, 'state'):
            state = _orchestrator_instance.state
            current_step = state.current_step or "none"
            error_count = len(state.errors) if hasattr(state, 'errors') else 0
            if hasattr(state, 'children') and state.children:
                child_info = list(state.children.keys())
    except Exception:
        pass
    return current_step, error_count, child_info


def display_persistent_message():
    """Draw full-screen status on TTY1 and console. Refreshes every 2s from background thread."""
    global _current_status, _run_counter

    log_file = os.environ.get('HOMERCHY_INSTALL_LOG_FILE', '/var/log/homerchy-install.log')
    recent_logs = _get_recent_logs(log_file, lines=8)
    current_step, error_count, child_info = _get_orchestrator_info()

    # Friendly label when orchestrator not running yet
    step_display = current_step if current_step not in ("unknown", "none") else "Initializing..."

    colors = [
        "\033[1m\033[31m", "\033[1m\033[32m", "\033[1m\033[33m",
        "\033[1m\033[34m", "\033[1m\033[35m", "\033[1m\033[36m",
    ]
    header_color = colors[_run_counter % len(colors)]

    try:
        msg = "\033[2J\033[H"  # Clear screen and home cursor
        msg += header_color
        msg += "=" * 70 + "\n"
        msg += "HOMERCHY INSTALLATION IN PROGRESS\n"
        msg += "=" * 70 + "\n\033[0m\n"
        msg += "\033[33m"
        msg += f"Status: {_current_status}\n"
        msg += "\033[0m\033[36m"
        msg += f"Current Step: {step_display}\n"
        msg += f"Run #: {_run_counter} | Errors: {error_count}\n"
        msg += "\033[0m"
        if child_info:
            msg += "\033[35m"
            msg += f"Executed: {', '.join(child_info[-5:])}\n"
            msg += "\033[0m"
        msg += "\n\033[32mRecent Logs:\033[0m\n"
        msg += "-" * 70 + "\n"
        for line in recent_logs[-6:]:
            if len(line) > 68:
                line = line[:65] + "..."
            msg += line + "\n"
        msg += "-" * 70 + "\n"
        msg += "\033[2mDetails: journalctl -u homerchy-first-boot-install.service\033[0m\n"

        for dev in ('/dev/tty1', '/dev/console'):
            try:
                with open(dev, 'w') as f:
                    f.write(msg)
                    f.flush()
            except Exception:
                pass
    except Exception as e:
        print(f"WARNING: Failed to display message: {e}", file=sys.stderr)


def update_status(status: str):
    """Set status and redraw the persistent message once."""
    global _current_status
    _current_status = status
    print(f"[STATUS UPDATE] {status}", file=sys.stderr)
    display_persistent_message()


def persistent_message_loop():
    """Background thread: refresh the status screen every 2 seconds."""
    while True:
        try:
            display_persistent_message()
            time.sleep(2)
        except Exception:
            break


def block_tty_and_display_message():
    """Stop/mask/disable gettys, switch to tty1, show persistent status screen."""
    try:
        for tty_num in range(1, 7):
            subprocess.run(['systemctl', 'stop', f'getty@tty{tty_num}.service'],
                          check=False, capture_output=True)
            subprocess.run(['systemctl', 'mask', f'getty@tty{tty_num}.service'],
                          check=False, capture_output=True)
            subprocess.run(['systemctl', 'disable', f'getty@tty{tty_num}.service'],
                          check=False, capture_output=True)
        subprocess.run(['chvt', '1'], check=False, capture_output=True)
        time.sleep(0.2)
        display_persistent_message()
        print("[INSTALL] TTY blocked, status displayed", file=sys.stderr)
    except Exception as e:
        print(f"WARNING: Failed to block TTY: {e}", file=sys.stderr)


def unblock_tty_login():
    """Unmask gettys and start getty on tty1."""
    try:
        for tty_num in range(1, 7):
            subprocess.run(['systemctl', 'unmask', f'getty@tty{tty_num}.service'],
                          check=False, capture_output=True)
        subprocess.run(['systemctl', 'start', 'getty@tty1.service'],
                      check=False, capture_output=True)
        print("[INSTALL] TTY login unblocked", file=sys.stderr)
    except Exception as e:
        print(f"WARNING: Failed to unblock TTY: {e}", file=sys.stderr)


def main():
    """Block TTY, show status (refreshing every 2s), sleep 5s, unblock, remove marker. No orchestrator yet."""
    global _run_counter

    _run_counter = get_or_increment_run_counter()
    print(f"[INSTALL] Run # {_run_counter}", file=sys.stderr)

    block_tty_and_display_message()
    threading.Thread(target=persistent_message_loop, daemon=True).start()

    time.sleep(5)

    unblock_tty_login()
    marker = Path('/var/lib/homerchy-install-needed')
    if marker.exists():
        marker.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
