#!/usr/bin/env python3
"""Hacker-demo phase: run the fake installer demo."""
import importlib.util
import sys
from pathlib import Path
from typing import Any


def main(install_path: Path, state: Any) -> None:
    phase_dir = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("hacker_demo", phase_dir / "demo.py")
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        mod.run(install_path, state)
