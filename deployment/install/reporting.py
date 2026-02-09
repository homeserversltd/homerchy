#!/usr/bin/env python3
"""
HOMESERVER Homerchy first-boot install – display and state reporting.
Copyright (C) 2024 HOMESERVER LLC

Single process: main (install.py) owns the display and holds state. Phases only
report into state. This module is the contract: build message from state, write
to TTY. Main imports it and calls redraw(); orchestrator/phases never draw,
they only mutate state.
"""

import os
from pathlib import Path
from typing import Any, Optional

from state import State


def _get_recent_logs(log_file: str, lines: int = 8) -> list[str]:
    """Return last N lines from log file."""
    try:
        if not Path(log_file).exists():
            return ["[Log file not created yet]"]
        with open(log_file, "r") as f:
            all_lines = f.readlines()
        recent = [line.rstrip() for line in all_lines[-lines:] if line.strip()]
        return recent if recent else ["[Log file is empty]"]
    except Exception as e:
        return [f"[Error reading log: {e}]"]


def build_message(
    state: State,
    run_counter: int,
    status_str: str,
    log_file: str,
    *,
    journalctl_hint: str = "journalctl -u homerchy.service",
) -> str:
    """Build the full-screen status string. Does not write anywhere."""
    if hasattr(state, 'capture_log_content') and state.capture_log_content:
        msg = "\033[2J\033[H"
        msg += state.capture_log_content
        msg += "\nPress any key to continue..."
        return msg
    if getattr(state, "recent_logs", None) and state.recent_logs:
        recent_logs = state.recent_logs[-10:]
    else:
        recent_logs = _get_recent_logs(log_file, lines=10)
    current_step = state.current_step or "none"
    step_display = current_step if current_step not in ("unknown", "none") else "Initializing..."
    error_count = len(state.errors) if hasattr(state, "errors") else 0
    child_info = list(state.children.keys()) if hasattr(state, "children") and state.children else []

    colors = [
        "\033[1m\033[31m", "\033[1m\033[32m", "\033[1m\033[33m",
        "\033[1m\033[34m", "\033[1m\033[35m", "\033[1m\033[36m",
    ]
    header_color = colors[run_counter % len(colors)]

    msg = "\033[2J\033[H"
    msg += header_color
    msg += "=" * 70 + "\n"
    msg += "HOMERCHY INSTALLATION IN PROGRESS\n"
    msg += "=" * 70 + "\n\033[0m\n"
    msg += "\033[33m"
    msg += f"Status: {status_str}\n"
    msg += "\033[0m\033[36m"
    msg += f"Current Step: {step_display}\n"
    msg += f"Run #: {run_counter} | Errors: {error_count}\n"
    msg += "\033[0m"
    if child_info:
        msg += "\033[35m"
        msg += f"Executed: {', '.join(child_info[-5:])}\n"
        msg += "\033[0m"
    msg += "\n\033[32mRecent Logs:\033[0m\n"
    msg += "-" * 70 + "\n"
    for line in recent_logs[-10:]:
        if len(line) > 68:
            line = line[:65] + "..."
        msg += line + "\n"
    msg += "-" * 70 + "\n"
    msg += f"\033[2mDetails: {journalctl_hint}\033[0m\n"
    return msg


def write_display(message: str, devices: tuple[str, ...] = ("/dev/tty1", "/dev/console")) -> None:
    """Write the message to the given TTY devices. Main owns these; phases never call this."""
    for dev in devices:
        try:
            with open(dev, "w") as f:
                f.write(message)
                f.flush()
        except Exception:
            pass


def redraw(
    state: State,
    run_counter: int,
    status_str: str,
    log_file: Optional[str] = None,
) -> None:
    """Build message from state and write to display. Main calls this (e.g. every 2s and on status change)."""
    if log_file is None:
        log_file = os.environ.get("HOMERCHY_INSTALL_LOG_FILE", "/var/log/homerchy-install.log")
    msg = build_message(state, run_counter, status_str, log_file)
    write_display(msg)
