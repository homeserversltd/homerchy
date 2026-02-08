#!/usr/bin/env python3
"""Preflight: disable mkinitcpio during install to avoid rebuilds at wrong time. Easiest step to confirm engine turnover."""
import subprocess
import sys
from pathlib import Path
from typing import Any

from helpers.logging import append_log


def run(install_path: Path, state: Any) -> None:
    append_log("Disabling mkinitcpio for install", state)
    for cmd in [
        ["systemctl", "disable", "mkinitcpio.service"],
        ["systemctl", "mask", "mkinitcpio.service"],
    ]:
        try:
            subprocess.run(cmd, check=False, capture_output=True, timeout=10)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass


def main(install_path: Path, state: Any) -> None:
    run(install_path, state)


if __name__ == "__main__":
    from state import State
    s = State()
    run(Path(__file__).resolve().parent.parent, s)
    sys.exit(0)
