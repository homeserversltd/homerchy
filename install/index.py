#!/usr/bin/env python3
"""
HOMESERVER Homerchy Installation Orchestrator
Copyright (C) 2024 HOMESERVER LLC

Root orchestrator for Homerchy installation system.
Implements infinite nesting pattern with index.py/index.json at each level.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))

from utils import (
    StateManager, Logger, ConfigLoader, ChildExecutor, ErrorHandler, Status
)


class Orchestrator:
    """Base orchestrator class for Homerchy installation."""
    
    def __init__(self, install_path: Optional[Path] = None, phase: str = "root"):
        self.phase = phase
        self.install_path = install_path or Path(__file__).parent
        self.config_path = self.install_path / "index.json"
        
        # Load configuration
        try:
            self.config = ConfigLoader.load(self.config_path)
            ConfigLoader.validate(self.config, ["metadata", "children"])
        except Exception as e:
            raise RuntimeError(f"Failed to load orchestrator config: {e}")
        
        # Resolve paths from config
        self.paths = self._resolve_paths(self.config.get("paths", {}))
        
        # Setup logging
        log_file = self.paths.get("log_file", "/var/log/omarchy-install.log")
        self.logger = Logger(log_file, phase=self.phase, console=True)
        
        # Initialize state manager
        self.state = StateManager(phase=self.phase)
        self.state.config = self.config
        
        # Initialize child executor
        self.executor = ChildExecutor(self.state, self.logger)
        
        self.logger.info(f"=== {self.phase.upper()} ORCHESTRATOR STARTED ===")
        self.logger.info(f"Install path: {self.install_path}")
        self.logger.info(f"Config path: {self.config_path}")
    
    def _resolve_paths(self, paths_config: Dict[str, str]) -> Dict[str, str]:
        """Resolve environment variables in path configuration."""
        resolved = {}
        for key, value in paths_config.items():
            # Expand environment variables
            resolved_value = os.path.expandvars(value)
            # Store as absolute path if it's a file path
            if key.endswith("_file") or key.endswith("_path"):
                resolved[key] = resolved_value
            else:
                resolved[key] = resolved_value
        return resolved
    
    def execute_phase(self, phase_name: str) -> StateManager:
        """Execute a specific phase."""
        phase_config = self.config.get("phases", {}).get(phase_name, {})
        
        if not phase_config.get("enabled", True):
            self.logger.info(f"Phase {phase_name} is disabled, skipping")
            phase_state = StateManager(phase=phase_name)
            phase_state.set_status(Status.SKIPPED)
            return phase_state
        
        self.logger.info(f"=== Starting phase: {phase_name} ===")
        self.state.current_step = phase_name
        
        # Get phase directory
        phase_path = self.install_path / phase_name
        
        if not phase_path.exists():
            self.logger.error(f"Phase directory not found: {phase_path}")
            phase_state = StateManager(phase=phase_name)
            phase_state.set_status(Status.FAILED)
            phase_state.add_error(f"Phase directory not found: {phase_path}")
            return phase_state
        
        # Check for phase orchestrator (index.py)
        phase_index = phase_path / "index.py"
        if phase_index.exists():
            # Execute nested orchestrator
            phase_state = self.executor.execute_child(phase_path, phase_name, self.config)
        else:
            # Phase has no orchestrator, mark as skipped
            self.logger.warning(f"Phase {phase_name} has no orchestrator (index.py)")
            phase_state = StateManager(phase=phase_name)
            phase_state.set_status(Status.SKIPPED)
        
        # Add phase state as child
        self.state.add_child(phase_name, phase_state)
        
        # Propagate errors if needed
        if phase_state.has_errors():
            should_continue = ErrorHandler.should_continue_on_error(
                self.config.get("execution", {}),
                phase_name
            )
            if not should_continue:
                self.state.set_status(Status.FAILED)
                ErrorHandler.propagate_errors(phase_state, self.state)
                self.logger.error(f"Phase {phase_name} failed and error handling is strict")
                return self.state
        
        self.logger.info(f"=== Completed phase: {phase_name} ===")
        return phase_state
    
    def execute_children(self) -> StateManager:
        """Execute all children of this orchestrator."""
        self.state.set_status(Status.RUNNING)
        children = self.config.get("children", [])
        
        for child_name in children:
            self.state.current_step = child_name
            self.logger.info(f"[PARENT-CHILD] Executing child: {child_name}")
            
            # Check for nested orchestrator (subdirectory with index.py)
            child_dir = self.install_path / child_name
            nested_orchestrator = child_dir / "index.py"
            direct_module = self.install_path / f"{child_name}.py"
            
            self.logger.info(f"[PARENT-CHILD] Checking paths for {child_name}:")
            self.logger.info(f"  install_path: {self.install_path}")
            self.logger.info(f"  child_dir: {child_dir}")
            self.logger.info(f"  nested_orchestrator ({nested_orchestrator}): EXISTS={nested_orchestrator.exists()}")
            self.logger.info(f"  direct_module ({direct_module}): EXISTS={direct_module.exists()}")
            
            if nested_orchestrator.exists():
                self.logger.info(f"[PARENT-CHILD] {child_name} -> NESTED ORCHESTRATOR path")
                child_state = self.executor.execute_child(child_dir, child_name, self.config)
            # Check for direct module (child_name.py in current directory)
            elif direct_module.exists():
                self.logger.info(f"[PARENT-CHILD] {child_name} -> DIRECT MODULE path")
                # Create a dummy path for the executor (it will use parent directory)
                child_state = self.executor.execute_child(self.install_path, child_name, self.config)
            else:
                self.logger.error(f"[PARENT-CHILD] {child_name} -> NOT FOUND")
                self.logger.error(f"Child {child_name} not found (no index.py or {child_name}.py)")
                child_state = StateManager(phase=child_name)
                child_state.set_status(Status.FAILED)
                child_state.add_error(f"Child {child_name} not found - Python-only installation requires index.py or {child_name}.py")
            
            # Add child state
            self.state.add_child(child_name, child_state)
            
            # Check for errors
            if child_state.has_errors():
                should_continue = ErrorHandler.should_continue_on_error(
                    self.config.get("execution", {}),
                    child_name
                )
                if not should_continue:
                    self.state.set_status(Status.FAILED)
                    ErrorHandler.propagate_errors(child_state, self.state)
                    self.logger.error(f"Child {child_name} failed and error handling is strict")
                    break
        
        # Finalize state
        if not self.state.has_errors():
            self.state.set_status(Status.COMPLETED)
            self.logger.info(f"=== {self.phase.upper()} ORCHESTRATOR COMPLETED SUCCESSFULLY ===")
        else:
            self.state.set_status(Status.FAILED)
            self.logger.error(f"=== {self.phase.upper()} ORCHESTRATOR COMPLETED WITH ERRORS ===")
        
        return self.state
    
    def run(self) -> StateManager:
        """Run the orchestrator - execute all phases in order."""
        self.state.set_status(Status.RUNNING)
        self.logger.info("Starting orchestrator execution")
        
        # Get children from config (phases to execute)
        children = self.config.get("children", [])
        
        # Sort by phase order if available
        phases_config = self.config.get("phases", {})
        children_sorted = sorted(
            children,
            key=lambda x: phases_config.get(x, {}).get("order", 999)
        )
        
        # Execute each phase
        for phase_name in children_sorted:
            phase_state = self.execute_phase(phase_name)
            
            # Check if we should stop on error
            if phase_state.status == Status.FAILED:
                should_continue = ErrorHandler.should_continue_on_error(
                    self.config.get("execution", {}),
                    phase_name
                )
                if not should_continue:
                    self.state.set_status(Status.FAILED)
                    self.logger.error(f"Stopping execution due to failure in {phase_name}")
                    break
        
        # Finalize state
        if not self.state.has_errors():
            self.state.set_status(Status.COMPLETED)
            self.logger.info("=== ORCHESTRATOR COMPLETED SUCCESSFULLY ===")
        else:
            self.state.set_status(Status.FAILED)
            self.logger.error("=== ORCHESTRATOR COMPLETED WITH ERRORS ===")
        
        return self.state


def main(install_path: Optional[Path] = None, phase: str = "root") -> StateManager:
    """
    Main entry point for orchestrator.
    
    Args:
        install_path: Path to installation directory (defaults to script directory)
        phase: Phase name for this orchestrator instance
    
    Returns:
        StateManager: Execution state with results
    """
    orchestrator = Orchestrator(install_path=install_path, phase=phase)
    return orchestrator.run()


if __name__ == "__main__":
    # Allow running directly
    install_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    state = main(install_path=install_path)
    
    # Exit with error code if failed
    if state.status == Status.FAILED:
        sys.exit(1)
    sys.exit(0)

