#!/usr/bin/env python3
"""
HOMESERVER Homerchy Display Test Orchestrator
Copyright (C) 2024 HOMESERVER LLC

Display test phase orchestrator - handles TTY display testing.
"""

import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from index import Orchestrator, StateManager, Status


def main(phase_path: Path, config: dict) -> StateManager:
    """
    Main entry point for display-test orchestrator.
    
    Args:
        phase_path: Path to display-test phase directory
        config: Configuration dictionary
    
    Returns:
        StateManager: Execution state with results
    """
    orchestrator = Orchestrator(install_path=phase_path, phase="display-test")
    # Execute children of this phase
    return orchestrator.execute_children()


if __name__ == "__main__":
    phase_path = Path(__file__).parent
    state = main(phase_path, {})
    sys.exit(0 if state.status == Status.COMPLETED else 1)
