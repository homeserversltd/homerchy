#!/usr/bin/env python3
"""Preflight phase placeholder. Run before packaging."""
from pathlib import Path
from typing import Any

def run(install_path: Path, state: Any) -> None:
    pass

def main(install_path: Path, state: Any) -> None:
    run(install_path, state)
