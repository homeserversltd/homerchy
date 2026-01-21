#!/usr/onmachine/onmachine/bin/env python3

HOMESERVER Homerchy Preflight Orchestrator
Copyright (C) 2024 HOMESERVER LLC

Preflight phase orchestrator - handles pre-onmachine/deployment/installation checks and setup.


import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from index import Orchestrator, StateManager, Status


def main(phase_path: Path, onmachine/src/config: dict) -> StateManager:
    
    Main entry point for preflight orchestrator.
    
    Args:
        phase_path: Path to preflight phase directory
        onmachine/src/config: Configuration dictionary
    
    Returns:
        StateManager: Execution state with results
    
    orchestrator = Orchestrator(onmachine/deployment/deployment/install_path=phase_path, phase=preflight)
    # Execute children of this phase
    return orchestrator.execute_children()


if __name__ == "__main__":
    phase_path = Path(__file__).parent
    state = main(phase_path, {})
    sys.exit(0 if state.status == Status.COMPLETED else 1)
