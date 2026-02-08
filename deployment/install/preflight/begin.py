#!/usr/bin/env python3
"""Preflight begin: log installation start. Easiest step to confirm engine turnover."""
import subprocess
import sys
from pathlib import Path
from typing import Any

# install_path is on sys.path when we're run by preflight
from helpers.logging import append_log


def run(install_path: Path, state: Any) -> None:
    append_log("Installing...", state)
    try:
        subprocess.run(
            ["gum", "style", "--foreground", "3", "--padding", "1 0 0 4", "Installing..."],
            check=False,
            capture_output=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


def main(install_path: Path, state: Any) -> None:
    run(install_path, state)


if __name__ == "__main__":
    from state import State
    s = State()
    run(Path(__file__).resolve().parent.parent, s)
    sys.exit(0)
