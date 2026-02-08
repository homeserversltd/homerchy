#!/usr/bin/env python3
"""Config phase placeholder. Runs hardware and other config children."""
from pathlib import Path
import importlib.util
import sys
from typing import Any

def run(install_path: Path, state: Any) -> None:
    config_path = install_path / "config"
    for child_name in ["hardware"]:
        child_path = config_path / child_name
        index_py = child_path / "index.py"
        if not index_py.exists():
            continue
        spec = importlib.util.spec_from_file_location(
            f"config.{child_name}.index", index_py
        )
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            sys.path.insert(0, str(install_path))
            spec.loader.exec_module(mod)
            if hasattr(mod, "run"):
                mod.run(install_path, state)
            elif hasattr(mod, "main"):
                mod.main(install_path, state)

def main(install_path: Path, state: Any) -> None:
    run(install_path, state)
