#!/usr/bin/env python3
"""Capture-hook phase: Display journalctl output and wait for keypress."""
import subprocess
import sys
import termios
import tty
from pathlib import Path
from typing import Any


def run(install_path: Path, state: Any) -> None:
    # (a) Get full journalctl output
    try:
        result = subprocess.run(
            ["journalctl", "-u", "homerchy.service", "--no-pager"],
            capture_output=True,
            text=True,
            timeout=60
        )
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        state.capture_log_content = stdout + stderr
    except subprocess.TimeoutExpired:
        state.capture_log_content = "[journalctl timed out]"
    except subprocess.CalledProcessError as e:
        state.capture_log_content = f"[journalctl failed: {e}]"
    except Exception as e:
        state.capture_log_content = f"[Error getting journal: {e}]"

    # (c) Wait for any keypress on TTY
    try:
        with open('/dev/tty1', 'r') as fd:
            old_settings = termios.tcgetattr(fd)
            tty.setraw(fd)
            fd.read(1)
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except (FileNotFoundError, termios.error, OSError):
        try:
            with open('/dev/tty', 'r') as fd:
                old_settings = termios.tcgetattr(fd)
                tty.setraw(fd)
                fd.read(1)
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except (FileNotFoundError, termios.error, OSError):
            pass  # Continue without keypress

    # (d) Clear capture_log_content
    state.capture_log_content = None


def main(install_path: Path, state: Any) -> None:
    run(install_path, state)