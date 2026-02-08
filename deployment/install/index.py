#!/usr/bin/env python3
"""
HOMESERVER Homerchy first-boot install root orchestrator.
Copyright (C) 2024 HOMESERVER LLC

Loads index.json and runs child phases in order. Compatible with install.py
entry point (Orchestrator(install_path=..., phase="root"), .run() -> state).
State is owned by main; pass state= so display stays in sync.
"""

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Optional

from state import State, Status


class Orchestrator:
    """Root orchestrator: loads index.json and runs child phases sequentially."""

    def __init__(
        self,
        install_path: Path,
        phase: str = "root",
        state: Optional[State] = None,
    ) -> None:
        self.install_path = Path(install_path)
        self.phase = phase
        self.config_path = self.install_path / "index.json"
        self.config = self._load_config()
        self.state = state if state is not None else State()

    def _load_config(self) -> dict:
        if not self.config_path.exists():
            return {"children": [], "execution": {}}
        with open(self.config_path, "r") as f:
            return json.load(f)

    def run(self) -> State:
        """Execute child phases in order. Returns state with status COMPLETED or FAILED."""
        children = self.config.get("children", [])
        continue_on_error = self.config.get("execution", {}).get("continue_on_error", False)

        for child_name in children:
            self.state.current_step = child_name
            child_path = self.install_path / child_name
            index_py = child_path / "index.py"

            if not index_py.exists():
                self.state.children[child_name] = "skip (no index.py)"
                continue

            try:
                self._run_child(child_path, child_name)
                self.state.children[child_name] = "ok"
            except Exception as e:
                self.state.errors.append(f"{child_name}: {e}")
                self.state.children[child_name] = str(e)
                if not continue_on_error:
                    self.state.status = Status.FAILED
                    return self.state

        self.state.status = Status.COMPLETED
        self.state.current_step = "none"
        return self.state

    def _run_child(self, child_path: Path, child_name: str) -> None:
        """Import child's index.py and call run(install_path, state)."""
        spec = importlib.util.spec_from_file_location(
            f"install.{child_name}.index",
            child_path / "index.py",
        )
        if spec is None or spec.loader is None:
            return
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        parent_path = str(self.install_path)
        if parent_path not in sys.path:
            sys.path.insert(0, parent_path)
        spec.loader.exec_module(module)

        if hasattr(module, "run"):
            module.run(self.install_path, self.state)
        elif hasattr(module, "main"):
            module.main(self.install_path, self.state)
