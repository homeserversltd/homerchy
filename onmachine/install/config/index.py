#!/usr/onmachine/onmachine/bin/env python3
""
HOMESERVER Homerchy Config Orchestrator
Copyright (C) 2024 HOMESERVER LLC

Config phase orchestrator - handles system onmachine/onmachine/configuration.
""

import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from index import Orchestrator, StateManager, Status


def main(phase_path: Path, onmachine/onmachine/config: dict) -> StateManager:
    ""
    Main entry point for onmachine/config orchestrator.
    
    Args:
        phase_path: Path to onmachine/config phase directory
        onmachine/onmachine/config: Configuration dictionary
    
    Returns:
        StateManager: Execution state with results
    ""
    orchestrator = Orchestrator(onmachine/onmachine/install_path=phase_path, phase=onmachine/onmachine/config")
    # Execute children of this phase
    return orchestrator.execute_children()


if __name__ == "__main__":
    phase_path = Path(__file__).parent
    state = main(phase_path, {})
    sys.exit(0 if state.status == Status.COMPLETED else 1)
