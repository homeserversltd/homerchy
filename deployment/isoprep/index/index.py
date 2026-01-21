#!/usr/bin/env python3

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from utils import Colors

class Orchestrator:
    """Main orchestrator for ISO build process."""

    def __init__(self, index_path: Path):
        self.index_path = index_path
        self.config_path = index_path / 'index.json'
        self.config = self._load_config()
        self.paths = self._resolve_paths()

    def _load_config(self):
        """Load configuration from index.json.

        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config = json.load(f)

        return config

    def _resolve_paths(self):
        """Resolve paths from config, expanding environment variables.

        Returns:
            Dict[str, Any]: Resolved paths dictionary with Path objects for paths
        """
        paths_config = self.config.get('paths', {}).copy()

        # Set default repo_root if not provided
        if 'repo_root' not in paths_config or not paths_config['repo_root']:
            default_repo_root = Path(__file__).parent.parent.parent.resolve()
            os.environ['ISOPREP_REPO_ROOT'] = str(default_repo_root)
            paths_config['repo_root'] = str(default_repo_root)

        # Expand bash-style variables first (${VAR:-default} syntax)
        for key, value in paths_config.items():
            if isinstance(value, str):
                paths_config[key] = self._expand_vars(value)

        # Then expand standard $VAR syntax
        for key, value in paths_config.items():
            if isinstance(value, str):
                paths_config[key] = os.path.expandvars(value)

        # Check paths exist and convert to Path objects
        resolved = {}
        for key, path_str in paths_config.items():
            if key.endswith('_dir') or key in ['repo_root']:
                path = Path(path_str)
                # Only check existence for paths that should exist (not output dirs that will be created)
                if key == 'repo_root' and not path.exists():
                    raise FileNotFoundError(f"Required path {key} does not exist: {path}")
                resolved[key] = path
            else:
                resolved[key] = path_str

        return resolved

    def _expand_vars(self, value: str) -> str:
        """Expand bash-style ${VAR:-default} syntax.

        Args:
            value: String with variable references

        Returns:
            str: String with variables expanded
        """
        import re
        pattern = r'\$\{([^:]+):-([^}]+)\}'

        def replacer(match):
            var_name = match.group(1)
            default = match.group(2)
            return os.environ.get(var_name, default)

        return re.sub(pattern, replacer, value)

    def execute(self) -> bool:
        """Execute all build children phases.

        Returns:
            bool: True if all phases succeeded, False otherwise
        """
        children = self.config.get('children', [])
        execution_config = self.config.get('execution', {})
        continue_on_error = execution_config.get('continue_on_error', False)
        results = {}
        success = True

        for phase_name in children:
            try:
                phase_result = self._execute_phase(phase_name, results)
                results[phase_name] = phase_result
            except Exception as e:
                print(f'{Colors.BLUE}Error in phase {phase_name}: {e}{Colors.NC}')
                if not continue_on_error:
                    return False
                success = False

        return success

    def _execute_phase(self, phase_name: str, phase_results: dict = None) -> dict:
        """Execute a single build phase.

        Args:
            phase_name: Name of the phase to execute
            phase_results: Previous phase results (optional)

        Returns:
            dict: Phase execution results
        """
        phase_dir = self.index_path / phase_name

        if not phase_dir.exists():
            raise FileNotFoundError(f"Phase directory not found: {phase_dir}")

        # Load phase config
        phase_config = {**self.paths, **self.config.get(phase_name, {})}

        # Import and run phase module
        import importlib.util
        # Add phase directory parent to path BEFORE loading (for relative imports to work)
        sys.path.insert(0, str(phase_dir.parent))
        
        # Use phase directory name as module name so relative imports resolve correctly
        module_name = f"{phase_name}.index"
        spec = importlib.util.spec_from_file_location(module_name, phase_dir / 'index.py')
        module = importlib.util.module_from_spec(spec)
        
        # Set __package__ attribute so relative imports work
        module.__package__ = phase_name
        spec.loader.exec_module(module)

        if hasattr(module, 'main'):
            result = module.main(phase_dir, phase_config)
            phase_config.update(result)
            return phase_config
        else:
            raise AttributeError(f"Phase {phase_name} does not have main() function")

    def print_summary(self):
        """Print build summary."""
        repo_root = self.paths.get('repo_root', 'N/A')
        if isinstance(repo_root, Path):
            repo_root = str(repo_root)
        print(f"{Colors.BLUE}Repository root: {repo_root}{Colors.NC}")

        children = self.config.get('children', [])
        print(f"{Colors.BLUE}Build phases: {', '.join(children)}{Colors.NC}")

        execution_config = self.config.get('execution', {})
        continue_on_error = execution_config.get('continue_on_error', False)
        print(f"{Colors.BLUE}Continue on error: {continue_on_error}{Colors.NC}")

        # Print status of each phase if results are available
        if hasattr(self, '_phase_results') and self._phase_results:
            print(f"{Colors.BLUE}Phase results:{Colors.NC}")
            for phase_name, result in self._phase_results.items():
                status = "SUCCESS" if result.get('success', False) else "FAILED"
                print(f"  {phase_name}: {status}")


def main():
    """Main entry point for the ISO build orchestration system."""
    orchestrator = Orchestrator(Path(__file__).parent)
    success = orchestrator.execute()
    import sys
    sys.exit(0 if success else 1)
