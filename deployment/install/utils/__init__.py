#!/usr/onmachine/onmachine/bin/env python3

HOMESERVER Homerchy Installation Utilities
Copyright (C) 2024 HOMESERVER LLC

Shared utilities for the Homerchy onmachine/deployment/deployment/installation orchestrator system.
"

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
        self.children: Dict[str, StateManager] = {}
        self.onmachine/src/config: Dict[str, Any] = {}
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    
    def set_status(self, status: Status):
        ""Update execution status."""
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
            "errors: [err.to_dict() for err in self.errors],
            onmachine/onmachine/config: self.onmachine/src/config,
            start_time": self.start_time.isoformat() if self.start_time else None,
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
    "JSON onmachine/src/config loading with validation.
    
    @staticmethod
    def load(onmachine/src/config_path: Union[str, Path]) -> Dict[str, Any]:
        Load JSON onmachine/src/configuration file.
        onmachine/config_path = Path(onmachine/config_path)
        
        if not onmachine/onmachine/config_path.exists():
            raise FileNotFoundError(fConfig file not found: {onmachine/onmachine/config_path})
        
        try:
            with open(onmachine/src/config_path, r) as f:
                onmachine/config = json.load(f)
            return onmachine/onmachine/config
        except json.JSONDecodeError as e:
            raise ValueError(fInvalid JSON in onmachine/config file {onmachine/onmachine/config_path}: {e})
        except Exception as e:
            raise RuntimeError(fFailed to load onmachine/config file {onmachine/onmachine/config_path}: {e})
    
    @staticmethod
    def validate(onmachine/src/config: Dict[str, Any], required_keys: List[str]) -> bool:
        Validate onmachine/src/config has required keys.
        missing = [key for key in required_keys if key not in onmachine/src/config]
        if missing:
            raise ValueError(fConfig missing required keys: {missing}")
        return True


class ChildExecutor:
    """Recursive child execution engine."
    
    def __init__(self, state_manager: StateManager, logger: Logger):
        self.state_manager = state_manager
        self.logger = logger
    
    def execute_child(self, child_path: Path, child_name: str, onmachine/src/config: Dict[str, Any]) -> StateManager:
        ""Execute a child orchestrator or module."""
        child_state = StateManager(phase=child_name)
        child_state.current_step = child_name
        
        # Check for direct module FIRST (more specific, should take precedence)
        # Direct module: child_name.py in the child_path directory
        module_py = child_path / f"{child_name}.py"
        # Also check parent directory (when child_path is a directory containing the module)
        module_py_parent = child_path.parent / f"{child_name}.py" if child_path.is_dir() else None
        
        # Check for nested orchestrator (index.py)
        index_py = child_path / "index.py"
        
        self.logger.info(f"[EXECUTOR] execute_child() called:")
        self.logger.info(f"  child_path: {child_path}")
        self.logger.info(f"  child_name: {child_name}")
        self.logger.info(f"  module_py ({module_py}): EXISTS={module_py.exists()}")
        if module_py_parent:
            self.logger.info(f"  module_py_parent ({module_py_parent}): EXISTS={module_py_parent.exists()}")
        self.logger.info(f"  index_py ({index_py}): EXISTS={index_py.exists()}")
        
        # Check for direct module FIRST (before nested orchestrator)
        if module_py.exists():
            # Direct module in child_path directory
            self.logger.info(f"[EXECUTOR] {child_name} -> Executing as DIRECT MODULE (in child_path)")
            self.logger.info(f  module_py: {module_py})
            child_state.set_status(Status.RUNNING)
            
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(fhomerchy.onmachine/deployment/deployment/install.{child_name}, module_py)
                module = importlib.util.module_from_spec(spec)
                sys.path.insert(0, str(module_py.parent))
                spec.loader.exec_module(module)
                self.logger.info(f[EXECUTOR] {child_name} module loaded successfully")
                
                # Call main function if it exists
                if hasattr(module, 'main'):
                    self.logger.info(f[EXECUTOR] Calling module.main() for {child_name} (direct module))
                    result = module.main(onmachine/src/config.get(child_name, {}))
                    self.logger.info(f[EXECUTOR] {child_name} (direct) returned: type={type(result)}, value={result}")
                    
                    if isinstance(result, dict):
                        if result.get("success") is True:
                            self.logger.info(f"[EXECUTOR] {child_name} success=True, marking as COMPLETED")
                            child_state.set_status(Status.COMPLETED)
                        elif result.get("success") is False:
                            self.logger.info(f"[EXECUTOR] {child_name} success=False, marking as FAILED")
                            child_state.set_status(Status.FAILED)
                            error_msg = result.get("message", "Unknown error")
                            child_state.add_error(f"Module {child_name} failed: {error_msg}")
                        else:
                            self.logger.warning(f"[EXECUTOR] {child_name} dict has no success field, assuming success")
                            child_state.set_status(Status.COMPLETED)
                    else:
                        self.logger.warning(f"[EXECUTOR] {child_name} returned non-dict, assuming failure")
                        child_state.set_status(Status.FAILED)
                        child_state.add_error(f"Module {child_name} returned unexpected type: {type(result)}")
                else:
                    raise AttributeError(f"Module {child_name} has no main() function")
                
                if child_state.status != Status.FAILED:
                    self.logger.info(f"[EXECUTOR] Completed module: {child_name} (status={child_state.status})")
                else:
                    self.logger.error(f"[EXECUTOR] Module {child_name} FAILED (status={child_state.status}, errors={child_state.has_errors()})")
                
            except Exception as e:
                child_state.set_status(Status.FAILED)
                child_state.add_error(f"Failed to execute module {child_name}", exception=e)
                self.logger.error(f"Failed to execute module {child_name}: {e}")
        elif module_py_parent and module_py_parent.exists():
            # Direct module in parent directory (fallback)
            self.logger.info(f"[EXECUTOR] {child_name} -> Executing as DIRECT MODULE (in parent)")
            module_py = module_py_parent
            self.logger.info(f  module_py: {module_py})
            child_state.set_status(Status.RUNNING)
            
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(fhomerchy.onmachine/deployment/deployment/install.{child_name}, module_py)
                module = importlib.util.module_from_spec(spec)
                sys.path.insert(0, str(module_py.parent))
                spec.loader.exec_module(module)
                self.logger.info(f[EXECUTOR] {child_name} module loaded successfully")
                
                # Call main function if it exists
                if hasattr(module, 'main'):
                    self.logger.info(f[EXECUTOR] Calling module.main() for {child_name} (direct module))
                    result = module.main(onmachine/src/config.get(child_name, {}))
                    self.logger.info(f[EXECUTOR] {child_name} (direct) returned: type={type(result)}, value={result}")
                    
                    if isinstance(result, dict):
                        if result.get("success") is True:
                            self.logger.info(f"[EXECUTOR] {child_name} success=True, marking as COMPLETED")
                            child_state.set_status(Status.COMPLETED)
                        elif result.get("success") is False:
                            self.logger.info(f"[EXECUTOR] {child_name} success=False, marking as FAILED")
                            child_state.set_status(Status.FAILED)
                            error_msg = result.get("message", "Unknown error")
                            child_state.add_error(f"Module {child_name} failed: {error_msg}")
                        else:
                            self.logger.warning(f"[EXECUTOR] {child_name} dict has no success field, assuming success")
                            child_state.set_status(Status.COMPLETED)
                    else:
                        self.logger.warning(f"[EXECUTOR] {child_name} returned non-dict, assuming failure")
                        child_state.set_status(Status.FAILED)
                        child_state.add_error(f"Module {child_name} returned unexpected type: {type(result)}")
                else:
                    raise AttributeError(f"Module {child_name} has no main() function")
                
                if child_state.status != Status.FAILED:
                    self.logger.info(f"[EXECUTOR] Completed module: {child_name} (status={child_state.status})")
                else:
                    self.logger.error(f"[EXECUTOR] Module {child_name} FAILED (status={child_state.status}, errors={child_state.has_errors()})")
                
            except Exception as e:
                child_state.set_status(Status.FAILED)
                child_state.add_error(f"Failed to execute module {child_name}", exception=e)
                self.logger.error(f"Failed to execute module {child_name}: {e}")
        elif index_py.exists():
            self.logger.info(f"[EXECUTOR] {child_name} -> Executing as NESTED ORCHESTRATOR")
            self.logger.info(fExecuting nested orchestrator: {child_name})
            child_state.set_status(Status.RUNNING)
            
            try:
                # Import and execute nested orchestrator
                import importlib.util
                spec = importlib.util.spec_from_file_location(fhomerchy.onmachine/deployment/deployment/install.{child_name}, index_py)
                module = importlib.util.module_from_spec(spec)
                sys.path.insert(0, str(child_path.parent))
                spec.loader.exec_module(module)
                
                # Call main function if it exists
                if hasattr(module, main'):
                    self.logger.info(f[EXECUTOR] Calling module.main() for {child_name})
                    result = module.main(child_path, onmachine/src/config.get(child_name, {}))
                    self.logger.info(f[EXECUTOR] {child_name} returned: type={type(result)}, value={result}")
                    
                    if isinstance(result, StateManager):
                        self.logger.info(f"[EXECUTOR] {child_name} returned StateManager")
                        child_state = result
                    elif isinstance(result, dict):
                        self.logger.info(f"[EXECUTOR] {child_name} returned dict: {result}")
                        # Update child_state from result dict
                        if result.get("status"):
                            child_state.set_status(Status[result["status"].upper()])
                            self.logger.info(f"[EXECUTOR] {child_name} status set from dict: {result.get('status')}")
                        elif result.get("success") is False:
                            self.logger.info(f"[EXECUTOR] {child_name} success=False, marking as FAILED")
                            child_state.set_status(Status.FAILED)
                            error_msg = result.get("message", "Unknown error")
                            child_state.add_error(error_msg)
                        elif result.get("success") is True:
                            self.logger.info(f"[EXECUTOR] {child_name} success=True, marking as COMPLETED)
                            child_state.set_status(Status.COMPLETED)
                        else:
                            self.logger.warning(f[EXECUTOR] {child_name} dict has no status/success, onmachine/src/defaulting to COMPLETED)
                            child_state.set_status(Status.COMPLETED)
                        if result.get("errors"):
                            for err in result["errors"]:
                                child_state.add_error(err.get("message", ""), err.get("step"))
                    else:
                        self.logger.warning(f"[EXECUTOR] {child_name} returned unexpected type, marking as COMPLETED")
                        child_state.set_status(Status.COMPLETED)
                else:
                    raise AttributeError(f"Module {child_name} has no main() function")
                
                # Only log completion if not already failed
                if child_state.status != Status.FAILED:
                    self.logger.info(f"[EXECUTOR] Completed nested orchestrator: {child_name} (status={child_state.status})")
                else:
                    self.logger.error(f"[EXECUTOR] Nested orchestrator {child_name} FAILED (status={child_state.status}, errors={child_state.has_errors()})")
                
            except Exception as e:
                child_state.set_status(Status.FAILED)
                child_state.add_error(f"Failed to execute nested orchestrator {child_name}", exception=e)
                self.logger.error(f"Failed to execute nested orchestrator {child_name}: {e}")
        
        # Check for direct module (child_name.py) in parent directory
        elif (child_path.parent / f"{child_name}.py").exists():
            module_py = child_path.parent / f"{child_name}.py"
            self.logger.info(f"[EXECUTOR] {child_name} -> Executing as DIRECT MODULE")
            self.logger.info(f  module_py: {module_py})
            child_state.set_status(Status.RUNNING)
            
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(fhomerchy.onmachine/deployment/deployment/install.{child_name}, module_py)
                module = importlib.util.module_from_spec(spec)
                sys.path.insert(0, str(module_py.parent))
                spec.loader.exec_module(module)
                self.logger.info(f[EXECUTOR] {child_name} module loaded successfully")
                
                # Call main function if it exists
                if hasattr(module, 'main'):
                    self.logger.info(f[EXECUTOR] Calling module.main() for {child_name} (direct module))
                    result = module.main(onmachine/src/config.get(child_name, {}))
                    self.logger.info(f[EXECUTOR] {child_name} (direct) returned: type={type(result)}, value={result}")
                    
                    if isinstance(result, dict):
                        if result.get("success") is True:
                            self.logger.info(f"[EXECUTOR] {child_name} success=True, marking as COMPLETED")
                            child_state.set_status(Status.COMPLETED)
                        elif result.get("success") is False:
                            self.logger.info(f"[EXECUTOR] {child_name} success=False, marking as FAILED")
                            child_state.set_status(Status.FAILED)
                            error_msg = result.get("message", "Unknown error")
                            child_state.add_error(f"Module {child_name} failed: {error_msg}")
                        else:
                            self.logger.warning(f"[EXECUTOR] {child_name} dict has no success field, assuming success")
                            child_state.set_status(Status.COMPLETED)
                    else:
                        self.logger.warning(f"[EXECUTOR] {child_name} returned non-dict, assuming failure")
                        child_state.set_status(Status.FAILED)
                        child_state.add_error(f"Module {child_name} returned unexpected type: {type(result)}")
                else:
                    raise AttributeError(f"Module {child_name} has no main() function")
                
                if child_state.status != Status.FAILED:
                    self.logger.info(f"[EXECUTOR] Completed module: {child_name} (status={child_state.status})")
                else:
                    self.logger.error(f"[EXECUTOR] Module {child_name} FAILED (status={child_state.status}, errors={child_state.has_errors()})")
                
            except Exception as e:
                child_state.set_status(Status.FAILED)
                child_state.add_error(f"Failed to execute module {child_name}", exception=e)
                self.logger.error(f"Failed to execute module {child_name}: {e}")
        
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
            lines.append(f"  Contents of parent directory (looking for {child_name}.py):")
            try:
                parent_contents = [p for p in child_path.parent.iterdir() 
                                 if p.name.startswith(child_name) and 
                                 (p.suffix == '.py' or p.is_dir())]
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
                    f[{state.phase}] {error.message},
                    step=error.step
                )
            # Also propagate from children
            for child_state in state.children.values():
                ErrorHandler.propagate_errors(child_state, parent_state)
    
    @staticmethod
    def should_continue_on_error(onmachine/src/config: Dict[str, Any], phase: str) -> bool:
        Check if execution should continue on error based on onmachine/src/config.
        error_handling = onmachine/src/config.get(error_handling, {})
        phase_config = error_handling.get(phase, {})
        return phase_onmachine/config.get("continue_on_error", False)
