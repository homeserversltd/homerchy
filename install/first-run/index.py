#!/usr/bin/env python3
"""
HOMESERVER Homerchy First-Run Orchestrator
Copyright (C) 2024 HOMESERVER LLC

First-run phase orchestrator - handles first boot tasks.
"""

import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from index import Orchestrator, StateManager, Status


def main(phase_path: Path, config: dict) -> StateManager:
    """
    Main entry point for first-run orchestrator.
    
    Args:
        phase_path: Path to first-run phase directory
        config: Configuration dictionary
    
    Returns:
        StateManager: Execution state with results
    """
    orchestrator = Orchestrator(install_path=phase_path, phase="first-run")
    # Execute children of this phase
    return orchestrator.execute_children()


if __name__ == "__main__":
    phase_path = Path(__file__).parent
    state = main(phase_path, {})
    sys.exit(0 if state.status == Status.COMPLETED else 1)
