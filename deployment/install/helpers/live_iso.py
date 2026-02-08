#!/usr/bin/env python3
"""
HOMESERVER Homerchy – helpers for the live-ISO automated script.
Copyright (C) 2024 HOMESERVER LLC

The ISO .automated_script.py imports helpers from the install path and expects
init_environment, start_install_log, clear_logo, gum_style. These are used only
in the live environment (before first boot); first-boot install uses state + reporting.
"""

import os
import subprocess
from pathlib import Path


def init_environment() -> None:
    """Set up environment for the automated script. No-op if already set."""
    log_file = os.environ.get("HOMERCHY_INSTALL_LOG_FILE", "/var/log/homerchy-install.log")
    os.environ.setdefault("HOMERCHY_INSTALL_LOG_FILE", log_file)


def start_install_log() -> None:
    """Ensure install log file exists and write a starter line."""
    log_file = os.environ.get("HOMERCHY_INSTALL_LOG_FILE", "/var/log/homerchy-install.log")
    path = Path(log_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "a") as f:
            f.write("[automated_script] Install log started\n")
            f.flush()
    except Exception:
        pass


def clear_logo() -> None:
    """Clear display (for live ISO)."""
    try:
        subprocess.run(["clear"], check=False, capture_output=True, timeout=2)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


def gum_style(message: str, foreground: int = 3, padding: str = "1 0 0 4") -> None:
    """Run gum style if available (for live ISO)."""
    try:
        subprocess.run(
            ["gum", "style", "--foreground", str(foreground), "--padding", padding, message],
            check=False,
            capture_output=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
