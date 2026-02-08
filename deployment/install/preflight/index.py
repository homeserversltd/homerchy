#!/usr/bin/env python3
"""
HOMESERVER Homerchy first-boot install – preflight phase orchestrator.
Copyright (C) 2024 HOMESERVER LLC

Runs preflight steps in order (guard, begin, show_env, ...). Each step
receives (install_path, state); state is the shared State from main.
Uses helpers.errors.record_error on failure.
"""

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

# When run, install_path is on sys.path (root install dir)
from helpers.errors import record_error


def run(install_path: Path, state: Any) -> None:
    """Run preflight children in order. Mutates state only; no display."""
    phase_path = install_path / "preflight"
    config_path = phase_path / "index.json"
    if not config_path.exists():
        return
    with open(config_path, "r") as f:
        config = json.load(f)
    children = config.get("children", [])
    continue_on_error = config.get("execution", {}).get("continue_on_error", False)

    for child_name in children:
        state.current_step = f"preflight.{child_name}"
        child_module_path = phase_path / f"{child_name}.py"
        if not child_module_path.exists():
            state.children[child_name] = "skip (no module)"
            continue

        try:
            _run_step(child_module_path, child_name, install_path, state)
            state.children[child_name] = "ok"
        except Exception as e:
            record_error(state, child_name, str(e))
            if not continue_on_error:
                raise

    state.current_step = "preflight"


def _run_step(module_path: Path, step_name: str, install_path: Path, state: Any) -> None:
    """Load step module and call run(install_path, state) or main(install_path, state)."""
    spec = importlib.util.spec_from_file_location(
        f"preflight.{step_name}",
        module_path,
    )
    if spec is None or spec.loader is None:
        return
    module = importlib.util.module_from_spec(spec)
    parent_path = str(install_path)
    if parent_path not in sys.path:
        sys.path.insert(0, parent_path)
    spec.loader.exec_module(module)

    if hasattr(module, "run"):
        module.run(install_path, state)
    elif hasattr(module, "main"):
        module.main(install_path, state)


def main(install_path: Path, state: Any) -> None:
    run(install_path, state)
