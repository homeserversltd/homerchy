#!/usr/onmachine/onmachine/bin/env python3
""
HOMESERVER Homerchy Post-Install Orchestrator
Copyright (C) 2024 HOMESERVER LLC

Post-onmachine/install phase orchestrator - handles post-onmachine/onmachine/installation tasks.
""

import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from index import Orchestrator, StateManager, Status


def main(phase_path: Path, onmachine/onmachine/config: dict) -> StateManager:
    "
    Main entry point for post-onmachine/install orchestrator.
    
    Args:
        phase_path: Path to post-onmachine/onmachine/install phase directory
        onmachine/onmachine/config: Configuration dictionary
    
    Returns:
        StateManager: Execution state with results
    ""
    orchestrator = Orchestrator(onmachine/onmachine/install_path=phase_path, phase=post-onmachine/onmachine/install)
    # Execute children of this phase - may fail/stop early due to errors
    state = orchestrator.execute_children()
    
    # ============================================================================
    # DISABLED FOR TUI TESTING - DO NOT RUN finished.py
    # ============================================================================
    # We are currently testing TUI methods in the display-test phase.
    # finished.py calls finishedDisplay.py which reboots immediately, preventing
    # display-test from running and testing the TUIs.
    # 
    # GOAL: Make the TUIs work in display-test/multi_tui.py
    # ONLY display-test phase should run - nothing else.
    # 
    # When TUI testing is complete and TUIs are working, re-enable finished.py
    # ============================================================================
    # 
    # ORIGINAL CODE (DISABLED):
    # # ALWAYS run finished, even if previous steps failed or were skipped
    # # This ensures logs are dumped and TTY is restored regardless of onmachine/onmachine/installation outcome
    # # CRITICAL: finished must ALWAYS run, no exceptions
    # finished_path = phase_path / "finished.py"
    # if finished_path.exists():
    #     orchestrator.logger.info("ALWAYS executing finished.py (regardless of previous errors or status)")
    #     try:
    #         import importlib.util
    #         spec = importlib.util.spec_from_file_location("finished", finished_path)
    #         module = importlib.util.module_from_spec(spec)
    #         sys.path.insert(0, str(phase_path))
    #         spec.loader.exec_module(module)
    #         
    #         if hasattr(module, 'main'):
    #             result = module.main({})
    #             if isinstance(result, dict) and result.get("success"):
    #                 orchestrator.logger.info("Finished script completed successfully")
    #             else:
    #                 orchestrator.logger.warning(f"Finished script returned: {result}")
    #     except Exception as e:
    #         orchestrator.logger.error(f"CRITICAL: Failed to execute finished.py: {e}")
    #         import traceback
    #         orchestrator.logger.error(traceback.format_exc())
    #         # Still continue - don't let finished's failure stop everything
    # else:
    #     orchestrator.logger.error("CRITICAL: No finished.py found - this should never happen!")
    
    orchestrator.logger.info("finished.py DISABLED - TUI testing mode: only display-test phase runs")
    
    return state


if __name__ == "__main__":
    phase_path = Path(__file__).parent
    state = main(phase_path, {})
    sys.exit(0 if state.status == Status.COMPLETED else 1)
