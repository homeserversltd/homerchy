#!/usr/bin/env python3
"""
HOMESERVER Homerchy Post-Install All
Copyright (C) 2024 HOMESERVER LLC

Python equivalent of all.sh - executes post-install phase children.
Uses the orchestrator system for proper execution and logging.
"""

import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from index import Orchestrator, StateManager, Status


def main():
    """Main entry point - executes post-install phase."""
    phase_path = Path(__file__).parent
    orchestrator = Orchestrator(install_path=phase_path, phase="post-install")
    state = orchestrator.execute_children()
    
    # Always ensure finished runs, even if previous steps failed
    # Check if finished was executed
    finished_executed = any(
        child_name == "finished" and child_state.status != Status.SKIPPED
        for child_name, child_state in state.children.items()
    )
    
    if not finished_executed:
        # Manually execute finished if it was skipped
        finished_path = phase_path / "finished.py"
        if finished_path.exists():
            orchestrator.logger.info("Executing finished.py (was skipped)")
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("finished", finished_path)
                module = importlib.util.module_from_spec(spec)
                sys.path.insert(0, str(phase_path))
                spec.loader.exec_module(module)
                
                if hasattr(module, 'main'):
                    result = module.main({})
                    if isinstance(result, dict) and result.get("success"):
                        orchestrator.logger.info("Finished script completed")
                    else:
                        orchestrator.logger.warning(f"Finished script returned: {result}")
            except Exception as e:
                orchestrator.logger.error(f"Failed to execute finished.py: {e}")
        else:
            orchestrator.logger.warning("No finished.py found - finished step will be skipped")
    
    return state


if __name__ == "__main__":
    state = main()
    sys.exit(0 if state.status == Status.COMPLETED else 1)

