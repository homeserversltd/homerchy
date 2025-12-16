#!/usr/bin/env python3
"""
HOMESERVER Homerchy Installation Utilities
Copyright (C) 2024 HOMESERVER LLC

Shared utilities for the Homerchy installation orchestrator system.
"""

import json
import os
import sys
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum


class Status(Enum):
    """Execution status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class LogEntry:
    """Structured log entry."""
    timestamp: str
    level: str  # INFO, ERROR, WARNING, DEBUG
    message: str
    phase: Optional[str] = None
    step: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ErrorEntry:
    """Structured error entry."""
    timestamp: str
    phase: str
    step: str
    message: str
    exception: Optional[str] = None
    traceback: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class StateManager:
    """Master sync state tracking for orchestrator execution."""
    
    def __init__(self, phase: str = "root"):
        self.phase = phase
        self.status = Status.PENDING
        self.current_step: Optional[str] = None
        self.logs: List[LogEntry] = []
        self.errors: List[ErrorEntry] = []
        self.children: Dict[str, 'StateManager'] = {}
        self.config: Dict[str, Any] = {}
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    
    def set_status(self, status: Status):
        """Update execution status."""
        self.status = status
        if status == Status.RUNNING and self.start_time is None:
            self.start_time = datetime.now()
        if status in (Status.COMPLETED, Status.FAILED) and self.end_time is None:
            self.end_time = datetime.now()
    
    def add_log(self, level: str, message: str, step: Optional[str] = None):
        """Add a log entry."""
        entry = LogEntry(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            level=level,
            message=message,
            phase=self.phase,
            step=step or self.current_step
        )
        self.logs.append(entry)
    
    def add_error(self, message: str, step: Optional[str] = None, exception: Optional[Exception] = None):
        """Add an error entry."""
        import traceback as tb
        error_entry = ErrorEntry(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            phase=self.phase,
            step=step or self.current_step or "unknown",
            message=message,
            exception=str(exception) if exception else None,
            traceback=tb.format_exc() if exception else None
        )
        self.errors.append(error_entry)
        self.add_log("ERROR", message, step)
    
    def add_child(self, name: str, child_state: 'StateManager'):
        """Add a child state manager."""
        self.children[name] = child_state
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            "status": self.status.value,
            "phase": self.phase,
            "current_step": self.current_step,
            "logs": [log.to_dict() for log in self.logs],
            "children": {name: child.to_dict() for name, child in self.children.items()},
            "errors": [err.to_dict() for err in self.errors],
            "config": self.config,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None
        }
    
    def has_errors(self) -> bool:
        """Check if state has any errors."""
        if self.errors:
            return True
        return any(child.has_errors() for child in self.children.values())


class Logger:
    """Structured logging with file rotation."""
    
    def __init__(self, log_file: str, phase: str = "root", console: bool = True):
        self.log_file = Path(log_file)
        self.phase = phase
        self.console = console
        
        # Check if we're root
        is_root = os.geteuid() == 0
        
        # Track if we fell back to user-writable location
        using_user_location = False
        
        # Ensure log directory exists
        log_dir = self.log_file.parent
        if not log_dir.exists():
            if is_root:
                log_dir.mkdir(parents=True, exist_ok=True)
            else:
                # Not root - try with sudo, or fall back to user-writable location
                try:
                    result = subprocess.run(['sudo', 'mkdir', '-p', str(log_dir)], check=True, capture_output=True)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    # sudo failed or not available - use user-writable location
                    user_log_dir = Path.home() / '.local' / 'share' / 'omarchy' / 'logs'
                    user_log_dir.mkdir(parents=True, exist_ok=True)
                    self.log_file = user_log_dir / f"{phase}-{self.log_file.name}"
                    log_dir = self.log_file.parent
                    using_user_location = True
        
        # Create log file if it doesn't exist
        if not self.log_file.exists():
            if is_root:
                self.log_file.touch(mode=0o666)
            elif using_user_location:
                # Already using user location - create directly
                self.log_file.touch(mode=0o666)
            else:
                # Not root - try with sudo, or fall back to user location
                try:
                    subprocess.run(['sudo', 'touch', str(self.log_file)], check=True, capture_output=True)
                    subprocess.run(['sudo', 'chmod', '666', str(self.log_file)], check=True, capture_output=True)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    # sudo failed - use user-writable location
                    user_log_dir = Path.home() / '.local' / 'share' / 'omarchy' / 'logs'
                    user_log_dir.mkdir(parents=True, exist_ok=True)
                    self.log_file = user_log_dir / f"{phase}-{self.log_file.name}"
                    self.log_file.touch(mode=0o666)
        
        # Setup Python logging
        self.logger = logging.getLogger(f"homerchy.{phase}")
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        file_handler = logging.FileHandler(self.log_file, mode='a')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler (if enabled)
        if console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                '[%(asctime)s] [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
    
    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)
    
    def error(self, message: str):
        """Log error message."""
        self.logger.error(message)
    
    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)
    
    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)


class ConfigLoader:
    """JSON config loading with validation."""
    
    @staticmethod
    def load(config_path: Union[str, Path]) -> Dict[str, Any]:
        """Load JSON configuration file."""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file {config_path}: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load config file {config_path}: {e}")
    
    @staticmethod
    def validate(config: Dict[str, Any], required_keys: List[str]) -> bool:
        """Validate config has required keys."""
        missing = [key for key in required_keys if key not in config]
        if missing:
            raise ValueError(f"Config missing required keys: {missing}")
        return True


class ChildExecutor:
    """Recursive child execution engine."""
    
    def __init__(self, state_manager: StateManager, logger: Logger):
        self.state_manager = state_manager
        self.logger = logger
    
    def execute_child(self, child_path: Path, child_name: str, config: Dict[str, Any]) -> StateManager:
        """Execute a child orchestrator or module."""
        child_state = StateManager(phase=child_name)
        child_state.current_step = child_name
        
        # Check for nested orchestrator (index.py)
        index_py = child_path / "index.py"
        if index_py.exists():
            self.logger.info(f"Executing nested orchestrator: {child_name}")
            child_state.set_status(Status.RUNNING)
            
            try:
                # Import and execute nested orchestrator
                import importlib.util
                spec = importlib.util.spec_from_file_location(f"homerchy.install.{child_name}", index_py)
                module = importlib.util.module_from_spec(spec)
                sys.path.insert(0, str(child_path.parent))
                spec.loader.exec_module(module)
                
                # Call main function if it exists
                if hasattr(module, 'main'):
                    result = module.main(child_path, config.get(child_name, {}))
                    if isinstance(result, StateManager):
                        child_state = result
                    elif isinstance(result, dict):
                        # Update child_state from result dict
                        if result.get("status"):
                            child_state.set_status(Status[result["status"].upper()])
                        if result.get("errors"):
                            for err in result["errors"]:
                                child_state.add_error(err.get("message", ""), err.get("step"))
                else:
                    raise AttributeError(f"Module {child_name} has no main() function")
                
                child_state.set_status(Status.COMPLETED)
                self.logger.info(f"Completed nested orchestrator: {child_name}")
                
            except Exception as e:
                child_state.set_status(Status.FAILED)
                child_state.add_error(f"Failed to execute nested orchestrator {child_name}", exception=e)
                self.logger.error(f"Failed to execute nested orchestrator {child_name}: {e}")
        
        # Check for direct module (child_name.py) in parent directory
        elif (child_path.parent / f"{child_name}.py").exists():
            module_py = child_path.parent / f"{child_name}.py"
            self.logger.info(f"Executing module: {child_name}")
            child_state.set_status(Status.RUNNING)
            
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(f"homerchy.install.{child_name}", module_py)
                module = importlib.util.module_from_spec(spec)
                sys.path.insert(0, str(module_py.parent))
                spec.loader.exec_module(module)
                
                # Call main function if it exists
                if hasattr(module, 'main'):
                    result = module.main(config.get(child_name, {}))
                    if isinstance(result, dict) and result.get("success"):
                        child_state.set_status(Status.COMPLETED)
                    else:
                        child_state.set_status(Status.FAILED)
                        error_msg = result.get("message", "Unknown error") if isinstance(result, dict) else "Module returned failure"
                        child_state.add_error(f"Module {child_name} failed: {error_msg}")
                else:
                    raise AttributeError(f"Module {child_name} has no main() function")
                
                self.logger.info(f"Completed module: {child_name}")
                
            except Exception as e:
                child_state.set_status(Status.FAILED)
                child_state.add_error(f"Failed to execute module {child_name}", exception=e)
                self.logger.error(f"Failed to execute module {child_name}: {e}")
        
        # Check for shell script (hybrid mode during transition)
        elif (child_path.parent / f"{child_name}.sh").exists():
            script_path = child_path.parent / f"{child_name}.sh"
            self.logger.info(f"Executing shell script: {child_name}")
            child_state.set_status(Status.RUNNING)
            
            try:
                result = subprocess.run(
                    ['bash', str(script_path)],
                    capture_output=True,
                    text=True,
                    cwd=str(script_path.parent)
                )
                
                if result.returncode == 0:
                    child_state.set_status(Status.COMPLETED)
                    self.logger.info(f"Completed shell script: {child_name}")
                else:
                    child_state.set_status(Status.FAILED)
                    error_msg = result.stderr or result.stdout or "Unknown error"
                    child_state.add_error(f"Shell script {child_name} failed: {error_msg}")
                    self.logger.error(f"Shell script {child_name} failed: {error_msg}")
                
            except Exception as e:
                child_state.set_status(Status.FAILED)
                child_state.add_error(f"Failed to execute shell script {child_name}", exception=e)
                self.logger.error(f"Failed to execute shell script {child_name}: {e}")
        
        else:
            child_state.set_status(Status.FAILED)
            error_msg = self._generate_missing_executable_error(child_path, child_name)
            child_state.add_error(f"No executable found for child: {child_name}")
            self.logger.error(error_msg)
        
        return child_state
    
    def _generate_missing_executable_error(self, child_path: Path, child_name: str) -> str:
        """Generate comprehensive error message when executable is not found."""
        lines = [
            "",
            "═" * 64,
            f"ERROR: No executable found for child: {child_name}",
            "═" * 64,
            "",
            "Expected files (checked in order):",
            f"  1. {child_path / 'index.py'}",
            f"     [{'EXISTS' if (child_path / 'index.py').exists() else 'MISSING'}]",
            f"  2. {child_path.parent / f'{child_name}.py'}",
            f"     [{'EXISTS' if (child_path.parent / f'{child_name}.py').exists() else 'MISSING'}]",
            f"  3. {child_path.parent / f'{child_name}.sh'}",
            f"     [{'EXISTS' if (child_path.parent / f'{child_name}.sh').exists() else 'MISSING'}]",
            "",
            "Path information:",
            f"  Child path: {child_path}",
            f"  Child path exists: {'YES' if child_path.exists() else 'NO'}",
            f"  Parent directory: {child_path.parent}",
            f"  Parent directory exists: {'YES' if child_path.parent.exists() else 'NO'}",
        ]
        
        # List directory contents
        if child_path.exists() and child_path.is_dir():
            lines.append("  Contents of child directory:")
            try:
                contents = list(child_path.iterdir())
                for item in sorted(contents)[:20]:  # Limit to 20 items
                    item_type = "DIR" if item.is_dir() else "FILE"
                    lines.append(f"    {item_type:4} {item.name}")
                if len(contents) > 20:
                    lines.append(f"    ... and {len(contents) - 20} more items")
            except Exception as e:
                lines.append(f"    [Error listing directory: {e}]")
        
        # List parent directory contents if relevant
        if child_path.parent.exists() and child_path.parent.is_dir():
            lines.append("")
            lines.append(f"  Contents of parent directory (looking for {child_name}.py/.sh):")
            try:
                parent_contents = [p for p in child_path.parent.iterdir() 
                                 if p.name.startswith(child_name) and 
                                 (p.suffix in ['.py', '.sh'] or p.is_dir())]
                for item in sorted(parent_contents):
                    item_type = "DIR" if item.is_dir() else "FILE"
                    lines.append(f"    {item_type:4} {item.name}")
                if not parent_contents:
                    lines.append("    [No matching files found]")
            except Exception as e:
                lines.append(f"    [Error listing directory: {e}]")
        
        lines.extend([
            "",
            "Environment context:",
            f"  Current working directory: {Path.cwd()}",
            f"  HOME: {os.environ.get('HOME', '[NOT SET]')}",
            f"  USER: {os.environ.get('USER', '[NOT SET]')}",
            f"  Python version: {sys.version.split()[0]}",
            "",
            "═" * 64,
            "",
        ])
        
        return "\n".join(lines)


class ErrorHandler:
    """Error collection and propagation."""
    
    @staticmethod
    def propagate_errors(state: StateManager, parent_state: StateManager):
        """Propagate errors from child state to parent."""
        if state.has_errors():
            for error in state.errors:
                parent_state.add_error(
                    f"[{state.phase}] {error.message}",
                    step=error.step
                )
            # Also propagate from children
            for child_state in state.children.values():
                ErrorHandler.propagate_errors(child_state, parent_state)
    
    @staticmethod
    def should_continue_on_error(config: Dict[str, Any], phase: str) -> bool:
        """Check if execution should continue on error based on config."""
        error_handling = config.get("error_handling", {})
        phase_config = error_handling.get(phase, {})
        return phase_config.get("continue_on_error", False)

