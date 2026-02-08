#!/usr/bin/env python3
"""Post-install phase placeholder. Completion TUI, unblock TTY."""
from pathlib import Path
from typing import Any

def run(install_path: Path, state: Any) -> None:
    pass

def main(install_path: Path, state: Any) -> None:
    run(install_path, state)
